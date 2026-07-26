"""Regressions for the two findings from round 3 of review on PR #3.

Both said my ROUND 2 fixes were insufficient rather than wrong, and both trace to
one shortcut: I chose cardinality over content, and totals over distribution,
specifically to avoid duplicating the instrument schema in grade_profile.py.

  - design_mix totalling correctly while describing the wrong designs
  - a domain set of the right SIZE but arbitrary NAMES

Both shortcuts produced the same symptom: grade_profile.py reported clean on a
file that rob_appraisal.py rejected with exit 2.

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

NOS_DOMAINS = {"selection": 4, "comparability": 2, "outcome_or_exposure": 3}
ROB2_DOMAINS = {"randomization": "low", "deviations": "low", "missing_data": "low",
                "measurement": "low", "selection_of_result": "low"}


class _Base(unittest.TestCase):
    def write(self, rec, name="rec.json"):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / name
        p.write_text(json.dumps(rec), encoding="utf-8")
        return p

    def run_gp(self, rec, rob, *args):
        out, err = io.StringIO(), io.StringIO()
        argv = ["gp.py", str(self.write(rec)), "--rob", str(self.write(rob, "rob.json")), *args]
        with mock.patch.object(sys, "argv", argv), redirect_stdout(out), redirect_stderr(err):
            code = gp.main()
        return code, out.getvalue(), err.getvalue()

    def profile(self, **over):
        rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
        rec["results"][0].update(over)
        return rec


def appraisal(design, n, domains=None):
    inst = {"rct": "rob2", "observational": "nos"}[design]
    doms = domains if domains is not None else (ROB2_DOMAINS if inst == "rob2" else NOS_DOMAINS)
    ids = ["P1", "P3", "P5", "P7"][:n]
    return {"schema_version": "1.0", "studies": [
        {"id": i, "design": design, "instrument": inst, "domains": doms, "overall": "low",
         "confirmed_by": "K", "confirmed_at": "2026-07-26"} for i in ids]}


class TestDesignDistributionReconciled(_Base):
    """P1 — the round-2 fix compared only the TOTAL. Four observational studies
    declared as {"rct": 4} totals correctly and still inflates the starting level
    from LOW to HIGH, which is the entire failure the check was added to stop."""

    def test_correct_total_wrong_designs_is_rejected(self):
        code, out, _ = self.run_gp(self.profile(), appraisal("observational", 4), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("design_mix claims rct=4", out)
        self.assertIn("referenced appraisals are observational=4", out)

    def test_matching_distribution_passes(self):
        code, out, err = self.run_gp(self.profile(), appraisal("rct", 4), "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_partial_swap_is_rejected(self):
        rob = appraisal("rct", 4)
        rob["studies"][0]["design"] = "observational"
        rob["studies"][0]["instrument"] = "nos"
        rob["studies"][0]["domains"] = NOS_DOMAINS
        code, out, _ = self.run_gp(self.profile(), rob, "--strict")
        self.assertEqual(code, 1)
        self.assertIn("design_mix claims", out)

    def test_totals_check_still_applies_without_rob(self):
        """Without an appraisal the distribution cannot be verified, so the totals
        rule remains the only guard — and must still fire."""
        rec = self.profile(design_mix={"rct": 100, "nrsi": 0, "observational": 0,
                                       "case_series": 0})
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["gp.py", str(self.write(rec)), "--strict"]), \
                redirect_stdout(out), redirect_stderr(err):
            code = gp.main()
        self.assertEqual(code, 2)
        self.assertIn("must describe the body it", err.getvalue())

    def test_limitation_is_documented(self):
        """Principle VI: the residual gap must be stated, not hidden."""
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "skills/validate-evidence/scripts/grade_profile.py").read_text(encoding="utf-8")
        self.assertIn("Without --rob, whether design_mix describes the studies", src)


class TestAppraisalDomainNamesValidated(_Base):
    """P1 — checking the domain COUNT let five arbitrary keys pass as a complete
    RoB 2 appraisal, so the two checks disagreed about the same file."""

    JUNK = {"a": None, "b": False, "c": [], "d": {}, "e": "garbage"}

    def test_count_correct_junk_is_rejected(self):
        code, out, err = self.run_gp(self.profile(),
                                     appraisal("rct", 4, domains=self.JUNK), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("unrecognised", err)
        self.assertNotIn("✅", out)

    def test_both_checks_now_agree_on_the_same_file(self):
        """The symptom that mattered: one check clean, the other exit 2."""
        rob = appraisal("rct", 4, domains=self.JUNK)
        code_gp, _, _ = self.run_gp(self.profile(), rob, "--strict")

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["ra.py", str(self.write(rob, "j.json")), "--strict"]), \
                redirect_stdout(out), redirect_stderr(err):
            code_ra = ra.main()
        self.assertEqual(code_gp, code_ra, "the two checks must agree about one file")
        self.assertEqual(code_gp, 2)

    def test_wrong_value_vocabulary_is_rejected(self):
        doms = dict(ROB2_DOMAINS, randomization="unclear")   # QUADAS-2 word on RoB 2
        code, _, err = self.run_gp(self.profile(), appraisal("rct", 4, domains=doms), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("rob2", err)

    def test_nos_star_range_enforced_in_the_rob_file(self):
        rec = self.profile(design_mix={"rct": 0, "nrsi": 0, "observational": 4,
                                       "case_series": 0}, starting_level="low",
                           final="low")
        rec["results"][0]["domains"]["inconsistency"]["rating"] = 0
        bad = dict(NOS_DOMAINS, comparability=9)             # max is 2
        code, _, err = self.run_gp(rec, appraisal("observational", 4, domains=bad), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("between 0 and 2", err)

    def test_a_real_appraisal_still_passes(self):
        code, out, err = self.run_gp(self.profile(), appraisal("rct", 4), "--strict")
        self.assertEqual(code, 0, msg=out + err)


if __name__ == "__main__":
    unittest.main()
