"""Coverage for skills/acquire-corpus/scripts/search_openalex.py.

NO NETWORK — urlopen is patched inside the module for every test. This script
produces the identification counts that feed the PRISMA flow, so a mapping error
here corrupts a published number.

Standard library only.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import pathlib
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

so = load("skills/acquire-corpus/scripts/search_openalex.py")


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def pages(*payloads):
    """Serve the given payloads in order, then fail loudly."""
    it = iter(payloads)

    def _open(req, timeout=None):
        try:
            payload = next(it)
        except StopIteration:
            raise AssertionError("more requests than the test provided pages for")
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(json.dumps(payload).encode("utf-8"))
    return _open


def work(i, **kw):
    w = {
        "id": f"https://openalex.org/W{i}",
        "doi": f"https://doi.org/10.1/{i}",
        "title": f"Study {i}",
        "authorships": [{"author": {"display_name": "Ada Smith"}}],
        "publication_year": 2024,
        "primary_location": {"source": {"display_name": "Journal of Things"}},
        "type": "article",
        "is_retracted": False,
        "cited_by_count": i,
        "referenced_works": [],
    }
    w.update(kw)
    return w


class TestAbstractReconstruction(unittest.TestCase):
    """OpenAlex ships abstracts as an inverted index; word order must be restored."""

    def test_reconstructs_word_order(self):
        inv = {"the": [0, 4], "cat": [1], "sat": [2], "on": [3], "mat": [5]}
        self.assertEqual(so.reconstruct_abstract(inv), "the cat sat on the mat")

    def test_empty_index(self):
        self.assertEqual(so.reconstruct_abstract(None), "")
        self.assertEqual(so.reconstruct_abstract({}), "")

    def test_repeated_word_at_multiple_positions(self):
        inv = {"a": [0, 2], "b": [1]}
        self.assertEqual(so.reconstruct_abstract(inv), "a b a")


class TestRecordMapping(unittest.TestCase):
    def test_maps_expected_fields(self):
        r = so.to_record(work(7))
        self.assertEqual(r["openalex_id"], "https://openalex.org/W7")
        self.assertEqual(r["doi"], "10.1/7")
        self.assertEqual(r["title"], "Study 7")
        self.assertEqual(r["authors"], ["Ada Smith"])
        self.assertEqual(r["year"], 2024)
        self.assertEqual(r["venue"], "Journal of Things")
        self.assertEqual(r["cited_by_count"], 7)

    def test_doi_url_prefix_stripped(self):
        self.assertEqual(so.to_record(work(1, doi="https://doi.org/10.5/x"))["doi"], "10.5/x")

    def test_missing_doi_becomes_none(self):
        self.assertIsNone(so.to_record(work(1, doi=None))["doi"])
        self.assertIsNone(so.to_record(work(1, doi=""))["doi"])

    def test_authors_capped_at_eight(self):
        many = [{"author": {"display_name": f"A{i}"}} for i in range(20)]
        self.assertEqual(len(so.to_record(work(1, authorships=many))["authors"]), 8)

    def test_missing_nested_structures_do_not_raise(self):
        r = so.to_record({"id": "x"})
        self.assertIsNone(r["venue"])
        self.assertEqual(r["authors"], [])
        self.assertEqual(r["referenced_works"], [])

    def test_retraction_flag_carried_through(self):
        self.assertTrue(so.to_record(work(1, is_retracted=True))["is_retracted"])


class TestSearch(unittest.TestCase):
    def setUp(self):
        # search() writes its PRISMA-S log line to stderr; silence it so the suite
        # output stays readable without suppressing genuine errors elsewhere.
        self._err = contextlib.redirect_stderr(io.StringIO())
        self._err.__enter__()
        self.addCleanup(lambda: self._err.__exit__(None, None, None))

    def args(self, **kw):
        # Mirrors every attribute search() reads, including run_date, which it
        # writes to the PRISMA-S search log line on stderr.
        base = dict(query="ai in radiology", from_date=None, to_date=None, type=None,
                    lang=None, mailto="", max=1000, run_date="2026-07-26")
        base.update(kw)
        return argparse.Namespace(**base)

    def test_single_page(self):
        payload = {"results": [work(1), work(2)], "meta": {"next_cursor": None}}
        with mock.patch.object(so.urllib.request, "urlopen", pages(payload)):
            got = so.search(self.args())
        self.assertEqual(len(got), 2)
        self.assertEqual(got[0]["title"], "Study 1")

    def test_paginates_via_cursor(self):
        p1 = {"results": [work(1)], "meta": {"next_cursor": "CUR2"}}
        p2 = {"results": [work(2)], "meta": {"next_cursor": None}}
        with mock.patch.object(so.urllib.request, "urlopen", pages(p1, p2)):
            got = so.search(self.args())
        self.assertEqual(len(got), 2)

    def test_deduplicates_repeated_ids_across_pages(self):
        """The same work returned twice must be identified once, or the PRISMA
        identification count is inflated before dedupe-records ever runs."""
        p1 = {"results": [work(1)], "meta": {"next_cursor": "CUR2"}}
        p2 = {"results": [work(1)], "meta": {"next_cursor": None}}
        with mock.patch.object(so.urllib.request, "urlopen", pages(p1, p2)):
            got = so.search(self.args())
        self.assertEqual(len(got), 1)

    def test_max_caps_results(self):
        payload = {"results": [work(i) for i in range(10)], "meta": {"next_cursor": None}}
        with mock.patch.object(so.urllib.request, "urlopen", pages(payload)):
            got = so.search(self.args(max=4))
        self.assertLessEqual(len(got), 4)

    def test_empty_result_set(self):
        payload = {"results": [], "meta": {"next_cursor": None}}
        with mock.patch.object(so.urllib.request, "urlopen", pages(payload)):
            self.assertEqual(so.search(self.args()), [])

    def test_http_error_does_not_crash_the_run(self):
        err = urllib.error.HTTPError("u", 503, "unavailable", None, None)
        with mock.patch.object(so.urllib.request, "urlopen", pages(err)):
            got = so.search(self.args())
        self.assertEqual(got, [])

    def test_filters_are_sent(self):
        seen = {}

        def _open(req, timeout=None):
            seen["url"] = req.full_url
            return FakeResponse(json.dumps(
                {"results": [], "meta": {"next_cursor": None}}).encode("utf-8"))

        with mock.patch.object(so.urllib.request, "urlopen", _open):
            so.search(self.args(from_date="2020-01-01", type="article", lang="en"))
        self.assertIn("from_publication_date%3A2020-01-01", seen["url"].replace(":", "%3A"))
        self.assertIn("filter", seen["url"])


class TestEmit(unittest.TestCase):
    def test_jsonl_one_record_per_line(self):
        out = io.StringIO()
        with mock.patch.object(sys, "stdout", out):
            so.emit([so.to_record(work(1)), so.to_record(work(2))], as_md=False)
        lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["title"], "Study 1")


class TestNoNetworkLeak(unittest.TestCase):
    def test_all_traffic_funnels_through_one_call_site(self):
        """One patch point covers the module."""
        import inspect
        self.assertEqual(inspect.getsource(so).count("urlopen("), 1)


if __name__ == "__main__":
    unittest.main()
