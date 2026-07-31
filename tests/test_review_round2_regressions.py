"""Regressions for the six findings from round 2 of review on PR #3.

Round 1 was about validating leaf TYPES. Round 2 is narrower and harder: fields
that are individually well-typed but CONTRADICT EACH OTHER, or a required field
whose absence was never noticed.

  - design_mix said 100 RCTs while study_ids listed 4 studies
  - a --rob record carried confirmations but no appraisal at all
  - the units table registered units the routing table had no route for

Type-correct input that disagrees with itself still passes a type check.
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
from _load import load, fixture, REPO_ROOT  # noqa: E402

ra = load("skills/appraise-risk-of-bias/scripts/rob_appraisal.py")
gp = load("skills/validate-evidence/scripts/grade_profile.py")
pc = load("skills/prisma-flow/scripts/prisma_checklist.py")
ru = load("skills/verify-review/scripts/review_units.py")


class _Base(unittest.TestCase):
    def write(self, rec, name="rec.json"):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / name
        p.write_text(json.dumps(rec), encoding="utf-8")
        return p

    def run_script(self, module, path, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["x.py", str(path), *args]), \
                redirect_stdout(out), redirect_stderr(err):
            code = module.main()
        return code, out.getvalue(), err.getvalue()

    def profile(self, **over):
        rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
        rec["results"][0].update(over)
        return rec


def full_appraisal(ids=("P1", "P3", "P5", "P7"), **over):
    def study(sid):
        s = {"id": sid, "design": "rct", "instrument": "rob2",
             "domains": {"randomization": "low", "deviations": "low", "missing_data": "low",
                         "measurement": "low", "selection_of_result": "low"},
             "overall": "low", "result_assessed": 'diagnostic accuracy at 12 months',
             "confirmed_by": "K", "confirmed_at": "2026-07-26"}
        s.update(over)
        return s
    return {"schema_version": "1.0", "studies": [study(i) for i in ids]}


class TestP1StubAppraisalRejected(_Base):
    """P1 — a --rob record of {id, overall, confirmed_by, confirmed_at} carried no
    appraisal at all, yet backed a `confirmed_rob` basis with a clean verdict."""

    def test_stub_without_design_is_rejected(self):
        stub = {"schema_version": "1.0", "studies": [
            {"id": s, "overall": "low", "result_assessed": 'diagnostic accuracy at 12 months',
             "confirmed_by": "K", "confirmed_at": "2026-07-26"}
            for s in ("P1", "P3", "P5", "P7")]}
        code, out, err = self.run_script(
            gp, fixture("grade-profile.valid.json"),
            "--rob", str(self.write(stub, "rob.json")), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("design", err)
        self.assertNotIn("✅", out)

    def test_stub_without_domains_is_rejected(self):
        """Later reclassified from exit 2 to exit 1.

        A record with no domains is INCOMPLETE, not unreadable: rob_appraisal.py
        reports the absent domains and exits 1 with diagnostics, so exiting 2 here
        denied the reader the diagnostics its owning check gives them. Still
        rejected — the assertion moved from the exit code alone to the exit code
        AND the named domains.
        """
        rob = full_appraisal()
        for s in rob["studies"]:
            del s["domains"]
        code, out, err = self.run_script(
            gp, fixture("grade-profile.valid.json"),
            "--rob", str(self.write(rob, "rob.json")), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("rob2 requires domain(s)", out)
        self.assertIn("cannot back a 'confirmed_rob' basis", out)
        self.assertNotIn("✅", out)

    def test_partial_domains_are_rejected(self):
        """Five domains define RoB 2; three is an incomplete appraisal."""
        rob = full_appraisal()
        for s in rob["studies"]:
            s["domains"] = {"randomization": "low", "deviations": "low", "missing_data": "low"}
        code, out, err = self.run_script(
            gp, fixture("grade-profile.valid.json"),
            "--rob", str(self.write(rob, "rob.json")), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("measurement", out)
        self.assertIn("which are absent", out)
        self.assertNotIn("✅", out)

    def test_instrument_must_match_design_in_the_rob_file(self):
        rob = full_appraisal(instrument="quadas2")
        code, out, err = self.run_script(
            gp, fixture("grade-profile.valid.json"),
            "--rob", str(self.write(rob, "rob.json")), "--strict")
        self.assertEqual(code, 1, msg=err)
        self.assertIn("instrument mismatch", out)
        self.assertIn("calls for", out)
        self.assertIn("## Evidence profile", out)

    def test_overall_checked_against_the_right_instrument_vocabulary(self):
        """'unclear' is QUADAS-2 vocabulary, not RoB 2 — the union check missed this."""
        rob = full_appraisal(overall="unclear")
        code, _, err = self.run_script(
            gp, fixture("grade-profile.valid.json"),
            "--rob", str(self.write(rob, "rob.json")), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("rob2", err)

    def test_a_complete_appraisal_still_passes(self):
        code, out, err = self.run_script(
            gp, fixture("grade-profile.valid.json"),
            "--rob", str(self.write(full_appraisal(), "rob.json")), "--strict")
        self.assertEqual(code, 0, msg=out + err)


class TestP1DesignMixReconciles(_Base):
    """P1, the most consequential — design_mix determines the STARTING LEVEL and was
    never checked against the studies actually cited."""

    def test_inflated_mix_is_rejected(self):
        rec = self.profile(design_mix={"rct": 100, "nrsi": 0, "observational": 0,
                                       "case_series": 0})
        code, out, err = self.run_script(
            gp, self.write(rec), "--rob",
            str(self.write(full_appraisal(), "rob.json")), "--strict")
        self.assertEqual(code, 2, msg=f"got {code}")
        self.assertIn("100", err)
        self.assertIn("4", err)
        self.assertNotIn("## Evidence profile", out)

    def test_undercounted_mix_is_rejected(self):
        rec = self.profile(design_mix={"rct": 2, "nrsi": 0, "observational": 0,
                                       "case_series": 0})
        code, _, err = self.run_script(
            gp, self.write(rec), "--rob",
            str(self.write(full_appraisal(), "rob.json")), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("must describe the body it", err)

    def test_matching_mix_passes(self):
        code, out, err = self.run_script(
            gp, fixture("grade-profile.valid.json"), "--rob",
            str(self.write(full_appraisal(), "rob.json")), "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_a_genuine_minority_rct_body_is_still_caught_by_the_level_rule(self):
        """The reconcile rule must not mask the starting-level rule it protects."""
        code, out, _ = self.run_script(
            gp, fixture("grade-profile.minority-rct.json"), "--rob",
            str(self.write(full_appraisal(), "rob.json")), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("predominant design", out)


class TestP1RoutingTableComplete(unittest.TestCase):
    """P1 — the backend can nominate any registered unit as dominant_unit, but the
    routing table listed no route for the two new ones, so the loop would stall on
    exactly the failures this feature introduces."""

    def setUp(self):
        self.skill = (REPO_ROOT / "skills/verify-review/SKILL.md").read_text(encoding="utf-8")

    def test_every_registered_unit_has_a_route(self):
        table = self.skill.split("| Dominant unit | Route to |")[1]
        missing = [u for u in ru.DEFAULT_WEIGHTS if f"`{u}`" not in table]
        self.assertEqual(missing, [],
                         f"units with no repair route — the loop would stall: {missing}")

    def test_grade_route_is_not_the_stale_definition(self):
        table = self.skill.split("| Dominant unit | Route to |")[1]
        row = next(l for l in table.splitlines() if "`U_grade`" in l)
        self.assertNotIn("ungraded themes", row,
                         "route still describes the definition U_grade no longer has")

    def test_rob_trace_route_names_the_human_gate(self):
        table = self.skill.split("| Dominant unit | Route to |")[1]
        row = next(l for l in table.splitlines() if "`U_rob_trace`" in l)
        self.assertIn("H_rob", row)


class TestP2UnhashableEnums(_Base):
    """P2 — `[] in {"1.0"}` raises TypeError (unhashable), producing a traceback and
    exit 1 rather than the documented exit 2."""

    def test_grade_profile_enums(self):
        for field, value in [("schema_version", []), ("review_type", {}),
                             ("synthesis_mode", [])]:
            rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
            rec[field] = value
            with self.subTest(field=field):
                code, _, err = self.run_script(gp, self.write(rec), "--strict")
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", err)

    def test_grade_profile_nested_enums(self):
        for field, value in [("starting_level", []), ("final", {})]:
            rec = self.profile(**{field: value})
            with self.subTest(field=field):
                code, _, err = self.run_script(gp, self.write(rec), "--strict")
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", err)

    def test_rob_appraisal_enums(self):
        for field, value in [("schema_version", []), ("design", {}), ("instrument", [])]:
            rec = full_appraisal()
            if field == "schema_version":
                rec[field] = value
            else:
                rec["studies"][0][field] = value
            with self.subTest(field=field):
                code, _, err = self.run_script(ra, self.write(rec), "--strict")
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", err)

    def test_checklist_enums(self):
        items = [{"number": n, "location": "S, p.1"} for _, n, _ in pc.PRISMA_2020]
        for field, value in [("schema_version", []), ("variant", {})]:
            rec = {"schema_version": "1.0", "variant": "prisma_2020", "items": items}
            rec[field] = value
            with self.subTest(field=field):
                code, _, err = self.run_script(pc, self.write(rec), "--strict")
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", err)


class TestP2QuadasApplicabilityRequired(_Base):
    """P2 — QUADAS-2's first three domains carry an applicability judgment; omitting
    all three still reported a clean, complete appraisal."""

    def _quadas(self, drop_applicability):
        doms = {}
        for name in ra.DOMAINS["quadas2"]:
            entry = {"risk_of_bias": "low"}
            if name in ra.QUADAS_APPLICABILITY and not drop_applicability:
                entry["applicability"] = "low"
            doms[name] = entry
        return {"schema_version": "1.0", "studies": [
            {"id": "D1", "design": "dta", "instrument": "quadas2", "domains": doms,
             "overall": "low", "result_assessed": 'diagnostic accuracy at 12 months',
             "confirmed_by": "K", "confirmed_at": "2026-07-26"}]}

    def test_missing_applicability_is_rejected(self):
        code, out, err = self.run_script(ra, self.write(self._quadas(True)), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("applicability", err)
        self.assertNotIn("✅", out)

    def test_present_applicability_passes(self):
        code, out, err = self.run_script(ra, self.write(self._quadas(False)), "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_flow_and_timing_needs_no_applicability(self):
        """Only the first three domains carry it — the fourth must not be required."""
        rec = self._quadas(False)
        self.assertNotIn("applicability", rec["studies"][0]["domains"]["flow_and_timing"])
        code, _, _ = self.run_script(ra, self.write(rec), "--strict")
        self.assertEqual(code, 0)


class TestP2OverallRequiredOnMismatch(_Base):
    """P2 — deferring the VOCABULARY check on an instrument mismatch is right, but
    presence is instrument-independent and was skipped."""

    def test_missing_overall_is_malformed_even_on_mismatch(self):
        rec = {"schema_version": "1.0", "studies": [
            {"id": "S1", "design": "rct", "instrument": "quadas2",
             "domains": {"patient_selection": "low"}, "result_assessed": 'diagnostic accuracy at 12 months',
             "confirmed_by": "K", "confirmed_at": "2026-07-26"}]}
        code, out, err = self.run_script(ra, self.write(rec), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("overall", err)
        self.assertNotIn("## Appraisal by study", out)

    def test_present_overall_still_yields_the_useful_mismatch_message(self):
        rec = {"schema_version": "1.0", "studies": [
            {"id": "S1", "design": "rct", "instrument": "quadas2",
             "domains": {"patient_selection": "low"}, "overall": "low",
             "result_assessed": 'diagnostic accuracy at 12 months',
             "confirmed_by": "K", "confirmed_at": "2026-07-26"}]}
        code, out, err = self.run_script(ra, self.write(rec), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("calls for rob2", out)
        self.assertNotIn("Traceback", err)


class TestResourceHandling(_Base):
    """Found while fixing round 2: input files were read via open().read() without
    a context manager, leaking the handle until GC."""

    def test_no_unclosed_file_warnings(self):
        import warnings
        for module, path in [(gp, fixture("grade-profile.valid.json")),
                             (ra, fixture("risk-of-bias.all-instruments.json")),
                             (pc, fixture("checklist.valid.json"))]:
            with self.subTest(script=module.__name__):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ResourceWarning)
                    self.run_script(module, path)
                leaks = [w for w in caught if issubclass(w.category, ResourceWarning)]
                self.assertEqual(leaks, [], f"unclosed handles: {[str(w.message) for w in leaks]}")


if __name__ == "__main__":
    unittest.main()
