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

    # Instrument and a clean domain set per design, so a test can build a --rob
    # record whose DESIGNS match the design_mix under test. Without it the
    # distribution reconcile fires first and the test measures the wrong rule.
    INSTRUMENTS = {
        "rct": ("rob2", {"randomization": "low", "deviations": "low",
                         "missing_data": "low", "measurement": "low",
                         "selection_of_result": "low"}),
        "nrsi": ("robins_i", {"confounding": "low", "participant_selection": "low",
                              "intervention_classification": "low",
                              "deviations": "low", "missing_data": "low",
                              "outcome_measurement": "low",
                              "selection_of_result": "low"}),
        "observational": ("nos", {"selection": 4, "comparability": 2,
                                  "outcome_or_exposure": 3}),
        "dta": ("quadas2", {
            "patient_selection": {"risk_of_bias": "low", "applicability": "low"},
            "index_test": {"risk_of_bias": "low", "applicability": "low"},
            "reference_standard": {"risk_of_bias": "low", "applicability": "low"},
            "flow_and_timing": {"risk_of_bias": "low"}}),
    }

    def rob_for(self, design, study_ids=("P1", "P3", "P5", "P7")):
        instrument, domains = self.INSTRUMENTS[design]
        return {"schema_version": "1.0", "studies": [
            {"id": sid, "design": design, "instrument": instrument,
             "domains": json.loads(json.dumps(domains)), "overall": "low",
             "result_assessed": TARGET,
             "confirmed_by": "K. Valcorza", "confirmed_at": "2026-07-26"}
            for sid in study_ids]}

    def run_gp_matching(self, rec, design, *args):
        return self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", self.write(self.rob_for(design), "rob.json"), *args)

    def body(self, design, start, **over):
        """A result of one design at a declared starting level, carrying a +2."""
        rec = self.profile(
            design_mix={d: (4 if d == design else 0) for d in gp.DESIGNS},
            starting_level=start,
            upgrades={"large_effect": 2, "dose_response": 0, "opposing_confounding": 0},
            **over)
        for name in gp.DOMAINS:
            rec["results"][0]["domains"][name]["rating"] = 0
        rec["results"][0]["final"] = gp.LEVEL_NAMES[
            max(1, min(4, gp.LEVELS[start] + 2))]
        return rec


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

    def test_an_invalid_appraisal_does_not_also_drive_the_coherence_rule(self):
        """Pins the filter that keeps invalid appraisals out of the Rule 12 comparison.

        Removing it left the suite green, even though it decides whether an
        appraisal its own instrument rejects can trigger — or suppress — a
        body-level coherence contradiction. Reporting a judgment DERIVED from an
        appraisal that is not valid tells the reviewer to fix a second thing that
        will disappear when they fix the first.
        """
        rob = json.loads(
            fixture("risk-of-bias.mostly-high.json").read_text(encoding="utf-8"))
        rec = json.loads(
            fixture("grade-profile.incoherent-rob.json").read_text(encoding="utf-8"))
        # Baseline: valid appraisals, so the coherence rule is what fires.
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("coherence_justification", out)

        # Now make every appraisal invalid. The violation is reported; the derived
        # coherence contradiction is not.
        for s in rob["studies"]:
            s["domains"].pop(sorted(s["domains"])[0])
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec2.json"),
            "--rob", self.write(rob, "rob2.json"), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("which are absent", out)
        self.assertNotIn("record a coherence_justification", out)


