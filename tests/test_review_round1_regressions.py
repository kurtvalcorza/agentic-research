"""Regressions for the eight findings from round 1 of review on PR #3.

All eight shared one root cause: counts were made rigorously type-strict
(`_int`, `_rating`, `_stars` reject bools, quoted numbers and fractions) while
TEXT fields were taken on trust via `str(...)` coercion or bare truthiness.
`str({})` is `"{}"` — truthy and non-empty — so malformed JSON satisfied every
check that only asked "is this present and non-empty?".

Kept in one module so the findings stay legible as a set rather than scattered
across four files. Standard library only.
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

ra = load("skills/appraise-risk-of-bias/scripts/rob_appraisal.py")
gp = load("skills/validate-evidence/scripts/grade_profile.py")
pc = load("skills/prisma-flow/scripts/prisma_checklist.py")
nodeps = load("tests/test_no_dependencies.py")


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


def appraisal(**over):
    s = {"id": "R1", "design": "rct", "instrument": "rob2",
         "domains": {"randomization": "low", "deviations": "low", "missing_data": "low",
                     "measurement": "low", "selection_of_result": "low"},
         "overall": "low", "confirmed_by": "K. Valcorza", "confirmed_at": "2026-07-26"}
    s.update(over)
    return {"schema_version": "1.0", "studies": [s]}


class TestP1ConfirmationTypes(_Base):
    """P1 — `confirmed_by: {}` satisfied the human gate: exit 0, H_rob 0."""

    def test_object_confirmation_is_malformed(self):
        code, out, err = self.run_script(
            ra, self.write(appraisal(confirmed_by={}, confirmed_at=[])), "--strict")
        self.assertEqual(code, 2, msg=out[:200])
        self.assertIn("confirmed_by", err)
        self.assertNotIn("## Appraisal by study", out)

    def test_numeric_confirmation_is_malformed(self):
        code, _, err = self.run_script(
            ra, self.write(appraisal(confirmed_at=20260726)), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("confirmed_at", err)

    def test_genuine_absence_is_still_a_violation_not_malformed(self):
        """Missing confirmation is an outstanding human gate (exit 1), not garbage."""
        rec = appraisal()
        del rec["studies"][0]["confirmed_by"]
        code, out, _ = self.run_script(ra, self.write(rec), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("**H_rob: 1**", out)


class TestP1AppraisalBacking(_Base):
    """P1 (worst) — a malformed --rob file backed a confirmed_rob profile cleanly,
    defeating the traceability the human gate exists to provide."""

    def test_out_of_vocabulary_overall_is_rejected(self):
        rob = {"schema_version": "1.0", "studies": [
            {"id": "P1", "overall": "totally-made-up",
             "confirmed_by": {}, "confirmed_at": []}]}
        code, out, err = self.run_script(
            gp, fixture("grade-profile.valid.json"),
            "--rob", str(self.write(rob, "rob.json")), "--strict")
        self.assertEqual(code, 2, msg=f"got {code}")
        self.assertIn("overall", err)
        self.assertNotIn("✅", out)

    def test_object_confirmation_in_appraisal_is_rejected(self):
        rob = {"schema_version": "1.0", "studies": [
            {"id": "P1", "overall": "low", "confirmed_by": {}, "confirmed_at": "2026-07-26"}]}
        code, _, err = self.run_script(
            gp, fixture("grade-profile.valid.json"),
            "--rob", str(self.write(rob, "rob.json")), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("confirmed_by", err)


class TestP1InstrumentMismatchCrash(_Base):
    """P1 — a quadas2 declaration over string domains called .get() on a str,
    crashing AFTER the first table had already been printed."""

    def test_mismatch_does_not_crash_the_generator(self):
        rec = appraisal(instrument="quadas2", domains={"patient_selection": "low"})
        code, out, err = self.run_script(ra, self.write(rec), "--strict")
        self.assertNotIn("Traceback", err)
        self.assertEqual(code, 1)
        self.assertIn("calls for rob2", out)

    def test_mismatch_with_list_domain_is_malformed(self):
        """Leaf types are validated even when the vocabulary cannot be."""
        rec = appraisal(instrument="quadas2", domains={"patient_selection": ["low"]})
        code, _, err = self.run_script(ra, self.write(rec), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("patient_selection", err)


class TestP2HumanGateIndependence(_Base):
    """P2 — the instrument-mismatch `continue` skipped the human-gate count, so an
    unconfirmed study vanished from H_rob."""

    def test_unconfirmed_counted_even_with_wrong_instrument(self):
        rec = {"schema_version": "1.0", "studies": [
            {"id": "S1", "design": "rct", "instrument": "nos",
             "domains": {"selection": 4, "comparability": 2, "outcome_or_exposure": 3},
             "overall": "low"}]}
        code, out, _ = self.run_script(ra, self.write(rec), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("**H_rob: 1**", out)
        self.assertIn("no human confirmation recorded", out)
        self.assertIn("calls for rob2", out)


class TestP2Disclosure(_Base):
    """P2 — any truthy value satisfied the rapid-review disclosure check."""

    def _rapid(self, disclosed):
        rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
        rec["review_type"] = "rapid"
        rec["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        rec["streamlined_method_disclosed"] = disclosed
        return self.write(rec)

    def test_boolean_disclosure_is_malformed(self):
        code, _, err = self.run_script(gp, self._rapid(True), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("streamlined_method_disclosed", err)

    def test_blank_disclosure_is_a_violation(self):
        code, out, _ = self.run_script(gp, self._rapid("   "), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("must be stated", out)

    def test_real_disclosure_passes(self):
        code, out, _ = self.run_script(
            gp, self._rapid("Single-reviewer screening; two databases."), "--strict")
        self.assertEqual(code, 0, msg=out[:200])


class TestP2ChecklistFieldTypes(_Base):
    """P2 — a non-string location was read as merely empty, giving exit 1 with an
    artifact instead of exit 2 with none."""

    def _record(self, first):
        items = [{"number": n, "location": f"{s}, p.1"} for s, n, _ in pc.PRISMA_2020]
        items[0] = first
        return {"schema_version": "1.0", "variant": "prisma_2020", "items": items}

    def test_numeric_location_is_malformed(self):
        code, out, err = self.run_script(
            pc, self.write(self._record({"number": "1", "location": 123})), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("location", err)
        self.assertNotIn("## Checklist", out)

    def test_object_justification_is_malformed(self):
        code, _, err = self.run_script(
            pc, self.write(self._record(
                {"number": "1", "not_applicable": {"reason": "x"}})), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("not_applicable", err)

    def test_boolean_location_is_malformed(self):
        code, _, _ = self.run_script(
            pc, self.write(self._record({"number": "1", "location": True})), "--strict")
        self.assertEqual(code, 2)


class TestP2StarsDrift(unittest.TestCase):
    """P2 — _stars rejected the integral float 3.0 that every other coercer
    accepts, and the conformance guard built to catch drift omitted _stars."""

    def test_integral_float_accepted(self):
        self.assertEqual(ra._stars(3.0, "x", 4), 3)

    def test_fraction_still_rejected(self):
        with self.assertRaises(ra.InputError):
            ra._stars(3.5, "x", 4)

    def test_bool_still_rejected(self):
        with self.assertRaises(ra.InputError):
            ra._stars(True, "x", 4)

    def test_range_still_enforced(self):
        with self.assertRaises(ra.InputError):
            ra._stars(5.0, "x", 4)


class TestP2GuardedImportDetection(unittest.TestCase):
    """P2 — the classifier treated every descendant of a Try as guarded,
    including except/else/finally, where a missing package raises unhandled."""

    def _classify(self, src):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / "m.py"
        p.write_text(src, encoding="utf-8")
        return nodeps.collect_imports(p)

    def test_try_body_import_is_guarded(self):
        _, lazy = self._classify(
            "def f():\n    try:\n        import thirdparty\n"
            "    except ImportError:\n        pass\n")
        self.assertIn("thirdparty", lazy)

    def test_finally_import_is_not_guarded(self):
        module, lazy = self._classify(
            "def f():\n    try:\n        pass\n    finally:\n        import thirdparty\n")
        self.assertIn("thirdparty", module)
        self.assertNotIn("thirdparty", lazy)

    def test_except_handler_import_is_not_guarded(self):
        module, _ = self._classify(
            "def f():\n    try:\n        pass\n    except Exception:\n        import thirdparty\n")
        self.assertIn("thirdparty", module)

    def test_else_import_is_not_guarded(self):
        module, _ = self._classify(
            "def f():\n    try:\n        pass\n    except Exception:\n        pass\n"
            "    else:\n        import thirdparty\n")
        self.assertIn("thirdparty", module)

    def test_module_level_try_is_guarded_but_not_lazy(self):
        """Importing the module would still require the package."""
        module, lazy = self._classify(
            "try:\n    import thirdparty\nexcept ImportError:\n    thirdparty = None\n")
        self.assertIn("thirdparty", module)
        self.assertNotIn("thirdparty", lazy)

    def test_nested_fallback_import_is_still_guarded(self):
        """The real pattern in rlm_corpus_loader.py: a fallback import inside the
        handler's own try block."""
        _, lazy = self._classify(
            "def f():\n"
            "    try:\n"
            "        from pypdf import X\n"
            "    except Exception:\n"
            "        try:\n"
            "            from PyPDF2 import X\n"
            "        except Exception:\n"
            "            raise RuntimeError('Install pypdf')\n")
        self.assertIn("pypdf", lazy)
        self.assertIn("PyPDF2", lazy)


if __name__ == "__main__":
    unittest.main()
