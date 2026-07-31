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

    def test_a_blank_target_is_a_violation_not_malformed_input(self):
        """A blank target names nothing, which is what omitting it does.

        Rejecting it during parsing fired on EVERY result, including a heuristic
        one whose target is never read — so a rapid review carrying a leftover
        empty string went from a clean profile to exit 2 and no output at all.
        It belongs to the check that consults the field: exit 1, with the artifact
        and every other diagnostic still printed.
        """
        code, out, err = self.run_gp(self.profile(appraised_result="   "), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("'appraised_result' is required", out)
        self.assertIn("present but blank", out)
        self.assertIn("Evidence profile", out)

    def test_a_blank_target_is_ignored_on_a_heuristic_result(self):
        """The field is only read when the basis is confirmed_rob, so a leftover
        blank on a heuristic result is not a failure at all."""
        rec = self.profile(appraised_result="")
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = "Single-reviewer screening, disclosed."
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_module(gp, "grade_profile.py",
                                         self.write(rec, "rec.json"), "--strict")
        self.assertEqual(code, 0, msg=out + err)


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
        self.assertIn("cannot read", err)
        self.assertNotIn("manifest error", err)

    def test_review_units_still_names_the_manifest_when_it_is_the_manifest(self):
        """The first fix swapped which file got mislabelled: catching the decode
        error across the whole block reported an undecodable MANIFEST as an
        unreadable input. The read now has its own handler, wrapping only the read.
        """
        manifest = self.path("bad-manifest.json")
        manifest.write_bytes(b"\xff\xfe not utf-8")
        code, out, err = self.run_module(
            ru, "review_units.py",
            self.write(json.loads(
                fixture("units.systematic-clean.json").read_text(encoding="utf-8")),
                "u.json"),
            "--manifest", manifest)
        self.assertEqual(code, 2)
        self.assertIn("manifest error", err)
        self.assertNotIn("cannot read", err)


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

    def test_a_legacy_record_is_still_a_valid_floor_guard_baseline(self):
        """The field is a LABEL, and the floor guard deliberately ignores it.

        Skipping unversioned records when establishing the anti-gaming baseline
        would let a denominator drop across the version boundary go unflagged —
        weakening the guard to gain nothing, since the unit redefinition never
        touched denominators. Pinned because the opposite is the obvious-looking
        change for someone who reads the field and assumes it must be consumed.
        """
        manifest = self.path("manifest.json")
        manifest.write_text(json.dumps({"verification_units": [
            {"cycle": 0, "state": "CONTINUE", "weighted_total": 9,
             "by_unit": {"U_grade": 4.0}, "floor_guard": "ok",
             "denominators": {"citations": 40}},
        ]}), encoding="utf-8")
        dropped = self.units()
        dropped["denominators"] = {"citations": 38}
        dropped.pop("exclusions_logged", None)
        self.run_module(ru, "review_units.py", self.write(dropped, "u.json"),
                        "--manifest", manifest)
        written = json.loads(manifest.read_text(encoding="utf-8"))["verification_units"]
        self.assertEqual(written[0]["schema_version"], ru.LEGACY_SCHEMA)
        self.assertTrue(written[-1]["floor_guard"].startswith("UNLOGGED"),
                        msg=written[-1]["floor_guard"])
        self.assertIn("citations 40->38", written[-1]["floor_guard"])

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


class TestTheAppraisalRecordIsJudgedAsARecord(_Base):
    """Reporting violations only for CITED appraisals produced an incoherent split.

    A misspelled domain name in an appraisal no result cites killed the run at
    exit 2, while a MISSING domain in that same appraisal was accepted silently and
    a clean profile printed. Same entry, same file, opposite verdicts — and the
    differential test could not see it, because its profile cites every appraised
    study by construction.
    """

    def record_with_an_uncited_appraisal(self, **over):
        rec = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        extra = json.loads(json.dumps(rec["studies"][0]))
        extra["id"] = "P9"                       # cited by no result in the profile
        extra.update(over)
        rec["studies"].append(extra)
        return rec

    def run_with(self, rob):
        return self.run_module(
            gp, "grade_profile.py", fixture("grade-profile.valid.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")

    def test_an_uncited_appraisal_missing_a_domain_is_reported(self):
        rob = self.record_with_an_uncited_appraisal(
            domains={"randomization": "low", "deviations": "low"})
        code, out, err = self.run_with(rob)
        self.assertEqual(code, 1, msg=err)
        self.assertIn("appraisal record: study P9", out)
        self.assertIn("which are absent", out)
        self.assertNotIn("✅", out)

    def test_an_uncited_appraisal_with_an_incoherent_overall_is_reported(self):
        rob = self.record_with_an_uncited_appraisal(
            domains={"randomization": "high", "deviations": "low", "missing_data": "low",
                     "measurement": "low", "selection_of_result": "low"},
            overall="low")
        code, out, err = self.run_with(rob)
        self.assertEqual(code, 1, msg=err)
        self.assertIn("more favourable than its worst domain", out)

    def test_a_broken_appraisal_behind_a_heuristic_result_is_reported(self):
        """The other flavour: the citing result's basis is heuristic, so
        traceability never runs and the appraisal went unjudged."""
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        rob["studies"][0]["domains"]["randomization"] = "high"
        rob["studies"][0]["overall"] = "low"
        rec = self.profile()
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = "Single-reviewer screening, disclosed."
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("more favourable than its worst domain", out)

    def test_a_cited_appraisal_is_reported_once(self):
        """The record-level sweep must not repeat what a result already said."""
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        rob["studies"][0]["domains"]["randomization"] = "high"
        rob["studies"][0]["overall"] = "low"
        code, out, err = self.run_with(rob)
        self.assertEqual(code, 1, msg=err)
        self.assertEqual(out.count("more favourable than its worst domain"), 1, msg=out)
        self.assertIn("cannot back a 'confirmed_rob' basis", out)
        self.assertNotIn("appraisal record: study", out)

    def test_an_uncited_appraisal_awaiting_confirmation_is_not_a_failure(self):
        """The deliberate scope line: validity is checked for the whole record,
        human confirmation only where a rating relies on it. An appraisal awaiting
        sign-off for another result is rob_appraisal.py's H_rob to report."""
        rob = self.record_with_an_uncited_appraisal(confirmed_by="", confirmed_at="")
        code, out, err = self.run_with(rob)
        self.assertEqual(code, 0, msg=out + err)

    def test_a_clean_uncited_appraisal_stays_clean(self):
        code, out, err = self.run_with(self.record_with_an_uncited_appraisal())
        self.assertEqual(code, 0, msg=out + err)


class TestDiagnosticsCannotBeForged(_Base):
    """Both checks render violations as markdown list items, and both interpolated
    caller-controlled ids into them raw. A newline in an id split one violation
    into two, and the second was free to read as a finding of its own."""

    INJECTION = "P1\n- **INJECTED** — every study confirmed"

    def test_rob_appraisal_keeps_one_violation_on_one_line(self):
        rec = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        s = rec["studies"][0]
        s["id"] = self.INJECTION
        s["confirmed_by"] = s["confirmed_at"] = ""
        code, out, err = self.run_module(ra, "rob_appraisal.py",
                                         self.write(rec, "rob.json"), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("**INJECTED**", out)          # the text survives, escaped
        # …but never at the start of a line, which is what would make it a list
        # item or a table row of its own.
        for line in out.splitlines():
            self.assertFalse(line.startswith("- **INJECTED**"), msg=line)
            self.assertFalse(line.startswith("| **INJECTED**"), msg=line)

    def test_grade_profile_keeps_one_violation_on_one_line(self):
        rec = self.profile(id="O1\n- **INJECTED** — no issues found",
                           appraised_result="nonexistent target")
        code, out, err = self.run_gp(rec, "--strict")
        self.assertEqual(code, 1, msg=err)
        for line in out.splitlines():
            self.assertFalse(line.startswith("- **INJECTED**"), msg=line)

    def test_the_prisma_diagram_cannot_gain_a_node(self):
        """The flow diagram is the headline figure of a systematic review, and its
        labels are caller-supplied dictionary KEYS — validated nowhere, while every
        count beside them was validated rigorously."""
        counts = {"identified_databases_registers": 30, "duplicates_removed": 0,
                  "records_screened": 30, "records_excluded_title_abstract": 10,
                  "reports_sought": 20, "reports_not_retrieved": 0,
                  "reports_assessed": 20,
                  "reports_excluded": {'wrong population"] --> EVIL[injected': 20},
                  "studies_included_databases": 0, "studies_included_total": 0}
        _, out, _ = self.run_module(pf, "prisma_flow.py", self.write(counts, "c.json"))
        self.assertNotIn('"] --> EVIL[', out)
        self.assertIn("&quot;", out)

    def test_a_database_name_cannot_gain_a_node(self):
        counts = {"identified_databases": {'OpenAlex"] --> EVIL[injected': 30},
                  "duplicates_removed": 0, "records_screened": 30,
                  "records_excluded_title_abstract": 10, "reports_sought": 20,
                  "reports_not_retrieved": 0, "reports_assessed": 20,
                  "reports_excluded": {"wrong population": 20},
                  "studies_included_databases": 0, "studies_included_total": 0}
        _, out, _ = self.run_module(pf, "prisma_flow.py", self.write(counts, "c.json"))
        self.assertNotIn('"] --> EVIL[', out)


class TestEveryRecordedExceptionIsRendered(_Base):
    """The class behind four findings at once.

    A GRADE record may carry three things that make an otherwise-illegal state
    legal — a starting-level justification, upgrades, a risk-of-bias coherence
    override — and the check honoured all three while the artifact showed none of
    them. A reader saw a rating with no route to the reasoning that permitted it.
    """

    def upgraded(self):
        """A legal non-randomized body upgraded two levels: low + 2 = high."""
        rec = self.profile(
            design_mix={"rct": 0, "nrsi": 0, "observational": 4, "dta": 0,
                        "case_series": 0},
            starting_level="low", final="high",
            upgrades={"large_effect": 2},
            appraised_result="diagnostic accuracy at 12 months")
        for name in ("inconsistency", "indirectness", "imprecision", "publication_bias"):
            rec["results"][0]["domains"][name]["rating"] = 0
        return rec

    def test_upgrades_appear_in_the_row_and_the_notes(self):
        _, out, _ = self.run_gp(self.upgraded())
        self.assertIn("| Up | Final |", out)
        self.assertIn("| +2 |", out)
        self.assertIn("*upgrades*: large effect (+2)", out)

    def test_the_arithmetic_is_readable_from_the_row(self):
        """low(2) + 0 downgrades + 2 upgrades = high(4). Without the column the row
        showed low on the left and high on the right and nothing between them."""
        _, out, _ = self.run_gp(self.upgraded())
        row = next(ln for ln in out.splitlines() if ln.startswith("| O1 |"))
        self.assertIn("| low |", row)
        self.assertIn("| +2 |", row)
        self.assertIn("high", row)

    def test_a_coherence_override_is_rendered(self):
        rec = self.profile(appraised_result="diagnostic accuracy at 12 months")
        rec["results"][0]["domains"]["risk_of_bias"]["coherence_justification"] = (
            "Sensitivity analysis without the high-risk studies moved the estimate 2%.")
        _, out, _ = self.run_gp(rec)
        self.assertIn("coherence override", out)
        self.assertIn("moved the estimate 2%", out)

    def test_every_exception_field_reaches_the_artifact(self):
        """One assertion per exception the schema allows, so a NEW one cannot be
        added to the parser without also being rendered."""
        exceptions = {
            "starting_level_justification": "Recorded rationale AAA.",
            "coherence_justification": "Recorded rationale BBB.",
        }
        rec = self.profile(
            appraised_result="diagnostic accuracy at 12 months",
            starting_level_justification=exceptions["starting_level_justification"])
        rec["results"][0]["domains"]["risk_of_bias"]["coherence_justification"] = \
            exceptions["coherence_justification"]
        _, out, _ = self.run_gp(rec)
        for field, text in exceptions.items():
            with self.subTest(field=field):
                self.assertIn(text, out)


class TestTheDaggerMarksADeparture(_Base):
    """The marker means "this level needed an exception", not "a justification was
    recorded" — the contract says so, and marking on presence flagged conforming
    rows to the manuscript reader as anomalies."""

    def test_a_justification_on_a_conforming_level_is_not_marked(self):
        rec = self.profile(
            starting_level_justification="All four are RCTs, so 'high' is the default.",
            appraised_result="diagnostic accuracy at 12 months")
        code, out, err = self.run_gp(rec, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertNotIn("†", out)
        # The rationale is still shown — recorded content is never hidden, it is
        # simply not presented as an exception.
        self.assertIn("All four are RCTs", out)

    def test_a_departure_is_marked(self):
        rec = self.profile(
            design_mix={"rct": 0, "nrsi": 0, "observational": 4, "dta": 0,
                        "case_series": 0},
            starting_level="high", final="moderate",
            starting_level_justification="Population-based with complete follow-up.")
        _, out, _ = self.run_gp(rec)
        self.assertIn("| high † |", out)
        self.assertIn("† *starting level*", out)


class TestConfirmationAuthenticityIsDisclosed(_Base):
    """FR-015 — wherever human confirmation is CHECKED, say what the check means.

    With --rob this command reads confirmed_by/confirmed_at and lets them back a
    certainty rating, so it checks confirmation and owed the reader the limitation
    rob_appraisal.py already prints.
    """

    def test_the_limitation_is_printed_with_rob(self):
        code, out, err = self.run_gp(
            self.profile(appraised_result="diagnostic accuracy at 12 months"), "--strict")
        self.assertEqual(code, 0, msg=err)
        self.assertIn("cannot establish that a human made the judgment", out)

    def test_it_matches_the_sibling_checks_claim(self):
        _, gp_out, _ = self.run_gp(
            self.profile(appraised_result="diagnostic accuracy at 12 months"))
        _, ra_out, _ = self.run_module(ra, "rob_appraisal.py",
                                       fixture("risk-of-bias.valid.json"))
        for claim in ("cannot establish that a human made the judgment",
                      "who that person was"):
            with self.subTest(claim=claim):
                self.assertIn(claim, gp_out)
                self.assertIn(claim, ra_out)

    def test_it_is_absent_when_no_confirmation_was_checked(self):
        """Without --rob nothing here reads a confirmation record, and a limitation
        about a check that did not run is noise the reader has to discount."""
        rec = self.profile()
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = "Single-reviewer screening, disclosed."
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_module(gp, "grade_profile.py",
                                         self.write(rec, "rec.json"), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertNotIn("cannot establish that a human", out)


if __name__ == "__main__":
    unittest.main()
