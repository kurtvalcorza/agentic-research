"""Cross-gate conformance for the acquire-corpus disclosure gate.

The core conformance modules predate ``acquisition_disclosure.py`` and enumerate the
four gates introduced by the standards-enforcement feature. This module binds the
new gate to the same repository-wide contracts without changing those historical
fixtures: numeric coercion, ``--strict`` exit semantics, ``--json`` envelope shape,
malformed-input behavior, and Principle VI limitation disclosure.

Standard library only.
"""
from __future__ import annotations

import io
import json
import math
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent

ad = load("skills/acquire-corpus/scripts/acquisition_disclosure.py")
pf = load("skills/prisma-flow/scripts/prisma_flow.py")
gp = load("skills/validate-evidence/scripts/grade_profile.py")
ru = load("skills/verify-review/scripts/review_units.py")
ra = load("skills/appraise-risk-of-bias/scripts/rob_appraisal.py")


def keyless_record() -> dict:
    return {
        "schema_version": "1.0",
        "run_date": "2026-09-10",
        "enrichment_mode": "keyless-only",
        "orx_available": False,
        "queries": [{
            "backend": "keyless",
            "sub_source": "openalex",
            "strategy": "search",
            "query": "widgets",
            "date": "2026-09-10",
            "outcome": "answered",
            "returned_count": 1,
            "normalization_drops": [],
            "admitted_enriched_count": 0,
            "unresolved_enrichment_count": 0,
            "unresolved_reasons": [],
            "circuit_open": False,
            "orx_version": None,
            "failure_reason": None,
        }],
        "reproducibility_disclosure": {
            "requires_openresearch": False,
            "successful_enrichment": [],
        },
        "unresolved": {
            "count": 0,
            "path": "corpus/enrichment-unresolved.jsonl",
        },
    }


def undisclosed_enriched_record() -> dict:
    rec = keyless_record()
    rec["enrichment_mode"] = "auto"
    rec["orx_available"] = True
    rec["queries"].append({
        "backend": "orx",
        "sub_source": "alphaxiv",
        "strategy": "keyword",
        "query": "widgets",
        "date": "2026-09-10",
        "outcome": "answered",
        "returned_count": 1,
        "normalization_drops": [],
        "admitted_enriched_count": 1,
        "unresolved_enrichment_count": 0,
        "unresolved_reasons": [],
        "circuit_open": False,
        "orx_version": "orx 0.9.0",
        "failure_reason": None,
    })
    return rec


def run_gate(record: dict, *flags: str):
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", encoding="utf-8", delete=False
    ) as handle:
        json.dump(record, handle)
        path = pathlib.Path(handle.name)
    try:
        proc = subprocess.run(
            [sys.executable,
             str(REPO / "skills/acquire-corpus/scripts/acquisition_disclosure.py"),
             str(path), *flags],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout, proc.stderr
    finally:
        path.unlink(missing_ok=True)


class TestNumericCoercionMatchesSharedContract(unittest.TestCase):
    def test_rejects_values_the_existing_discrete_counters_reject(self):
        rejected = [
            True, False, -1, float("nan"), float("inf"), 3.5,
            "3", "many", None, [], {},
        ]
        for value in rejected:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ad.InputError):
                    ad._count(value, "x")

    def test_accepts_whole_non_negative_json_numbers(self):
        for value in (0, 1, 9, 3.0):
            with self.subTest(value=value):
                self.assertEqual(ad._count(value, "x"), int(value))

    def test_existing_discrete_counters_and_new_gate_agree_on_sample(self):
        existing = [
            (lambda v: pf._int(v, "x"), pf.CountError),
            (lambda v: gp._int(v, "x"), gp.InputError),
            (lambda v: ru._as_int_count(v, "x"), ru.InputError),
            (lambda v: ra._stars(v, "x", 9), ra.InputError),
        ]
        samples = [True, -1, math.nan, "3", None, {}, 3.5]
        for value in samples:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ad.InputError):
                    ad._count(value, "x")
                for fn, exc in existing:
                    with self.assertRaises(exc):
                        fn(value)


class TestSharedCliContract(unittest.TestCase):
    def test_clean_json_envelope_has_shared_shape(self):
        code, out, err = run_gate(keyless_record(), "--strict", "--json")
        self.assertEqual(code, 0, msg=err)
        payload = json.loads(out)
        self.assertEqual(payload["check"], "acquisition_disclosure")
        self.assertEqual(payload["schema_version"], "1.0")
        for key in ("issues", "units", "gates", "unattributed"):
            self.assertIn(key, payload)
        self.assertEqual(payload["units"], {})
        self.assertEqual(payload["gates"], {})

    def test_json_changes_rendering_not_exit_semantics(self):
        for record in (keyless_record(), undisclosed_enriched_record()):
            with self.subTest(enriched=len(record["queries"]) > 1):
                plain, _, _ = run_gate(record, "--strict")
                as_json, _, _ = run_gate(record, "--strict", "--json")
                self.assertEqual(plain, as_json)

    def test_method_violation_is_one_under_strict(self):
        code, out, err = run_gate(undisclosed_enriched_record(), "--strict", "--json")
        self.assertEqual(code, 1, msg=err)
        payload = json.loads(out)
        self.assertGreater(payload["issues"], 0)
        self.assertEqual(payload["unattributed"], payload["issues"])

    def test_malformed_input_is_two_and_emits_no_envelope(self):
        rec = keyless_record()
        rec["unknown"] = True
        code, out, err = run_gate(rec, "--strict", "--json")
        self.assertEqual(code, 2)
        self.assertEqual(out.strip(), "")
        self.assertIn("malformed input", err)


class TestPrincipleViDocumentation(unittest.TestCase):
    def test_gate_states_what_it_cannot_check(self):
        script = (
            REPO / "skills/acquire-corpus/scripts/acquisition_disclosure.py"
        ).read_text(encoding="utf-8")
        self.assertIn("WHAT THIS CANNOT CHECK", script)
        self.assertIn("EXIT CODES", script)
        self.assertIn("--strict", script)

    def test_owning_skill_states_gate_limits(self):
        skill = (REPO / "skills/acquire-corpus/SKILL.md").read_text(
            encoding="utf-8"
        ).casefold()
        self.assertIn("it cannot establish that", skill)
        self.assertIn("prisma-s compliant", skill)


if __name__ == "__main__":
    unittest.main()
