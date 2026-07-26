"""Regressions for the two findings from round 4 of review on PR #3.

One is the round-3 class again: grade_profile.py accepting an appraisal that
rob_appraisal.py rejects. The other is a CRASH my round-3 fix introduced.

The crash exposed a modelling gap that predates this PR: the two design
taxonomies never matched.

    GRADE design_mix : rct, nrsi, observational,      case_series
    appraisal designs: rct, nrsi, observational, dta

`dta` had no GRADE category (KeyError on the verdict path) and `case_series` has
no risk-of-bias instrument (so it can never appear in an appraisal record).

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

ROB2 = {"randomization": "low", "deviations": "low", "missing_data": "low",
        "measurement": "low", "selection_of_result": "low"}
QUADAS = {"patient_selection": {"risk_of_bias": "low", "applicability": "low"},
          "index_test": {"risk_of_bias": "low", "applicability": "low"},
          "reference_standard": {"risk_of_bias": "low", "applicability": "low"},
          "flow_and_timing": {"risk_of_bias": "low"}}
NOS = {"selection": 4, "comparability": 2, "outcome_or_exposure": 3}


class _Base(unittest.TestCase):
    def write(self, rec, name="rec.json"):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / name
        p.write_text(json.dumps(rec), encoding="utf-8")
        return p

    def run_gp(self, rec, rob=None, *args):
        argv = ["gp.py", str(self.write(rec))]
        if rob is not None:
            argv += ["--rob", str(self.write(rob, "rob.json"))]
        argv += list(args)
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", argv), redirect_stdout(out), redirect_stderr(err):
            code = gp.main()
        return code, out.getvalue(), err.getvalue()

    def run_ra(self, rob, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv",
                               ["ra.py", str(self.write(rob, "r.json")), *args]), \
                redirect_stdout(out), redirect_stderr(err):
            code = ra.main()
        return code, out.getvalue(), err.getvalue()

    def profile(self, **over):
        rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
        rec["results"][0].update(over)
        return rec


def appraisal(design, instrument, domains, overall="low", n=4, **over):
    ids = ["P1", "P3", "P5", "P7"][:n]
    studies = []
    for i in ids:
        s = {"id": i, "design": design, "instrument": instrument, "domains": domains,
             "overall": overall, "confirmed_by": "K", "confirmed_at": "2026-07-26"}
        s.update(over)
        studies.append(s)
    return {"schema_version": "1.0", "studies": studies}


class TestOverallValidatedAgainstDomains(_Base):
    """P1 - an appraisal declaring overall 'low' over a 'high' domain is invalid,
    rob_appraisal.py rejects it, and grade_profile.py was consuming the favourable
    overall as backing for a zero risk-of-bias downgrade."""

    BAD = dict(ROB2, randomization="high")

    def test_favourable_overall_is_rejected(self):
        code, out, err = self.run_gp(self.profile(),
                                     appraisal("rct", "rob2", self.BAD), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("more favourable than its worst domain", err)
        self.assertNotIn("✅", out)

    def test_both_checks_agree_on_the_same_file(self):
        rob = appraisal("rct", "rob2", self.BAD)
        code_gp, _, _ = self.run_gp(self.profile(), rob, "--strict")
        code_ra, _, _ = self.run_ra(rob, "--strict")
        self.assertNotEqual(code_gp, 0)
        self.assertNotEqual(code_ra, 0)

    def test_recorded_justification_is_honoured(self):
        """The sibling allows an override; so must this."""
        rob = appraisal("rct", "rob2", self.BAD,
                        overall_justification="Attrition balanced; analysis unchanged.")
        code, out, err = self.run_gp(self.profile(), rob, "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_nos_band_mismatch_is_rejected(self):
        rec = self.profile(design_mix={"rct": 0, "nrsi": 0, "observational": 4,
                                       "dta": 0, "case_series": 0},
                           starting_level="low", final="low")
        rec["results"][0]["domains"]["inconsistency"]["rating"] = 0
        bad_nos = dict(NOS, selection=0)          # total 5 bands as moderate, not low
        code, _, err = self.run_gp(rec, appraisal("observational", "nos", bad_nos), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("bands as", err)


class TestDiagnosticAccuracyGradeable(_Base):
    """P1 - a QUADAS-2 appraisal has design 'dta', which had no design_mix category,
    so the distribution reconcile raised KeyError on the verdict path and made
    confirmed diagnostic-accuracy evidence impossible to grade at all."""

    def dta_profile(self):
        return self.profile(design_mix={"rct": 0, "nrsi": 0, "observational": 0,
                                        "dta": 4, "case_series": 0},
                            starting_level="high", final="moderate")

    def test_dta_body_does_not_crash(self):
        code, out, err = self.run_gp(self.dta_profile(),
                                     appraisal("dta", "quadas2", QUADAS), "--strict")
        self.assertNotIn("Traceback", err)
        self.assertNotIn("KeyError", err)
        self.assertEqual(code, 0, msg=out + err)

    def test_dta_starts_high_not_low(self):
        """GRADE rates a body of test-accuracy studies as starting HIGH. Mapping dta
        onto 'observational' would understate certainty by two levels."""
        self.assertEqual(gp.DESIGN_START["dta"], "high")

    def test_dta_starting_level_low_is_flagged(self):
        rec = self.dta_profile()
        rec["results"][0]["starting_level"] = "low"
        rec["results"][0]["final"] = "very_low"
        code, out, _ = self.run_gp(rec, appraisal("dta", "quadas2", QUADAS), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("predominant design 'dta'", out)

    def test_dta_distribution_is_reconciled(self):
        rec = self.profile(design_mix={"rct": 4, "nrsi": 0, "observational": 0,
                                       "dta": 0, "case_series": 0})
        code, out, _ = self.run_gp(rec, appraisal("dta", "quadas2", QUADAS), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("dta=4", out)

    def test_scope_limit_is_documented(self):
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "skills/validate-evidence/scripts/grade_profile.py").read_text(encoding="utf-8")
        self.assertIn("SENSITIVITY and SPECIFICITY as separate", src)


class TestCaseSeriesUntraceable(_Base):
    """Adjacent trap of the same class, found while fixing: case_series has no
    risk-of-bias instrument, so it can never appear in an appraisal record. Naively
    reconciling would report a guaranteed mismatch for a legitimate record."""

    def test_case_series_body_reports_the_limitation_not_a_mismatch(self):
        rec = self.profile(design_mix={"rct": 0, "nrsi": 0, "observational": 0,
                                       "dta": 0, "case_series": 4},
                           starting_level="very_low", final="very_low")
        rec["results"][0]["domains"]["inconsistency"]["rating"] = 0
        code, out, _ = self.run_gp(rec, appraisal("rct", "rob2", ROB2), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("no risk-of-bias instrument", out)
        self.assertIn("cannot be verified", out)
        self.assertNotIn("design_mix claims", out)

    def test_appraisable_designs_excludes_case_series(self):
        self.assertNotIn("case_series", gp.APPRAISABLE_DESIGNS)
        self.assertEqual(set(gp.APPRAISABLE_DESIGNS), set(ra.DESIGN_INSTRUMENT))


class TestPredominantDesignTaxonomy(unittest.TestCase):
    """The KeyError came from a hand-maintained order dict that went stale when a
    design was added. Strength now derives from DESIGN_START."""

    def test_every_design_has_a_starting_level(self):
        self.assertEqual(set(gp.DESIGNS), set(gp.DESIGN_START))

    def test_no_design_raises(self):
        for d in gp.DESIGNS:
            with self.subTest(design=d):
                mix = {x: 0 for x in gp.DESIGNS}
                mix[d] = 3
                self.assertEqual(gp.predominant_design(mix), d)

    def test_tie_resolves_to_the_weaker_starting_level(self):
        mix = {x: 0 for x in gp.DESIGNS}
        mix["rct"] = mix["observational"] = 4
        self.assertEqual(gp.predominant_design(mix), "observational")

    def test_tie_between_equal_strength_designs_is_deterministic(self):
        mix = {x: 0 for x in gp.DESIGNS}
        mix["rct"] = mix["dta"] = 4          # both start high
        self.assertEqual(gp.predominant_design(mix), gp.predominant_design(dict(mix)))


if __name__ == "__main__":
    unittest.main()


class TestRound5NoInformation(_Base):
    """Round 5 (1 finding) — the fifth instance of the same disagreement class.

    _validate_appraisal_overall filters unorderable domains out of the worst-domain
    comparison, which is right: ROBINS-I `no_information` cannot be ranked. But
    filtering it must not silently EXONERATE it. An overall of 'low' while a domain
    reports nothing is a claim the record has to justify, and rob_appraisal.py
    rejects exactly that.
    """

    ROBINS = {"confounding": "low", "participant_selection": "low",
              "intervention_classification": "low", "deviations": "low",
              "missing_data": "low", "outcome_measurement": "low",
              "selection_of_result": "low"}

    def nrsi_profile(self):
        return self.profile(design_mix={"rct": 0, "nrsi": 4, "observational": 0,
                                        "dta": 0, "case_series": 0},
                            starting_level="low", final="very_low")

    def _rob(self, **over):
        doms = dict(self.ROBINS, confounding="no_information")
        return appraisal("nrsi", "robins_i", doms, **over)

    def test_low_overall_with_no_information_is_rejected(self):
        code, out, err = self.run_gp(self.nrsi_profile(), self._rob(), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("no information", err)
        self.assertIn("absence of evidence", err)
        self.assertNotIn("✅", out)

    def test_justification_permits_it(self):
        rob = self._rob(overall_justification="Design precludes confounding.")
        code, out, err = self.run_gp(self.nrsi_profile(), rob, "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_non_low_overall_with_no_information_is_fine(self):
        """The rule targets 'low' specifically; 'moderate' is an honest reading."""
        code, out, err = self.run_gp(self.nrsi_profile(), self._rob(overall="moderate"),
                                     "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_both_checks_agree(self):
        rob = self._rob()
        code_gp, _, _ = self.run_gp(self.nrsi_profile(), rob, "--strict")
        code_ra, _, _ = self.run_ra(rob, "--strict")
        self.assertNotEqual(code_gp, 0)
        self.assertNotEqual(code_ra, 0)
