"""Coverage for skills/verify-sources/scripts/resolve_citation.py.

NO NETWORK. Every test patches urllib.request.urlopen inside the module, so an
unmocked code path raises rather than quietly reaching the internet — that turns
"the suite makes no requests" from a convention into an enforced property.

Standard library only.
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

rc = load("skills/verify-sources/scripts/resolve_citation.py")


class FakeResponse(io.BytesIO):
    """Minimal stand-in for the urlopen context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def responder(mapping, default=None):
    """Return a urlopen replacement dispatching on a substring of the URL."""
    def _open(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        for needle, payload in mapping.items():
            if needle in url:
                if isinstance(payload, Exception):
                    raise payload
                return FakeResponse(json.dumps(payload).encode("utf-8"))
        if default is None:
            raise AssertionError(f"unexpected request to {url}")
        if isinstance(default, Exception):
            raise default
        return FakeResponse(json.dumps(default).encode("utf-8"))
    return _open


OPENALEX_OK = {
    "title": "Ileal-lymphoid-nodular hyperplasia",
    "authorships": [{"author": {"display_name": "A Wakefield"}}],
    "publication_year": 1998,
    "primary_location": {"source": {"display_name": "The Lancet"}},
    "is_retracted": True,
}
OPENALEX_CLEAN = dict(OPENALEX_OK, is_retracted=False, title="A perfectly fine paper")


class TestCleanDoi(unittest.TestCase):
    def test_strips_url_prefixes(self):
        for form in ("https://doi.org/10.1/abc", "http://dx.doi.org/10.1/abc", "doi:10.1/abc"):
            with self.subTest(form=form):
                self.assertEqual(rc._clean_doi(form), "10.1/abc")

    def test_prefix_not_character_set(self):
        """'doi:' is stripped as a PREFIX — a DOI containing those letters survives."""
        self.assertEqual(rc._clean_doi("10.1/void-index"), "10.1/void-index")

    def test_empty(self):
        self.assertEqual(rc._clean_doi(None), "")


class TestResolveDoi(unittest.TestCase):
    def test_retracted_paper_flagged(self):
        with mock.patch.object(rc.urllib.request, "urlopen",
                               responder({"api.openalex.org": OPENALEX_OK})):
            out = rc.resolve_doi("10.1016/S0140-6736(97)11096-0", "")
        self.assertEqual(out["status"], "RETRACTED")
        self.assertTrue(out["is_retracted"])
        self.assertEqual(out["retraction_source"], "openalex:is_retracted")
        self.assertEqual(out["backend"], "openalex")

    def test_clean_paper_verified(self):
        with mock.patch.object(rc.urllib.request, "urlopen",
                               responder({"api.openalex.org": OPENALEX_CLEAN})):
            out = rc.resolve_doi("10.1/ok", "")
        self.assertEqual(out["status"], "VERIFIED")
        self.assertFalse(out["is_retracted"])
        self.assertEqual(out["journal"], "The Lancet")
        self.assertEqual(out["year"], 1998)

    def test_falls_back_to_crossref_when_openalex_misses(self):
        crossref = {"message": {"title": ["A CrossRef paper"],
                                "author": [{"given": "Ada", "family": "Smith"}],
                                "published": {"date-parts": [[2021, 3]]},
                                "container-title": ["Journal of Things"]}}
        with mock.patch.object(rc.urllib.request, "urlopen", responder({
                "api.openalex.org": urllib.error.HTTPError("u", 404, "nf", None, None),
                "api.crossref.org": crossref})):
            out = rc.resolve_doi("10.1/xref", "")
        self.assertEqual(out["backend"], "crossref")
        self.assertEqual(out["status"], "VERIFIED")
        self.assertEqual(out["year"], 2021)
        self.assertEqual(out["authors"], ["Ada Smith"])

    def test_crossref_retraction_detected(self):
        crossref = {"message": {"title": ["Retracted via CrossRef"],
                                "update-to": [{"type": "retraction", "DOI": "10.1/notice"}]}}
        with mock.patch.object(rc.urllib.request, "urlopen", responder({
                "api.openalex.org": urllib.error.HTTPError("u", 404, "nf", None, None),
                "api.crossref.org": crossref})):
            out = rc.resolve_doi("10.1/retracted", "")
        self.assertEqual(out["status"], "RETRACTED")
        self.assertIn("crossref:update-to", out["retraction_source"])

    def test_unresolvable_doi_stays_unverified(self):
        """A fabricated DOI must not come back VERIFIED."""
        err = urllib.error.HTTPError("u", 404, "not found", None, None)
        with mock.patch.object(rc.urllib.request, "urlopen", responder({}, default=err)):
            out = rc.resolve_doi("10.9999/definitely-made-up", "")
        self.assertEqual(out["status"], "UNVERIFIED")
        self.assertIn("unresolved", out["note"])
        self.assertIn("HTTP 404", out["note"])

    def test_network_failure_is_reported_not_raised(self):
        with mock.patch.object(rc.urllib.request, "urlopen",
                               responder({}, default=OSError("connection reset"))):
            out = rc.resolve_doi("10.1/x", "")
        self.assertEqual(out["status"], "UNVERIFIED")
        self.assertIn("connection reset", out["note"])


class TestReverseLookup(unittest.TestCase):
    def test_title_match_resolves_via_doi(self):
        search = {"results": [{"publication_year": 2024, "doi": "https://doi.org/10.1/found",
                               "authorships": [{"author": {"display_name": "Ada Smith"}}]}]}
        with mock.patch.object(rc.urllib.request, "urlopen", responder({
                "works?search=": search, "works/doi:": OPENALEX_CLEAN})):
            out = rc.reverse_lookup("A perfectly fine paper", "smith", 2024, "")
        self.assertEqual(out["status"], "VERIFIED")
        self.assertEqual(out["note"], "matched via title reverse-lookup")

    def test_candidates_but_no_author_match_is_unverified(self):
        search = {"results": [{"publication_year": 2024, "doi": "10.1/other",
                               "authorships": [{"author": {"display_name": "Bo Jones"}}]}]}
        with mock.patch.object(rc.urllib.request, "urlopen",
                               responder({"works?search=": search})):
            out = rc.reverse_lookup("Some title", "smith", 2024, "")
        self.assertEqual(out["status"], "UNVERIFIED")
        self.assertIn("review manually", out["note"])

    def test_no_record_suggests_fabrication(self):
        """The headline failure mode this repository exists to catch."""
        with mock.patch.object(rc.urllib.request, "urlopen",
                               responder({"works?search=": {"results": []}})):
            out = rc.reverse_lookup("A title nobody ever wrote", "", "", "")
        self.assertEqual(out["status"], "UNVERIFIED")
        self.assertIn("likely fabricated", out["note"])

    def test_year_tolerance_of_one(self):
        search = {"results": [{"publication_year": 2023, "doi": "10.1/found",
                               "authorships": [{"author": {"display_name": "Ada Smith"}}]}]}
        with mock.patch.object(rc.urllib.request, "urlopen", responder({
                "works?search=": search, "works/doi:": OPENALEX_CLEAN})):
            out = rc.reverse_lookup("A paper", "smith", 2024, "")
        self.assertEqual(out["status"], "VERIFIED")


class TestNoNetworkLeak(unittest.TestCase):
    """Proves the mocking strategy actually isolates the network.

    Note `_get` catches `Exception` broadly and converts every failure into an
    error tuple — by design, since any failure is a resolution miss. That means an
    AssertionError raised by the responder is swallowed rather than propagated, so
    the isolation is asserted on the returned error instead of on a raise.
    """

    def test_unexpected_url_is_intercepted_not_fetched(self):
        with mock.patch.object(rc.urllib.request, "urlopen", responder({})):
            data, err = rc._get("https://example.invalid/x", "")
        self.assertIsNone(data)
        self.assertIn("unexpected request", err)

    def test_every_request_goes_through_get(self):
        """One patch point covers the module: all traffic funnels through _get."""
        import inspect
        source = inspect.getsource(rc)
        # urlopen appears exactly once — inside _get.
        self.assertEqual(source.count("urlopen("), 1)


if __name__ == "__main__":
    unittest.main()