class TestOneMissingDomainConcealsNothing(_Base):
    """The rules that do not need a full domain set must still run.

    Stopping at the first missing domain hid every later violation, so the reviewer
    fixed one thing, re-ran, and met the next — staged discovery of work that was
    knowable on the first pass. The contract now claims this; nothing asserted it,
    and re-inserting the `continue` left the whole suite green.
    """

    def broken_result(self):
        rec = self.profile(
            design_mix={"rct": 0, "nrsi": 0, "observational": 4, "dta": 0,
                        "case_series": 0},
            starting_level="high", final="moderate")   # departs, unjustified
        del rec["results"][0]["domains"]["publication_bias"]
        return rec

    def test_a_missing_domain_does_not_hide_the_starting_level_rule(self):
        code, out, err = self.run_gp(self.broken_result(), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("missing downgrade domain(s) publication_bias", out)
        self.assertIn("does not match the predominant design", out)

    def test_a_missing_domain_does_not_hide_the_basis_rule(self):
        rec = self.broken_result()
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_gp(rec, "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("missing downgrade domain(s)", out)
        self.assertIn("requires confirmed appraisal", out)

    def test_a_missing_domain_does_not_hide_traceability(self):
        rec = self.broken_result()
        rec["results"][0]["appraised_result"] = "a target nothing appraises"
        code, out, err = self.run_gp(rec, "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("missing downgrade domain(s)", out)
        self.assertIn("does not appear in the appraisal record", out)

    def test_an_unresolved_downgrade_still_blocks_an_upgrade(self):
        """Decidable from the domains present: a recorded -1 is unresolved whether
        or not some other domain was ever written down."""
        rec = self.broken_result()
        rec["results"][0]["starting_level"] = "low"
        rec["results"][0]["domains"]["inconsistency"]["rating"] = -1
        rec["results"][0]["upgrades"] = {"large_effect": 2, "dose_response": 0,
                                         "opposing_confounding": 0}
        code, out, err = self.run_gp(rec, "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("upgrades applied while downgrade(s) remain", out)

    def test_the_arithmetic_alone_waits_for_a_full_domain_set(self):
        """The one rule that genuinely cannot be decided over a partial domain set.

        The fixture must be one whose PARTIAL sum does not reconcile, or the test
        cannot see the guard at all: the first version used a record that added up
        either way, so removing `if not missing` left it — and the whole suite —
        green while the check reported a sum the record never claimed.
        """
        rec = self.profile(starting_level="low", final="very_low")
        for name in gp.DOMAINS:
            rec["results"][0]["domains"][name]["rating"] = 0
        # The absent domain is the one carrying the downgrade, so low(2) -1 =
        # very_low(1) reconciles over the full set and low(2) +0 does not.
        rec["results"][0]["domains"]["publication_bias"]["rating"] = -1
        del rec["results"][0]["domains"]["publication_bias"]
        code, out, err = self.run_gp(rec, "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("missing downgrade domain(s) publication_bias", out)
        self.assertNotIn("difference of", out)


class TestUpgradeLegalityHasTwoBars(_Base):
    """Rating up is barred by the DESIGN and, separately, by the DECLARED level.

    Three versions of this rule each enforced one bar and dropped the other, and
    the third — testing the declared level alone — was the worst, because Rule 4
    tells the reviewer to add the very justification that unlocks it:

        step 1, no justification:  exit 1, "starting_level 'low' does not match
                                   the predominant design 'rct' … record a
                                   starting_level_justification"
        step 2, justification added, nothing else changed:  exit 0, high ⊕⊕⊕⊕

    A randomized body rated down for study limitations and then raised back to
    high on large-effect is the most consequential fail-open this check exists to
    prevent. Both bars are asserted here, in both directions.
    """

    def test_a_randomized_body_may_not_upgrade_however_it_is_declared(self):
        for start in ("very_low", "low", "moderate", "high"):
            with self.subTest(starting_level=start):
                rec = self.body("rct", start, appraised_result=TARGET,
                                starting_level_justification="Downgraded for attrition.")
                code, out, err = self.run_gp_matching(rec, "rct", "--strict")
                self.assertEqual(code, 1, msg=out + err)
                self.assertIn("reserves rating up for non-randomized evidence", out)

    def test_a_diagnostic_accuracy_body_may_not_upgrade_however_it_is_declared(self):
        for start in ("low", "high"):
            with self.subTest(starting_level=start):
                rec = self.body("dta", start, appraised_result=TARGET,
                                starting_level_justification="Index test applied "
                                                             "outside its population.")
                code, out, err = self.run_gp_matching(rec, "dta", "--strict")
                self.assertEqual(code, 1, msg=out + err)
                self.assertIn("reserves rating up for non-randomized evidence", out)

    def test_the_design_bar_is_not_reachable_by_adding_a_justification(self):
        """The staged trap, walked end to end."""
        rec = self.body("rct", "low", appraised_result=TARGET)
        code, out, _ = self.run_gp_matching(rec, "rct", "--strict")
        self.assertEqual(code, 1)
        self.assertIn("does not match the predominant design", out)

        rec["results"][0]["starting_level_justification"] = "Downgraded for attrition."
        code, out, _ = self.run_gp_matching(rec, "rct", "--strict")
        self.assertEqual(code, 1, msg=out)      # NOT unlocked by the justification
        self.assertIn("reserves rating up for non-randomized evidence", out)


class TestUpgradeLegalityUsesTheDeclaredStart(_Base):
    """The second bar: nothing rates above high, whatever the design implies."""

    def test_an_observational_body_justified_up_to_high_may_not_upgrade(self):
        """Keying on the DESIGN's implied start alone, a body justified up to high
        took +2 and had it absorbed by the ceiling — recorded, illegal, invisible."""
        rec = self.body("observational", "high",
                        appraised_result=TARGET,
                        starting_level_justification="Population-based, complete follow-up.")
        code, out, err = self.run_gp_matching(rec, "observational", "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("already declaring a starting level of 'high'", out)

    def test_an_observational_body_starting_low_may_still_upgrade(self):
        """The legitimate case both bars must leave alone — otherwise the rule stops
        modelling GRADE and starts forbidding rating up altogether."""
        rec = self.body("observational", "low", appraised_result=TARGET)
        code, out, err = self.run_gp_matching(rec, "observational", "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_the_message_names_which_bar_bit(self):
        """A reviewer told "upgrades are not permitted" cannot tell whether to
        change the design mix, the starting level, or the upgrade itself."""
        _, design_bar, _ = self.run_gp_matching(
            self.body("rct", "high", appraised_result=TARGET), "rct")
        self.assertIn("body of rct studies", design_bar)
        _, level_bar, _ = self.run_gp_matching(
            self.body("observational", "high", appraised_result=TARGET,
                      starting_level_justification="Population-based."),
            "observational")
        self.assertIn("already declaring a starting level of 'high'", level_bar)


class TestTheUnitCountIsEmittedNotCounted(_Base):
    """`U_grade` is the number of failing RESULTS, and the loop is told to read this
    line rather than count diagnostics. Only a zero was ever pinned — where the two
    definitions coincide — so replacing the count with `len(errs)` stayed green."""

    def two_broken_results(self):
        rec = self.profile(
            design_mix={"rct": 0, "nrsi": 0, "observational": 4, "dta": 0,
                        "case_series": 0},
            starting_level="high", final="high",
            upgrades={"large_effect": 2, "dose_response": 0, "opposing_confounding": 0})
        rec["results"][0]["domains"]["inconsistency"]["rating"] = -1
        second = json.loads(json.dumps(rec["results"][0]))
        second["id"] = "O2"
        rec["results"].append(second)
        return rec

    def test_one_result_with_several_violations_counts_once(self):
        rec = self.two_broken_results()
        del rec["results"][1]
        code, out, err = self.run_gp(rec, "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertGreater(out.count("\n- result O1:"), 1, msg=out)   # several messages
        self.assertIn("**U_grade: 1** result(s)", out)                 # one result

    def test_two_broken_results_count_twice_and_are_named(self):
        code, out, err = self.run_gp(self.two_broken_results(), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("**U_grade: 2** result(s)", out)
        self.assertIn("(O1, O2)", out)

    def test_a_clean_record_reports_zero(self):
        code, out, err = self.run_gp(
            self.profile(appraised_result="diagnostic accuracy at 12 months"), "--strict")
        self.assertEqual(code, 0, msg=err)
        self.assertIn("**U_grade: 0** result(s)", out)

    def test_record_level_violations_are_excluded_and_said_to_be(self):
        """They belong to the --rob record, not to a certainty result, so counting
        them into U_grade would book work against a result that has none."""
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        extra = json.loads(json.dumps(rob["studies"][0]))
        extra["id"] = "P9"
        extra["domains"] = {"randomization": "low"}
        rob["studies"].append(extra)
        code, out, err = self.run_module(
            gp, "grade_profile.py",
            self.write(self.profile(appraised_result="diagnostic accuracy at 12 months"),
                       "rec.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("**U_grade: 0** result(s)", out)
        self.assertIn("belong to the appraisal record", out)


class TestTheArtifactMarkers(_Base):
    """Both markers were introduced with prose in the contract and no assertion."""

    def clamped(self):
        rec = self.profile(
            design_mix={"rct": 0, "nrsi": 0, "observational": 4, "dta": 0,
                        "case_series": 0},
            starting_level="low", final="very_low")
        for name in gp.DOMAINS:
            rec["results"][0]["domains"][name]["rating"] = 0
        rec["results"][0]["domains"]["inconsistency"]["rating"] = -2
        rec["results"][0]["domains"]["indirectness"]["rating"] = -2
        rec["results"][0]["appraised_result"] = TARGET
        return rec

    def test_a_clamped_sum_is_marked_and_explained(self):
        code, out, err = self.run_gp_matching(self.clamped(), "observational", "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("⌁", out)
        self.assertIn("certainty bound", out)
        self.assertIn("held at very_low(1)", out)

    def test_an_unclamped_sum_is_not_marked(self):
        _, out, _ = self.run_gp(
            self.profile(appraised_result="diagnostic accuracy at 12 months"))
        self.assertNotIn("⌁", out)

    def test_an_unjustified_departure_carries_no_dagger(self):
        """The marker points at a footnote. Marking a departure with no justification
        promised the reader an explanation the record never wrote."""
        rec = self.profile(
            design_mix={"rct": 0, "nrsi": 0, "observational": 4, "dta": 0,
                        "case_series": 0},
            starting_level="high", final="moderate")
        code, out, _ = self.run_gp(rec, "--strict")
        self.assertEqual(code, 1)                      # reported as a violation
        self.assertNotIn("†", out)


class TestExceptionsAreNotShownWhereTheyDoNotApply(_Base):
    """Rendering an exception that licenses nothing credits the record with an
    allowance it never had — the same overclaim as hiding one, inverted."""

    def test_a_disclosure_is_not_shown_for_a_systematic_review(self):
        rec = self.profile()
        rec["streamlined_method_disclosed"] = "SHORTCUT TEXT"
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_module(gp, "grade_profile.py",
                                         self.write(rec, "rec.json"), "--strict")
        self.assertEqual(code, 1, msg=err)             # nothing licenses it here
        self.assertIn("requires confirmed appraisal", out)
        self.assertNotIn("SHORTCUT TEXT", out)

    def test_a_disclosure_is_shown_for_a_rapid_review(self):
        rec = self.profile()
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = "SHORTCUT TEXT"
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_module(gp, "grade_profile.py",
                                         self.write(rec, "rec.json"), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("SHORTCUT TEXT", out)

    def test_appraisal_overrides_are_not_shown_under_a_heuristic_basis(self):
        """A heuristic basis rests on no appraisal, so listing human-signed
        overrides beneath a PROVISIONAL banner credits it with backing it lacks."""
        rec = self.profile(appraised_result="diagnostic accuracy at 12 months")
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = "Single-reviewer screening."
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        for s in rob["studies"]:
            s["overall_justification"] = "OVERRIDE TEXT"
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertNotIn("OVERRIDE TEXT", out)

    def test_a_load_bearing_override_is_shown_even_under_a_heuristic_basis(self):
        """The inverse failure, created by the fix above.

        An `overall_justification` that suppresses a real method violation is what
        makes the SUPPLIED RECORD legal. Gating its rendering on a rating resting on
        it meant the run exited 0 while the human sign-off holding it clean appeared
        on no page — and deleting that same justification exited 1. The artifact was
        hiding precisely the thing keeping it green.
        """
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        rob["studies"][0]["domains"]["measurement"] = "high"      # now incoherent…
        rob["studies"][0]["overall"] = "low"
        rob["studies"][0]["overall_justification"] = "LOAD BEARING OVERRIDE"  # …suppressed
        rec = self.profile(appraised_result=TARGET)
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = "Single-reviewer screening."
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("LOAD BEARING OVERRIDE", out)
        self.assertIn("suppressed a method violation", out)

    def test_deleting_that_override_reports_the_violation_it_suppressed(self):
        """The other half of the pair: what the override is holding back."""
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        rob["studies"][0]["domains"]["measurement"] = "high"
        rob["studies"][0]["overall"] = "low"
        rec = self.profile(appraised_result=TARGET)
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = "Single-reviewer screening."
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("more favourable than its worst domain", out)

    def test_an_inert_override_is_not_advertised(self):
        """An override on an already-valid appraisal suppresses nothing, so listing
        it would credit the record with an exception it never needed."""
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        for s in rob["studies"]:
            s["overall_justification"] = "INERT OVERRIDE"
        rec = self.profile(appraised_result=TARGET)
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = "Single-reviewer screening."
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertNotIn("INERT OVERRIDE", out)

    def test_a_disclosure_survives_where_the_heuristic_basis_is_legal(self):
        """Scoping and narrative reviews may use a heuristic basis, so gating the
        disclosure on `rapid` dropped it from a PASSING artifact — two records
        differing in a recorded shortcut rendered byte-identically."""
        for rtype in ("scoping", "narrative", "rapid"):
            with self.subTest(review_type=rtype):
                rec = self.profile()
                rec["review_type"] = rtype
                rec["streamlined_method_disclosed"] = "DISCLOSED SHORTCUT"
                rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
                code, out, err = self.run_module(
                    gp, "grade_profile.py", self.write(rec, "rec.json"), "--strict")
                self.assertEqual(code, 0, msg=out + err)
                self.assertIn("DISCLOSED SHORTCUT", out)

    def test_appraisal_overrides_are_shown_under_a_confirmed_basis(self):
        rec = self.profile(appraised_result="diagnostic accuracy at 12 months")
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        for s in rob["studies"]:
            s["overall_justification"] = "OVERRIDE TEXT"
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", self.write(rob, "rob.json"), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("OVERRIDE TEXT", out)


class TestAHumanGateIsNotAutoReducibleWork(_Base):
    """The loop's core promise: clear everything mechanical, then HAND OFF.

    Three documents say a matching but unconfirmed appraisal belongs exclusively to
    `H_rob`. `U_rob_trace` implemented that; `U_grade` did not — so a review whose
    only outstanding item was a signature booked a unit of auto-reducible work,
    never reached `auto_units_zero`, and reported PLATEAU instead of
    BLOCKED_ON_HUMAN while the routing table sent the agent back to this check to
    repair something only a person can clear.
    """

    def test_an_unconfirmed_appraisal_is_reported_but_not_counted(self):
        """Still a violation — the rating is not yet backed — but not a UNIT.

        The exit code and the unit count answer different questions. Exit 1 says
        this record is not finished; `U_grade` says how much of what remains the
        loop can repair on its own. A missing signature is none of it.
        """
        code, out, err = self.run_module(
            gp, "grade_profile.py", fixture("grade-profile.valid.json"),
            "--rob", fixture("risk-of-bias.unconfirmed.json"), "--strict")
        self.assertEqual(code, 1, msg=err)                   # not finished
        self.assertIn("have no human confirmation", out)     # still reported
        self.assertIn("HUMAN GATE (H_rob)", out)             # and named as a gate
        self.assertIn("**U_grade: 0**", out)                 # not booked as work

    def test_a_real_defect_alongside_it_is_still_counted(self):
        """The exclusion must not swallow the result whenever a gate is pending."""
        rec = self.profile(appraised_result=TARGET, final="high")   # arithmetic wrong
        code, out, err = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"),
            "--rob", fixture("risk-of-bias.unconfirmed.json"), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("have no human confirmation", out)
        self.assertIn("**U_grade: 1**", out)

    def test_the_loop_then_reaches_the_handoff_state(self):
        """End to end: the count this check emits, fed to the backend that routes on it."""
        units = {"schema_version": "1.0", "review_type": "systematic", "cycle": 4,
                 "units": {"U_cite_external": 0, "U_cite_internal": 0, "U_screen": 0,
                           "U_extract": 0, "U_prisma": 0, "U_grade": 0,
                           "U_rob_trace": 0, "U_checklist": 0},
                 "units_in_scope": ["U_screen", "U_prisma", "U_grade", "U_rob_trace",
                                    "U_checklist", "U_extract"],
                 "consistency": {"score": 90, "critical_breaks": 0},
                 "gates": {"H_rob": 1, "H_screen_adj": 0, "H_cite_manual": 0,
                           "H_numeric": 0},
                 "history": [1, 1, 1]}
        code, out, err = self.run_module(ru, "review_units.py",
                                         self.write(units, "units.json"))
        self.assertEqual(code, 1, msg=err)
        verdict = json.loads(out)
        self.assertEqual(verdict["state"], "BLOCKED_ON_HUMAN")
        self.assertTrue(verdict["auto_units_zero"])
        self.assertEqual(verdict["gates_remaining"], 1)

    def test_and_would_have_plateaued_on_the_old_count(self):
        """The same record with U_grade booked at 1, which is what the check used to
        emit — the state the loop actually reached."""
        units = {"schema_version": "1.0", "review_type": "systematic", "cycle": 4,
                 "units": {"U_cite_external": 0, "U_cite_internal": 0, "U_screen": 0,
                           "U_extract": 0, "U_prisma": 0, "U_grade": 1,
                           "U_rob_trace": 0, "U_checklist": 0},
                 "units_in_scope": ["U_screen", "U_prisma", "U_grade", "U_rob_trace",
                                    "U_checklist", "U_extract"],
                 "consistency": {"score": 90, "critical_breaks": 0},
                 "gates": {"H_rob": 1, "H_screen_adj": 0, "H_cite_manual": 0,
                           "H_numeric": 0},
                 "history": [1, 1, 1]}
        _, out, _ = self.run_module(ru, "review_units.py",
                                    self.write(units, "units.json"))
        self.assertEqual(json.loads(out)["state"], "PLATEAU")


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
        counts = {"schema_version": "1.0", "duplicates_removed": 0,
                  "records_screened": 30, "records_excluded_title_abstract": 10,
                  "reports_sought": 20, "reports_not_retrieved": 0,
                  "reports_assessed": 20,
                  "reports_excluded": {'wrong population"] --> EVIL[injected': 20},
                  "studies_included_databases": 0, "studies_included_total": 0}
        _, out, _ = self.run_module(pf, "prisma_flow.py", self.write(counts, "c.json"))
        self.assertNotIn('"] --> EVIL[', out)
        self.assertIn("&quot;", out)

    def test_a_database_name_cannot_gain_a_node(self):
        counts = {"schema_version": "1.0",
                  "identified_databases": {'OpenAlex"] --> EVIL[injected': 30},
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

    # Every field in the schema whose PURPOSE is to make an otherwise-illegal state
    # legal, with how to place it in a record. Derived from the parser's own key
    # sets by the test below, so a new one cannot be added without either being
    # rendered or failing here — the previous version hardcoded two of these and
    # was already missing the other two while claiming to be exhaustive.
    EXCEPTION_FIELDS = {
        "starting_level_justification": "RECORDED RATIONALE AAA",
        "coherence_justification": "RECORDED RATIONALE BBB",
        "streamlined_method_disclosed": "RECORDED RATIONALE CCC",
        "overall_justification": "RECORDED RATIONALE DDD",
    }

    def record_using_every_exception(self):
        """A rapid review that needs all four at once."""
        rec = self.profile(
            appraised_result="diagnostic accuracy at 12 months",
            design_mix={"rct": 0, "nrsi": 0, "observational": 4, "dta": 0,
                        "case_series": 0},
            starting_level="high", final="moderate",
            starting_level_justification=self.EXCEPTION_FIELDS[
                "starting_level_justification"])
        rec["review_type"] = "rapid"
        rec["streamlined_method_disclosed"] = self.EXCEPTION_FIELDS[
            "streamlined_method_disclosed"]
        rob_domain = rec["results"][0]["domains"]["risk_of_bias"]
        rob_domain["basis"] = "heuristic"
        rob_domain["coherence_justification"] = self.EXCEPTION_FIELDS[
            "coherence_justification"]
        rob = json.loads(fixture("risk-of-bias.valid.json").read_text(encoding="utf-8"))
        for s in rob["studies"]:
            s["overall_justification"] = self.EXCEPTION_FIELDS["overall_justification"]
        return rec, rob

    def test_every_exception_field_reaches_the_artifact(self):
        rec, rob = self.record_using_every_exception()
        # The appraisal override is only visible where a rating rests on it, so
        # render the confirmed-basis variant for that one.
        _, heuristic_out, _ = self.run_module(
            gp, "grade_profile.py", self.write(rec, "rec.json"))
        confirmed = json.loads(json.dumps(rec))
        confirmed["results"][0]["domains"]["risk_of_bias"]["basis"] = "confirmed_rob"
        _, confirmed_out, _ = self.run_module(
            gp, "grade_profile.py", self.write(confirmed, "rec2.json"),
            "--rob", self.write(rob, "rob.json"))
        combined = heuristic_out + confirmed_out
        for field, text in self.EXCEPTION_FIELDS.items():
            with self.subTest(field=field):
                self.assertIn(text, combined,
                              msg=f"{field} is honoured by the check and invisible "
                                  f"in the artifact")

    # The parser's complete key sets. Pinned, so that ADDING ANY FIELD fails this
    # test until someone answers the question that matters — does it make an
    # otherwise-illegal state legal? A previous version derived the exception list
    # by matching name suffixes, which asks "is it spelled like an exception?" and
    # so missed a live `starting_level_waiver` entirely. Names are not purposes; a
    # frozen schema forces the classification instead of guessing it.
    SCHEMA_KEYS = {
        "RECORD_KEYS": {"schema_version", "review_type", "synthesis_mode",
                        "streamlined_method_disclosed", "results"},
        "RESULT_KEYS": {"id", "label", "study_ids", "design_mix", "starting_level",
                        "starting_level_justification", "domains", "upgrades",
                        "final", "certainty_statement", "appraised_result"},
        "DOMAIN_KEYS": {"rating", "note", "basis", "coherence_justification"},
        "APPRAISAL_STUDY_KEYS": {"id", "design", "instrument", "result_assessed",
                                 "domains", "evidence", "overall",
                                 "overall_justification", "confirmed_by",
                                 "confirmed_at"},
    }

    def test_the_schema_has_not_gained_a_field_without_classifying_it(self):
        """Adding a field must force a decision, not slip past a naming convention.

        If this fails because you added a field: decide whether it can make an
        otherwise-illegal state legal. If it can, add it to EXCEPTION_FIELDS and
        render it in the artifact — an exception the record needs in order to be
        legal must be visible to the reader. If it cannot, add it here and say so.
        """
        for name, expected in self.SCHEMA_KEYS.items():
            with self.subTest(key_set=name):
                self.assertEqual(getattr(gp, name), expected)

    def test_every_pinned_exception_is_a_real_schema_field(self):
        """The other direction: an EXCEPTION_FIELDS entry the parser does not accept
        would be rendered-and-tested vapour."""
        known = set().union(*self.SCHEMA_KEYS.values())
        for field in self.EXCEPTION_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, known)


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

    def test_a_confirmed_basis_without_rob_still_omits_it(self):
        """Pins the --rob guard SEPARATELY from the confirmed-basis one.

        The test above uses a record that satisfies both guards at once, so either
        one alone would carry it — deleting the --rob check left the whole suite
        green. Here the basis IS confirmed_rob and no appraisal record is supplied:
        nothing read a confirmation, so nothing may be said about one.
        """
        code, out, err = self.run_module(
            gp, "grade_profile.py",
            self.write(self.profile(appraised_result="diagnostic accuracy at 12 months"),
                       "rec.json"), "--strict")
        self.assertEqual(code, 1, msg=err)          # the claim is not taken on trust
        self.assertIn("no appraisal record was supplied", out)
        self.assertNotIn("cannot establish that a human", out)


if __name__ == "__main__":
    unittest.main()
