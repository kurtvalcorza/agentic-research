"""Regressions for the ten findings reported against commit 2f6ce14.

Three of them were one class, and are pinned by the exit-code comparison added to
`test_differential_appraisal.py` rather than duplicated here: grade_profile.py
raised an input error (exit 2, no artifact) for records rob_appraisal.py reports
as method violations (exit 1, with diagnostics). One class-closing test is worth
more than three instance tests, and that one bites on eleven mutations across all
four instruments, not the three that were reported.

What remains, one test per finding:

  * `appraised_result` was stripped before an exact lookup, so a padded reference
    silently resolved to the unpadded target it was mistyped from;
  * the evidence profile discarded the result ID, so two results sharing a label
    rendered as indistinguishable rows with nothing linking them to diagnostics;
  * a starting level permitted only by a recorded justification rendered without
    it, leaving the reader an unexplained anomaly;
  * a file that is not valid UTF-8 raised UnicodeDecodeError past every handler —
    it is a ValueError, not an OSError — producing a traceback and exit 1 where
    the contract says exit 2;
  * manifest records carried no schema_version, so a history spanning the
    U_grade/U_rob_trace redefinition held two vocabularies that look like one.

Standard library only.
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load, fixture  # noqa: E402

gp = load("skills/validate-evidence/scripts/grade_profile.py")
ra = load("skills/appraise-risk-of-bias/scripts/rob_appraisal.py")
pc = load("skills/prisma-flow/scripts/prisma_checklist.py")
pf = load("skills/prisma-flow/scripts/prisma_flow.py")
ru = load("skills/verify-review/scripts/review_units.py")

TARGET = "diagnostic accuracy at 12 months"


class _Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def path(self, name: str) -> pathlib.Path:
        return pathlib.Path(self.dir.name) / name

    def write(self, obj, name: str) -> pathlib.Path:
        p = self.path(name)
        p.write_text(json.dumps(obj), encoding="utf-8")
        return p

    def run_module(self, mod, argv0, *args) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", [argv0, *[str(a) for a in args]]), \
                redirect_stdout(out), redirect_stderr(err):
            code = mod.main()
        return code, out.getvalue(), err.getvalue()

    def profile(self, **over):
        rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
        rec["results"][0].update(over)
        return rec

    def run_gp(self, rec, *args):
        return self.run_module(gp, "grade_profile.py", self.write(rec, "rec.json"),
                               "--rob", fixture("risk-of-bias.valid.json"), *args)


class TestAppraisedResultIsMatchedVerbatim(_Base):
    """The value is a lookup key, and normalising one side of an exact comparison
    hides the near-miss the comparison exists to surface."""

    def test_padded_target_is_reported_not_reconciled(self):
        code, out, err = self.run_gp(self.profile(appraised_result=f"  {TARGET} "),
                                     "--strict")
        self.assertEqual(code, 1, msg=out + err)
        self.assertIn("does not appear in the appraisal record", out)
        self.assertIn("matched exactly", out)
        self.assertNotIn("✅", out)

    def test_the_exact_target_still_resolves(self):
        code, out, err = self.run_gp(self.profile(appraised_result=TARGET), "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_a_blank_target_is_malformed_not_absent(self):
        """Whitespace can match nothing, so reading it as "not supplied" would report
        a missing field the caller can see they supplied."""
        code, out, err = self.run_gp(self.profile(appraised_result="   "), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("appraised_result", err)
        self.assertNotIn("Evidence profile", out)


class TestGeneratedTablesIdentifyEveryResult(_Base):
    """Only `id` must be unique, so a label cannot be the only thing on the row."""

    def two_results_one_label(self):
        rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
        second = json.loads(json.dumps(rec["results"][0]))
        second["id"] = "O2"
        second["domains"]["inconsistency"]["rating"] = 0
        second["final"] = "high"
        rec["results"].append(second)
        return rec

    def test_rows_are_distinguishable(self):
        code, out, err = self.run_gp(self.two_results_one_label(), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("| O1 |", out)
        self.assertIn("| O2 |", out)
        # Both tables, not just the evidence profile.
        self.assertEqual(out.count("| O2 |"), 2, msg=out)

    def test_the_id_column_is_declared_in_both_headers(self):
        _, out, _ = self.run_gp(self.two_results_one_label())
        self.assertIn("| ID | Result | Studies | Predominant design |", out)
        self.assertIn("| ID | Result | Studies | Certainty | What this means |", out)

    def test_notes_name_the_result_they_belong_to(self):
        _, out, _ = self.run_gp(self.two_results_one_label())
        self.assertIn("(O1)", out)
        self.assertIn("(O2)", out)


class TestStartingLevelJustificationIsRendered(_Base):
    """A start that departs from the predominant design is legal only because a
    justification was recorded; the artifact showed the departure and not the reason."""

    def observational_body(self, **over):
        rec = self.profile(
            design_mix={"rct": 0, "nrsi": 0, "observational": 4, "dta": 0,
                        "case_series": 0},
            starting_level="high", final="moderate", **over)
        return rec

    JUSTIFICATION = "Upgraded per protocol: all four are population-based with complete follow-up."

    def test_the_recorded_rationale_appears_in_the_profile(self):
        rec = self.observational_body(starting_level_justification=self.JUSTIFICATION)
        code, out, err = self.run_gp(rec, "--strict")
        self.assertEqual(code, 1, msg=err)     # the appraisal is rct, so the mix still fails
        self.assertIn(self.JUSTIFICATION, out)
        self.assertIn("† *starting level*", out)

    def test_the_row_marks_the_departure(self):
        rec = self.observational_body(starting_level_justification=self.JUSTIFICATION)
        _, out, _ = self.run_gp(rec)
        self.assertIn("| high † |", out)

    def test_an_unmarked_start_stays_unmarked(self):
        _, out, _ = self.run_gp(self.profile())
        self.assertNotIn("†", out)


class TestUndecodableInputFailsClosed(_Base):
    """UnicodeDecodeError is a ValueError, not an OSError, so it escaped both the
    read handler and the JSON one and surfaced as a traceback with exit 1."""

    def bad_bytes(self, name="bad.json") -> pathlib.Path:
        p = self.path(name)
        # Valid JSON structure, invalid UTF-8 inside it: the decoder fails before
        # the parser ever sees it.
        p.write_bytes(b'{"schema_version": "1.0", "note": "\xff\xfe not utf-8"}')
        return p

    def test_grade_profile_exits_two(self):
        code, out, err = self.run_module(gp, "grade_profile.py", self.bad_bytes())
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertEqual(out, "")

    def test_grade_profile_rob_file_exits_two(self):
        code, out, err = self.run_module(
            gp, "grade_profile.py", fixture("grade-profile.valid.json"),
            "--rob", self.bad_bytes("rob.json"), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("--rob", err)
        self.assertEqual(out, "")

    def test_rob_appraisal_exits_two(self):
        code, out, err = self.run_module(ra, "rob_appraisal.py", self.bad_bytes())
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertEqual(out, "")

    def test_prisma_checklist_exits_two(self):
        code, out, err = self.run_module(pc, "prisma_checklist.py", self.bad_bytes())
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertEqual(out, "")

    def test_prisma_flow_exits_two(self):
        """Its read was not guarded at all, so even a missing file raised."""
        code, out, err = self.run_module(pf, "prisma_flow.py", self.bad_bytes())
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertEqual(out, "")

    def test_prisma_flow_reports_a_missing_file_rather_than_raising(self):
        code, out, err = self.run_module(pf, "prisma_flow.py", self.path("absent.json"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

    def test_review_units_names_the_input_not_the_manifest(self):
        """It was caught — as a ValueError — and reported as a "manifest error",
        pointing the reader at a file that was never the problem."""
        code, out, err = self.run_module(ru, "review_units.py", self.bad_bytes())
        self.assertEqual(code, 2)
        self.assertIn("cannot decode input", err)
        self.assertNotIn("manifest error", err)


class TestManifestRecordsCarryTheirSchemaVersion(_Base):
    """Validating only the transient input left the WRITTEN history unlabelled, so a
    manifest spanning the unit redefinition holds two vocabularies that look alike."""

    def units(self):
        return json.loads(
            fixture("units.systematic-clean.json").read_text(encoding="utf-8"))

    def test_every_appended_record_is_versioned(self):
        manifest = self.path("manifest.json")
        code, out, err = self.run_module(
            ru, "review_units.py", self.write(self.units(), "u.json"),
            "--manifest", manifest)
        self.assertIn(code, (0, 1), msg=err)
        written = json.loads(manifest.read_text(encoding="utf-8"))
        record = written["verification_units"][-1]
        self.assertEqual(record["schema_version"], ru.SCHEMA_VERSION)

    def test_unversioned_history_is_migrated_explicitly(self):
        """Stamped LEGACY, not adopted into the current version.

        Silently versioning a record whose definitions are unknown is the overclaim
        the field exists to prevent — the honest label is "we do not know".
        """
        manifest = self.path("manifest.json")
        manifest.write_text(json.dumps({"verification_units": [
            {"cycle": 0, "state": "CONTINUE", "weighted_total": 9,
             "by_unit": {"U_grade": 4.0}},
        ]}), encoding="utf-8")
        self.run_module(ru, "review_units.py", self.write(self.units(), "u.json"),
                        "--manifest", manifest)
        written = json.loads(manifest.read_text(encoding="utf-8"))["verification_units"]
        self.assertEqual(written[0]["schema_version"], ru.LEGACY_SCHEMA)
        self.assertNotEqual(ru.LEGACY_SCHEMA, ru.SCHEMA_VERSION)
        self.assertEqual(written[-1]["schema_version"], ru.SCHEMA_VERSION)

    def test_the_migration_changes_nothing_else(self):
        """A migration that rewrote values would corrupt the audit trail it labels."""
        manifest = self.path("manifest.json")
        legacy = {"cycle": 0, "state": "CONTINUE", "weighted_total": 9,
                  "by_unit": {"U_grade": 4.0}, "outcome": "baseline"}
        manifest.write_text(json.dumps({"verification_units": [dict(legacy)]}),
                            encoding="utf-8")
        self.run_module(ru, "review_units.py", self.write(self.units(), "u.json"),
                        "--manifest", manifest)
        written = json.loads(manifest.read_text(encoding="utf-8"))["verification_units"][0]
        self.assertEqual({k: v for k, v in written.items() if k != "schema_version"},
                         legacy)


if __name__ == "__main__":
    unittest.main()
