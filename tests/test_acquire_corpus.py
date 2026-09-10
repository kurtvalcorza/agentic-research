from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from _load import load

acq = load("skills/acquire-corpus/scripts/acquire_corpus.py")


def config(tmp: Path, **overrides):
    values = dict(
        queries=("quantum widgets",),
        output_dir=tmp / "corpus",
        run_date="2026-09-10",
        keyless_only=False,
        orx_strategies=("keyword", "embedding"),
        orx_limit=5,
    )
    values.update(overrides)
    return acq.AcquisitionConfig(**values)


def keyless_record(title="Baseline paper"):
    return {
        "openalex_id": "https://openalex.org/W1",
        "doi": "10.1000/base",
        "title": title,
        "authors": ["Ada Smith"],
        "year": 2025,
        "venue": "Journal",
        "type": "article",
        "is_retracted": False,
        "abstract": "",
        "cited_by_count": 1,
        "referenced_works": [],
    }


class TestLitHitNormalization(unittest.TestCase):
    def test_maps_supported_lithit(self):
        raw = [{
            "source": "alphaxiv",
            "id": "10.1000/example",
            "title": "Example paper",
            "abstract": "Abstract",
            "publicationDate": "2025-04-12",
            "votes": 2,
            "snippets": [{"pageNumber": 1, "snippet": "match"}],
        }]
        records, drops = acq.normalize_lithit_response(raw, "keyword")
        self.assertEqual(drops, {})
        self.assertEqual(records[0]["source"], "orx")
        self.assertEqual(records[0]["sub_source"], "alphaxiv")
        self.assertEqual(records[0]["doi"], "10.1000/example")
        self.assertEqual(records[0]["year"], 2025)
        self.assertNotIn("authors", records[0])

    def test_unknown_top_level_key_fails_whole_response(self):
        raw = [{
            "source": "alphaxiv", "id": "1234.5678", "title": "Example",
            "futureField": "new",
        }]
        with self.assertRaises(acq.EnrichmentFailure) as ctx:
            acq.normalize_lithit_response(raw, "keyword")
        self.assertIn("unknown-key", ctx.exception.reason)

    def test_strategy_source_mismatch_fails_closed(self):
        raw = [{"source": "openalex", "id": "W1", "title": "Example"}]
        with self.assertRaises(acq.EnrichmentFailure):
            acq.normalize_lithit_response(raw, "keyword")

    def test_invalid_record_is_counted_without_fabrication(self):
        raw = [
            {"source": "alphaxiv", "id": "", "title": "Bad"},
            {"source": "alphaxiv", "id": "1234.5678", "title": "Good"},
        ]
        records, drops = acq.normalize_lithit_response(raw, "keyword")
        self.assertEqual(len(records), 1)
        self.assertEqual(drops["missing-or-invalid-required-discovery-field"], 1)
        self.assertNotIn("authors", records[0])


class TestSafeAdmission(unittest.TestCase):
    def test_unresolved_hit_never_gains_empty_authors(self):
        rec = {
            "source": "orx", "sub_source": "alphaxiv",
            "source_id": "1234.5678", "orx_strategy": "keyword",
            "title": "Unresolved paper", "year": 2025,
        }
        admitted, unresolved = acq.admit_enriched_hit(
            rec, config(Path(".")), resolver=lambda _r, _c: None
        )
        self.assertIsNone(admitted)
        self.assertEqual(unresolved["reason"], "bibliographic-metadata-unresolved")
        self.assertNotIn("authors", unresolved)

    def test_verified_authors_and_year_admit(self):
        rec = {
            "source": "orx", "sub_source": "alphaxiv",
            "source_id": "1234.5678", "orx_strategy": "keyword",
            "title": "Resolved paper", "year": 2025,
        }
        resolver = lambda _r, _c: {
            "authors": ["Grace Hopper"], "year": 2025, "doi": "10.1000/resolved"
        }
        admitted, unresolved = acq.admit_enriched_hit(
            rec, config(Path(".")), resolver=resolver
        )
        self.assertIsNone(unresolved)
        self.assertEqual(admitted["authors"], ["Grace Hopper"])
        self.assertEqual(admitted["year"], 2025)
        self.assertFalse(admitted["identifier_less"])


class TestAcquisition(unittest.TestCase):
    def test_absent_orx_preserves_keyless_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td), orx_strategies=("keyword",))
            baseline = [keyless_record()]

            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: list(baseline),
                which=lambda _name: None,
            )

            lines = (cfg.output_dir / "candidates.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual([json.loads(line) for line in lines], baseline)
            self.assertFalse(record["orx_available"])
            self.assertEqual(record["enrichment_mode"], "auto")
            self.assertTrue(all(q["backend"] == "keyless" for q in record["queries"]))

    def test_keyless_only_records_intent_without_invoking_orx(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td), keyless_only=True)
            called = []

            def version_reader(_exe):
                called.append("version")
                return "should-not-run"

            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: [keyless_record()],
                which=lambda _name: "/usr/bin/orx",
                version_reader=version_reader,
            )
            self.assertTrue(record["orx_available"])
            self.assertEqual(record["enrichment_mode"], "keyless-only")
            self.assertEqual(called, [])
            log = (cfg.output_dir / "search-log.md").read_text(encoding="utf-8")
            self.assertIn("intentionally restricted", log)
            self.assertNotIn("Enrichment degradation", log)

    def test_failure_opens_alphaxiv_circuit_and_survives_log_generation(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td), orx_strategies=("keyword", "embedding"))
            calls = []

            def failing_runner(_exe, strategy, _query, _cfg):
                calls.append(strategy)
                raise acq.EnrichmentFailure("timeout", elapsed=5)

            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: [keyless_record()],
                which=lambda _name: "/usr/bin/orx",
                version_reader=lambda _exe: "orx 0.9.0",
                orx_runner=failing_runner,
            )
            self.assertEqual(calls, ["keyword"])
            outcomes = [q["outcome"] for q in record["queries"] if q["backend"] == "orx"]
            self.assertEqual(outcomes, ["failed-and-fell-back", "skipped-circuit-open"])
            log = (cfg.output_dir / "search-log.md").read_text(encoding="utf-8")
            self.assertIn("Enrichment degradation", log)
            self.assertIn("failed-and-fell-back", log)
            self.assertIn("skipped-circuit-open", log)

    def test_unresolved_enrichment_is_outside_candidates_and_handed_off(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td), orx_strategies=("keyword",))
            raw = [{
                "source": "alphaxiv",
                "id": "1234.5678",
                "title": "Full text only paper",
                "publicationDate": "2025-01-02",
            }]

            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: [keyless_record()],
                which=lambda _name: "/usr/bin/orx",
                version_reader=lambda _exe: "orx 0.9.0",
                orx_runner=lambda *_args, **_kwargs: (raw, 0.1),
                metadata_resolver=lambda _rec, _cfg: None,
            )

            candidates = [
                json.loads(line)
                for line in (cfg.output_dir / "candidates.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(candidates, [keyless_record()])
            unresolved = [
                json.loads(line)
                for line in (cfg.output_dir / "enrichment-unresolved.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(len(unresolved), 1)
            self.assertEqual(record["unresolved"]["count"], 1)
            log = (cfg.output_dir / "search-log.md").read_text(encoding="utf-8")
            self.assertIn("Unresolved enrichment", log)
            self.assertIn(record["unresolved"]["path"], log)


if __name__ == "__main__":
    unittest.main()
