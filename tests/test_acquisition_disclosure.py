from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from _load import load

gate = load("skills/acquire-corpus/scripts/acquisition_disclosure.py")


def query(**overrides):
    value = {
        "backend": "keyless",
        "sub_source": "openalex",
        "strategy": "search",
        "query": "widgets",
        "date": "2026-09-10",
        "outcome": "answered",
        "returned_count": 2,
        "normalization_drops": [],
        "admitted_enriched_count": 0,
        "unresolved_enrichment_count": 0,
        "unresolved_reasons": [],
        "circuit_open": False,
        "orx_version": None,
        "failure_reason": None,
    }
    value.update(overrides)
    return value


def record(*queries, disclosure=None, unresolved=0, mode="auto"):
    return {
        "schema_version": "1.0",
        "run_date": "2026-09-10",
        "enrichment_mode": mode,
        "orx_available": True,
        "queries": list(queries or [query()]),
        "reproducibility_disclosure": disclosure or {
            "requires_openresearch": False,
            "successful_enrichment": [],
        },
        "unresolved": {
            "count": unresolved,
            "path": "corpus/enrichment-unresolved.jsonl",
        },
    }


class TestParsing(unittest.TestCase):
    def test_valid_keyless_record(self):
        parsed = gate.parse(record(query()))
        self.assertEqual(gate.check(parsed), [])

    def test_unknown_key_is_malformed(self):
        raw = record(query())
        raw["surprise"] = True
        with self.assertRaises(gate.InputError):
            gate.parse(raw)

    def test_numeric_string_is_malformed(self):
        raw = record(query(returned_count="2"))
        with self.assertRaises(gate.InputError):
            gate.parse(raw)

    def test_empty_queries_is_malformed(self):
        raw = record(query())
        raw["queries"] = []
        with self.assertRaises(gate.InputError):
            gate.parse(raw)


class TestDisclosure(unittest.TestCase):
    def enriched(self, version="orx 0.9.0"):
        return query(
            backend="orx",
            sub_source="alphaxiv",
            strategy="keyword",
            outcome="answered",
            returned_count=1,
            admitted_enriched_count=1,
            orx_version=version,
        )

    def disclosure(self, version="orx 0.9.0"):
        return {
            "requires_openresearch": True,
            "successful_enrichment": [{
                "query": "widgets",
                "strategy": "keyword",
                "sub_source": "alphaxiv",
                "orx_version": version,
            }],
        }

    def test_enriched_with_matching_disclosure_passes(self):
        parsed = gate.parse(record(query(), self.enriched(), disclosure=self.disclosure()))
        self.assertEqual(gate.check(parsed), [])

    def test_missing_disclosure_is_method_violation(self):
        parsed = gate.parse(record(query(), self.enriched()))
        issues = gate.check(parsed)
        self.assertTrue(any("requires_openresearch is false" in issue for issue in issues))
        self.assertTrue(any("omits" in issue for issue in issues))

    def test_missing_version_is_method_violation_not_malformed(self):
        disclosure = self.disclosure(version=None)
        parsed = gate.parse(record(query(), self.enriched(version=None), disclosure=disclosure))
        issues = gate.check(parsed)
        self.assertTrue(any("no OpenResearch version" in issue for issue in issues))

    def test_unresolved_count_must_reconcile(self):
        enriched = self.enriched()
        enriched["unresolved_enrichment_count"] = 2
        parsed = gate.parse(record(query(), enriched, disclosure=self.disclosure(), unresolved=1))
        issues = gate.check(parsed)
        self.assertTrue(any("unresolved count mismatch" in issue for issue in issues))


class TestCli(unittest.TestCase):
    def test_strict_violation_exits_one(self):
        raw = record(query(), TestDisclosure().enriched())
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
            json.dump(raw, fh)
            path = fh.name
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        with mock.patch("sys.stdout", new=io.StringIO()), mock.patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(gate.main([path, "--strict"]), 1)

    def test_malformed_exits_two_without_stdout(self):
        raw = record(query())
        raw["queries"] = []
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
            json.dump(raw, fh)
            path = fh.name
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdout", new=out), mock.patch("sys.stderr", new=err):
            self.assertEqual(gate.main([path, "--json"]), 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("malformed input", err.getvalue())

    def test_json_output_uses_shared_envelope(self):
        raw = record(query())
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
            json.dump(raw, fh)
            path = fh.name
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        out = io.StringIO()
        with mock.patch("sys.stdout", new=out):
            self.assertEqual(gate.main([path, "--json", "--strict"]), 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["check"], "acquisition_disclosure")
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["issues"], 0)
        self.assertEqual(payload["units"], {})
        self.assertEqual(payload["gates"], {})
        self.assertEqual(payload["unattributed"], 0)


if __name__ == "__main__":
    unittest.main()
