"""Failure-mode regressions for the acquire-corpus enrichment path (PR #33 review).

Each class binds one reviewer finding to a discriminating test:

- P1-1  metadata completion is bounded by the run-level failure budget/circuit
- P1-2  title/year similarity alone never promotes missing authors to verified
- P1-3  a keyless transport failure is recorded as ``incomplete``, not ``empty``
        or ``answered``
- P1-4  a zero-normalizable response keeps its normalization-drop counts
- P2    structured loss/method disclosures exist, are rendered, and are
        reconciled by the disclosure gate

Standard library only; no network.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error

from _load import load

acq = load("skills/acquire-corpus/scripts/acquire_corpus.py")
gate = load("skills/acquire-corpus/scripts/acquisition_disclosure.py")

REPO = Path(__file__).resolve().parent.parent
ARXIV_ID = "1234.5678"


def config(tmp: Path, **overrides):
    values = dict(
        queries=("quantum widgets",),
        output_dir=tmp / "corpus",
        run_date="2026-09-11",
        keyless_only=False,
        orx_strategies=("keyword",),
        orx_limit=15,
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


def alphaxiv_hit(idx: int, title: str | None = None):
    return {
        "source": "alphaxiv",
        "id": f"2401.{10000 + idx:05d}",
        "title": title or f"Discovered paper {idx}",
        "publicationDate": "2025-03-01",
    }


def lithit_batch(strategy: str, count: int):
    source = acq.STRATEGY_SUB_SOURCE[strategy]
    out = []
    for idx in range(count):
        if source == "alphaxiv":
            out.append(alphaxiv_hit(idx))
        elif source == "openalex":
            out.append({"source": "openalex", "id": f"W{1000 + idx}", "title": f"OA paper {idx}"})
        else:
            out.append({
                "source": "biorxiv", "id": f"10.1101/2025.01.01.{idx:06d}",
                "title": f"bioRxiv paper {idx}",
            })
    return out


def openalex_candidate(*, title, year, doi, authors, extra=None):
    cand = {
        "id": "https://openalex.org/W999",
        "title": title,
        "publication_year": year,
        "doi": f"https://doi.org/{doi}" if doi else None,
        "authorships": [{"author": {"display_name": name}} for name in authors],
        "primary_location": {"source": {"display_name": "Venue"}},
        "type": "article",
    }
    cand.update(extra or {})
    return cand


def run_gate(record: dict) -> list[str]:
    return gate.check(gate.parse(json.loads(json.dumps(record))))


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class TestP1MetadataCompletionBudget(unittest.TestCase):
    """P1-1: many enriched hits through a timeout stub -> bounded attempts/wait."""

    def test_timeouts_are_bounded_by_run_budget_and_circuit(self):
        strategies = ("keyword", "embedding", "openalex", "biorxiv")
        attempts = []

        def timing_out_http(url, _mailto="", timeout=None):
            attempts.append(url)
            raise TimeoutError("simulated OpenAlex timeout")

        def resolver(rec, cfg):
            return acq.resolve_openalex_metadata(rec, cfg, http_json=timing_out_http)

        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td), orx_strategies=strategies, orx_limit=15)
            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: [keyless_record()],
                which=lambda _name: "/usr/bin/orx",
                version_reader=lambda _exe: "orx 0.9.0",
                orx_runner=lambda _e, strategy, _q, _c: (lithit_batch(strategy, 15), 0.1),
                metadata_resolver=resolver,
            )
            hits = 15 * len(strategies)
            max_by_budget = int(
                acq.ENRICHMENT_FAILURE_BUDGET_SECONDS // acq.ORX_TIMEOUT_SECONDS
            )
            self.assertLessEqual(
                len(attempts), max_by_budget,
                f"{len(attempts)} metadata-completion requests for {hits} hits; the "
                f"15 s failure budget allows at most {max_by_budget} five-second waits",
            )
            # One transport failure opens the completion circuit for the run.
            self.assertEqual(len(attempts), 1)
            self.assertEqual(record["unresolved"]["count"], hits)
            self.assertEqual(record["loss_summary"]["metadata_completion_skipped_count"], hits)
            reasons = {
                item["reason"]
                for q in record["queries"] if q["backend"] == "orx"
                for item in q["unresolved_reasons"]
            }
            self.assertEqual(
                reasons,
                {"metadata-completion-timeout", "metadata-completion-skipped:circuit-open"},
            )
            candidates = read_jsonl(cfg.output_dir / "candidates.jsonl")
            self.assertEqual(candidates, [keyless_record()])
            self.assertEqual(run_gate(record), [])

    def test_budget_exhausted_by_discovery_skips_completion_without_requests(self):
        attempts = []

        def resolver(rec, cfg):
            attempts.append(rec["source_id"])
            return {"authors": ["Grace Hopper"], "year": 2025}

        runs = []

        def runner(_exe, strategy, _q, _c):
            runs.append(strategy)
            if strategy in {"keyword", "openalex", "biorxiv"}:
                raise acq.EnrichmentFailure("timeout", elapsed=5.0)
            return (lithit_batch(strategy, 3), 0.1)

        with tempfile.TemporaryDirectory() as td:
            # Three failed sub-sources exhaust the 15 s budget before embedding runs.
            cfg = config(Path(td), orx_strategies=("keyword", "openalex", "biorxiv", "embedding"))
            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: [keyless_record()],
                which=lambda _name: "/usr/bin/orx",
                version_reader=lambda _exe: "orx 0.9.0",
                orx_runner=runner,
                metadata_resolver=resolver,
            )
            self.assertEqual(attempts, [])
            outcomes = [q["outcome"] for q in record["queries"] if q["backend"] == "orx"]
            self.assertEqual(
                outcomes,
                ["failed-and-fell-back"] * 3 + ["skipped-circuit-open"],
            )
            self.assertEqual(run_gate(record), [])

    def test_repeated_identifier_is_resolved_once(self):
        attempts = []

        def resolver(rec, _cfg):
            attempts.append(rec["source_id"])
            return {"authors": ["Grace Hopper"], "year": 2025, "doi": f"10.48550/arxiv.{ARXIV_ID}"}

        same = {"source": "alphaxiv", "id": ARXIV_ID, "title": "Same paper", "publicationDate": "2025-01-01"}
        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td), orx_strategies=("keyword", "embedding"))
            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: [],
                which=lambda _name: "/usr/bin/orx",
                version_reader=lambda _exe: "orx 0.9.0",
                orx_runner=lambda *_a, **_k: ([dict(same)], 0.1),
                metadata_resolver=resolver,
            )
            self.assertEqual(attempts, [ARXIV_ID])
            admitted = [q["admitted_enriched_count"] for q in record["queries"] if q["backend"] == "orx"]
            self.assertEqual(admitted, [1, 1])
            self.assertEqual(run_gate(record), [])


class TestP1TitleYearIsNotIdentity(unittest.TestCase):
    """P1-2: same title/year, different study -> stays unresolved."""

    def hit(self):
        return {
            "source": "orx", "sub_source": "alphaxiv", "source_id": ARXIV_ID,
            "orx_strategy": "keyword", "title": "Deep widgets at scale", "year": 2025,
        }

    def test_candidate_matching_requires_identity_corroboration(self):
        candidate = openalex_candidate(
            title="Deep widgets at scale", year=2025, doi="10.1000/other-study",
            authors=["Mallory Other"],
        )
        self.assertFalse(acq._openalex_candidate_matches(self.hit(), candidate, direct=False))

    def test_same_title_same_year_different_authors_is_not_admitted(self):
        impostor = openalex_candidate(
            title="Deep widgets at scale", year=2025, doi="10.1000/other-study",
            authors=["Mallory Other", "Eve Adversary"],
        )
        requested = []

        def http_json(url, _mailto="", timeout=None):
            requested.append(url)
            if "/doi:" in url or "/W" in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=None)
            return {"results": [impostor]}

        def resolver(rec, cfg):
            return acq.resolve_openalex_metadata(rec, cfg, http_json=http_json)

        raw = [{
            "source": "alphaxiv", "id": ARXIV_ID, "title": "Deep widgets at scale",
            "publicationDate": "2025-06-01",
        }]
        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td))
            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: [],
                which=lambda _name: "/usr/bin/orx",
                version_reader=lambda _exe: "orx 0.9.0",
                orx_runner=lambda *_a, **_k: (raw, 0.1),
                metadata_resolver=resolver,
            )
            candidates = read_jsonl(cfg.output_dir / "candidates.jsonl")
            self.assertEqual(candidates, [], "title/year-only completion admitted a different study")
            unresolved = read_jsonl(cfg.output_dir / "enrichment-unresolved.jsonl")
            self.assertEqual(len(unresolved), 1)
            self.assertNotIn("authors", unresolved[0])
            self.assertEqual(record["unresolved"]["count"], 1)
            self.assertEqual(run_gate(record), [])

    def test_stable_identifier_match_still_resolves(self):
        genuine = openalex_candidate(
            title="Deep widgets at scale", year=2025, doi=f"10.48550/arXiv.{ARXIV_ID}",
            authors=["Grace Hopper"],
        )
        resolved = acq.resolve_openalex_metadata(
            self.hit(), config(Path(".")), http_json=lambda *_a, **_k: genuine
        )
        self.assertEqual(resolved["authors"], ["Grace Hopper"])
        self.assertEqual(resolved["year"], 2025)

    def test_hit_without_stable_identifier_makes_no_request(self):
        requested = []
        hit = dict(self.hit(), source_id="not-an-identifier")
        resolved = acq.resolve_openalex_metadata(
            hit, config(Path(".")),
            http_json=lambda url, *_a, **_k: requested.append(url) or {"results": []},
        )
        self.assertIsNone(resolved)
        self.assertEqual(requested, [])


class TestP1KeylessTransportFailureIsRecorded(unittest.TestCase):
    """P1-3: keyless failure is `incomplete`, never `empty`/`answered`."""

    def acquire_with(self, http_json, **cfg_overrides):
        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td), **cfg_overrides)
            with mock.patch.object(acq, "_http_json", http_json), \
                    mock.patch.object(acq.time, "sleep", lambda _s: None):
                record = acq.acquire(cfg, which=lambda _name: None)
            log = (cfg.output_dir / "search-log.md").read_text(encoding="utf-8")
        return record, log

    def test_first_page_failure_is_not_a_zero_result_search(self):
        def failing(_url, _mailto="", timeout=None):
            raise urllib.error.URLError("connection refused")

        record, log = self.acquire_with(failing)
        entry = record["queries"][0]
        self.assertEqual(entry["backend"], "keyless")
        self.assertNotEqual(entry["outcome"], "empty")
        self.assertEqual(entry["outcome"], "incomplete")
        self.assertEqual(entry["returned_count"], 0)
        self.assertTrue(str(entry["failure_reason"]).startswith("keyless-transport-failure:page-1:"))
        self.assertIn("Keyless baseline incomplete", log)
        self.assertEqual(run_gate(record), [])

    def test_later_page_failure_is_not_a_fully_answered_search(self):
        pages = []

        def paged(url, _mailto="", timeout=None):
            pages.append(url)
            if len(pages) == 1:
                return {
                    "results": [
                        {"id": "https://openalex.org/W1", "title": "One", "publication_year": 2025},
                        {"id": "https://openalex.org/W2", "title": "Two", "publication_year": 2025},
                    ],
                    "meta": {"next_cursor": "page2"},
                }
            raise urllib.error.URLError("reset by peer")

        record, _log = self.acquire_with(paged)
        entry = record["queries"][0]
        self.assertEqual(len(pages), 2)
        self.assertNotEqual(entry["outcome"], "answered")
        self.assertEqual(entry["outcome"], "incomplete")
        self.assertEqual(entry["returned_count"], 2)
        self.assertTrue(str(entry["failure_reason"]).startswith("keyless-transport-failure:page-2:"))
        self.assertEqual(run_gate(record), [])

    def test_exhausted_source_is_still_a_complete_answer(self):
        record, log = self.acquire_with(lambda *_a, **_k: {"results": [], "meta": {}})
        entry = record["queries"][0]
        self.assertEqual(entry["outcome"], "empty")
        self.assertIsNone(entry["failure_reason"])
        self.assertNotIn("Keyless baseline incomplete", log)

    def test_gate_requires_failure_reason_for_incomplete_and_rejects_orx_incomplete(self):
        base = {
            "backend": "keyless", "sub_source": "openalex", "strategy": "search",
            "query": "w", "date": "2026-09-11", "outcome": "incomplete", "returned_count": 0,
            "normalization_drops": [], "admitted_enriched_count": 0,
            "unresolved_enrichment_count": 0, "unresolved_reasons": [], "circuit_open": False,
            "orx_version": None, "failure_reason": None,
        }
        record = {
            "schema_version": "1.1", "run_date": "2026-09-11", "enrichment_mode": "auto",
            "orx_available": False, "queries": [base],
            "reproducibility_disclosure": {"requires_openresearch": False, "successful_enrichment": []},
            "unresolved": {"count": 0, "path": "corpus/enrichment-unresolved.jsonl"},
            "loss_summary": {
                "admitted_enriched_count": 0, "admitted_doi_less_count": 0, "unresolved_count": 0,
                "unresolved_missing_authors_count": 0, "unresolved_missing_year_count": 0,
                "metadata_completion_skipped_count": 0,
            },
            "method_disclosure": {
                "opaque_ranking_or_truncation": False, "affected_sub_sources": [],
                "orx_limit": None, "orx_prioritize": None, "is_deduplication_step": False,
            },
        }
        with self.assertRaises(gate.InputError):
            gate.parse(record)
        record["queries"][0]["failure_reason"] = "keyless-transport-failure:page-1:URLError"
        self.assertEqual(gate.check(gate.parse(record)), [])
        record["queries"][0].update(backend="orx", sub_source="alphaxiv", strategy="keyword")
        with self.assertRaises(gate.InputError):
            gate.parse(record)

    def test_main_reports_incomplete_keyless_on_stderr_and_keeps_exit_zero(self):
        record = {"queries": [{
            "backend": "keyless", "outcome": "incomplete", "query": "w",
            "failure_reason": "keyless-transport-failure:page-1:URLError", "returned_count": 0,
        }]}
        err = io.StringIO()
        with mock.patch.object(acq, "acquire", return_value=record), \
                mock.patch.object(acq.sys, "stderr", err):
            code = acq.main(["--query", "w", "--output-dir", "unused"])
        self.assertEqual(code, 0)
        self.assertIn("[search] stopped:", err.getvalue())
        self.assertIn("keyless-transport-failure:page-1:URLError", err.getvalue())


class TestP1ZeroNormalizableKeepsDropCounts(unittest.TestCase):
    """P1-4: all-invalid response -> returned_count == sum(normalization_drops)."""

    def test_all_invalid_records_are_counted_in_failed_entry(self):
        raw = [
            {"source": "alphaxiv", "id": "", "title": "No identifier"},
            {"source": "alphaxiv", "id": "2401.00001", "title": "   "},
            {"source": "alphaxiv", "id": "2401.00002", "title": "Bad votes", "votes": "many"},
        ]
        with tempfile.TemporaryDirectory() as td:
            cfg = config(Path(td))
            record = acq.acquire(
                cfg,
                keyless_search=lambda _q, _c: [keyless_record()],
                which=lambda _name: "/usr/bin/orx",
                version_reader=lambda _exe: "orx 0.9.0",
                orx_runner=lambda *_a, **_k: (raw, 0.1),
                metadata_resolver=lambda _r, _c: {"authors": ["X"], "year": 2025},
            )
            entry = [q for q in record["queries"] if q["backend"] == "orx"][0]
            self.assertEqual(entry["outcome"], "failed-and-fell-back")
            self.assertEqual(entry["failure_reason"], "zero-normalizable-records")
            self.assertEqual(entry["returned_count"], len(raw))
            dropped = sum(item["count"] for item in entry["normalization_drops"])
            self.assertEqual(entry["returned_count"], dropped)
            self.assertEqual(
                {item["reason"]: item["count"] for item in entry["normalization_drops"]},
                {"missing-or-invalid-required-discovery-field": 2, "invalid-votes": 1},
            )
            self.assertEqual(run_gate(record), [])
            log = (cfg.output_dir / "search-log.md").read_text(encoding="utf-8")
            self.assertIn("invalid-votes", log)

    def test_gate_rejects_zero_normalizable_entry_that_lost_its_drops(self):
        record = {
            "schema_version": "1.1", "run_date": "2026-09-11", "enrichment_mode": "auto",
            "orx_available": True,
            "queries": [{
                "backend": "orx", "sub_source": "alphaxiv", "strategy": "keyword",
                "query": "w", "date": "2026-09-11", "outcome": "failed-and-fell-back",
                "returned_count": 3, "normalization_drops": [], "admitted_enriched_count": 0,
                "unresolved_enrichment_count": 0, "unresolved_reasons": [], "circuit_open": True,
                "orx_version": "orx 0.9.0", "failure_reason": "zero-normalizable-records",
            }],
            "reproducibility_disclosure": {"requires_openresearch": False, "successful_enrichment": []},
            "unresolved": {"count": 0, "path": "corpus/enrichment-unresolved.jsonl"},
            "loss_summary": {
                "admitted_enriched_count": 0, "admitted_doi_less_count": 0, "unresolved_count": 0,
                "unresolved_missing_authors_count": 0, "unresolved_missing_year_count": 0,
                "metadata_completion_skipped_count": 0,
            },
            "method_disclosure": {
                "opaque_ranking_or_truncation": False, "affected_sub_sources": [],
                "orx_limit": None, "orx_prioritize": None, "is_deduplication_step": False,
            },
        }
        issues = gate.check(gate.parse(json.loads(json.dumps(record))))
        self.assertEqual(len(issues), 1)
        self.assertIn("zero-normalizable", issues[0])
        record["queries"][0]["normalization_drops"] = [
            {"reason": "missing-or-invalid-required-discovery-field", "count": 3}
        ]
        self.assertEqual(gate.check(gate.parse(record)), [])


class TestP2LossAndMethodDisclosure(unittest.TestCase):
    """P2: FR-022 / FR-012 / FR-023 structured disclosures, rendering, gate, docs."""

    def acquire_mixed(self, td: Path):
        raw = [
            {"source": "alphaxiv", "id": "2401.00001", "title": "Resolvable", "publicationDate": "2025-01-01"},
            {"source": "alphaxiv", "id": "2401.00002", "title": "Sparse, no year"},
            {"source": "alphaxiv", "id": "2401.00003", "title": "Sparse, has year", "publicationDate": "2024-01-01"},
        ]

        def resolver(rec, _cfg):
            if rec["source_id"] == "2401.00001":
                return {"authors": ["Grace Hopper"], "year": 2025}
            return None

        cfg = config(td, orx_limit=7, orx_prioritize="recency")
        record = acq.acquire(
            cfg,
            keyless_search=lambda _q, _c: [keyless_record()],
            which=lambda _name: "/usr/bin/orx",
            version_reader=lambda _exe: "orx 0.9.0",
            orx_runner=lambda *_a, **_k: (raw, 0.1),
            metadata_resolver=resolver,
        )
        return cfg, record

    def test_record_carries_structured_loss_and_method_summaries(self):
        with tempfile.TemporaryDirectory() as td:
            cfg, record = self.acquire_mixed(Path(td))
            self.assertEqual(record["schema_version"], "1.1")
            self.assertEqual(record["loss_summary"], {
                "admitted_enriched_count": 1,
                "admitted_doi_less_count": 1,
                "unresolved_count": 2,
                "unresolved_missing_authors_count": 2,
                "unresolved_missing_year_count": 1,
                "metadata_completion_skipped_count": 0,
            })
            self.assertEqual(record["method_disclosure"], {
                "opaque_ranking_or_truncation": True,
                "affected_sub_sources": ["alphaxiv"],
                "orx_limit": 7,
                "orx_prioritize": "recency",
                "is_deduplication_step": False,
            })
            self.assertEqual(run_gate(record), [])
            log = (cfg.output_dir / "search-log.md").read_text(encoding="utf-8")
            self.assertIn("| Dropped |", log)
            self.assertIn("## Loss summary", log)
            self.assertIn("without a DOI: **1**", log)
            self.assertIn("missing verified authors: 2; missing verified year: 1", log)
            self.assertIn("title-only false merges", log)
            self.assertIn("**not** the review's deduplication step", log)
            self.assertIn("`--limit 7`", log)

    def test_gate_reconciles_loss_and_method_summaries(self):
        with tempfile.TemporaryDirectory() as td:
            _cfg, record = self.acquire_mixed(Path(td))
        tampered = json.loads(json.dumps(record))
        tampered["loss_summary"]["admitted_doi_less_count"] = 5
        self.assertTrue(any("admitted_doi_less_count" in i for i in run_gate(tampered)))

        tampered = json.loads(json.dumps(record))
        tampered["loss_summary"]["unresolved_missing_authors_count"] = 0
        tampered["loss_summary"]["unresolved_missing_year_count"] = 0
        self.assertTrue(any("does not explain every unresolved" in i for i in run_gate(tampered)))

        tampered = json.loads(json.dumps(record))
        tampered["method_disclosure"]["is_deduplication_step"] = True
        self.assertTrue(any("deduplication" in i for i in run_gate(tampered)))

        tampered = json.loads(json.dumps(record))
        tampered["method_disclosure"]["opaque_ranking_or_truncation"] = False
        tampered["method_disclosure"]["affected_sub_sources"] = []
        issues = run_gate(tampered)
        self.assertTrue(any("opaque_ranking_or_truncation is false" in i for i in issues))

    def test_schema_1_0_records_are_still_accepted_and_closed(self):
        legacy = {
            "schema_version": "1.0", "run_date": "2026-09-10", "enrichment_mode": "keyless-only",
            "orx_available": False,
            "queries": [{
                "backend": "keyless", "sub_source": "openalex", "strategy": "search",
                "query": "w", "date": "2026-09-10", "outcome": "answered", "returned_count": 1,
                "normalization_drops": [], "admitted_enriched_count": 0,
                "unresolved_enrichment_count": 0, "unresolved_reasons": [], "circuit_open": False,
                "orx_version": None, "failure_reason": None,
            }],
            "reproducibility_disclosure": {"requires_openresearch": False, "successful_enrichment": []},
            "unresolved": {"count": 0, "path": "corpus/enrichment-unresolved.jsonl"},
        }
        self.assertEqual(gate.check(gate.parse(json.loads(json.dumps(legacy)))), [])
        with_summary = dict(legacy, loss_summary={})
        with self.assertRaises(gate.InputError):
            gate.parse(with_summary)
        legacy["queries"][0].update(outcome="incomplete", failure_reason="x")
        with self.assertRaises(gate.InputError):
            gate.parse(legacy)
        modern = dict(legacy, schema_version="1.1")
        modern["queries"][0].update(outcome="answered", failure_reason=None)
        with self.assertRaises(gate.InputError):
            gate.parse(modern)  # 1.1 requires the summaries

    def test_owning_docs_state_doi_less_reverse_lookup_guidance(self):
        for rel in ("skills/acquire-corpus/SKILL.md", "skills/acquire-corpus/README.md"):
            text = (REPO / rel).read_text(encoding="utf-8").casefold()
            with self.subTest(doc=rel):
                self.assertIn("cannot be resolved directly by doi", text)
                self.assertIn("title/author/year reverse lookup", text)
                self.assertIn("incomplete", text)


if __name__ == "__main__":
    unittest.main()
