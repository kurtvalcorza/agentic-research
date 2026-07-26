"""Coverage for skills/prisma-flow/scripts/prisma_flow.py.

The flow check is the repository's flagship gate — the README leads with it — and
until now it had no tests. Standard library only.
"""
from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _load import load  # noqa: E402

pf = load("skills/prisma-flow/scripts/prisma_flow.py")


def counts_template1(**overrides):
    """A reconciling databases-and-registers-only flow (PRISMA 2020 Template 1)."""
    c = {
        "identified_databases": {"OpenAlex": 412, "CrossRef": 88},
        "identified_registers": {"PROSPERO": 0},
        "duplicates_removed": 96,
        "removed_other_reasons": 0,
        "records_screened": 404,
        "records_excluded_title_abstract": 328,
        "reports_sought": 76,
        "reports_not_retrieved": 4,
        "reports_assessed": 72,
        "reports_excluded": {"wrong population": 18, "not empirical": 9, "wrong outcome": 7},
        "studies_included_databases": 38,
        "studies_included_total": 38,
    }
    c.update(overrides)
    return c


def counts_template2(**overrides):
    """A reconciling flow with the parallel other-methods arm (Template 2)."""
    c = counts_template1(
        identified_other={"citation searching": 23},
        other_reports_sought=23,
        other_reports_not_retrieved=1,
        other_reports_assessed=22,
        other_reports_excluded={"wrong outcome": 4},
        studies_included_other=18,
        studies_included_total=56,
    )
    c.update(overrides)
    return c


class TestReconcileTemplate1(unittest.TestCase):
    def test_clean_counts_reconcile(self):
        self.assertEqual(pf.reconcile(counts_template1()), [])

    def test_identification_break_is_reported(self):
        # Lowering records_screened breaks two consecutive steps, not one: the
        # identification subtraction AND the screening subtraction that follows
        # it. Both are real and both should be reported.
        errs = pf.reconcile(counts_template1(records_screened=400))
        ident = [e for e in errs if "identification" in e]
        self.assertEqual(len(ident), 1)
        # The message must carry the numbers, not just name the rule.
        self.assertIn("404", ident[0])
        self.assertTrue(any("screening" in e for e in errs))

    def test_screening_break_is_reported(self):
        errs = pf.reconcile(counts_template1(reports_sought=70))
        self.assertTrue(any("screening" in e for e in errs))

    def test_retrieval_break_is_reported(self):
        errs = pf.reconcile(counts_template1(reports_assessed=70))
        self.assertTrue(any("retrieval" in e for e in errs))

    def test_eligibility_break_is_reported(self):
        errs = pf.reconcile(counts_template1(studies_included_databases=40,
                                             studies_included_total=40))
        self.assertTrue(any("eligibility" in e for e in errs))

    def test_merge_mismatch_is_reported(self):
        errs = pf.reconcile(counts_template1(studies_included_total=40))
        self.assertTrue(any("merge" in e for e in errs))


class TestReconcileTemplate2(unittest.TestCase):
    def test_clean_two_arm_counts_reconcile(self):
        self.assertEqual(pf.reconcile(counts_template2()), [])

    def test_other_arm_is_detected(self):
        self.assertTrue(pf._has_other(counts_template2()))
        self.assertFalse(pf._has_other(counts_template1()))

    def test_other_arm_identification_break(self):
        errs = pf.reconcile(counts_template2(other_reports_sought=20))
        self.assertTrue(any("other methods identification" in e for e in errs))

    def test_other_arm_retrieval_break(self):
        errs = pf.reconcile(counts_template2(other_reports_assessed=20))
        self.assertTrue(any("other methods retrieval" in e for e in errs))

    def test_other_arm_eligibility_break(self):
        errs = pf.reconcile(counts_template2(studies_included_other=20,
                                             studies_included_total=58))
        self.assertTrue(any("other methods eligibility" in e for e in errs))

    def test_arms_reconcile_independently(self):
        """A break in one arm must not mask or duplicate into the other."""
        errs = pf.reconcile(counts_template2(records_screened=400))
        self.assertTrue(all("other methods" not in e for e in errs))


class TestCoercion(unittest.TestCase):
    """The shared input-coercion contract (specs/001 contracts/cli-contract.md)."""

    def test_accepts_int(self):
        self.assertEqual(pf._int(3, "x"), 3)

    def test_accepts_integral_float(self):
        self.assertEqual(pf._int(3.0, "x"), 3)

    def test_rejects_bool(self):
        # bool is an int subclass; True would otherwise silently become 1.
        with self.assertRaises(pf.CountError):
            pf._int(True, "x")

    def test_rejects_non_integral_float(self):
        with self.assertRaises(pf.CountError):
            pf._int(3.5, "x")

    def test_rejects_negative(self):
        with self.assertRaises(pf.CountError):
            pf._int(-1, "x")

    def test_rejects_non_finite(self):
        for bad in (float("nan"), float("inf")):
            with self.subTest(value=bad), self.assertRaises(pf.CountError):
                pf._int(bad, "x")

    def test_rejects_numeric_string(self):
        """A quoted count is malformed input, not a number to coerce.

        review_units.py already rejects non-numbers outright, commenting that a
        wrong type must fail closed. This asserts prisma_flow.py agrees, so the
        two gates share one definition of malformed input.
        """
        with self.assertRaises(pf.CountError):
            pf._int("3", "x")

    def test_rejects_none(self):
        with self.assertRaises(pf.CountError):
            pf._int(None, "x")

    def test_rejects_arbitrary_string(self):
        with self.assertRaises(pf.CountError):
            pf._int("many", "x")


class TestMermaid(unittest.TestCase):
    def test_template1_omits_other_arm(self):
        out = pf.mermaid(counts_template1())
        self.assertIn("```mermaid", out)
        self.assertIn("Identification via databases & registers", out)
        self.assertNotIn("Identification via other methods", out)

    def test_template2_includes_other_arm(self):
        out = pf.mermaid(counts_template2())
        self.assertIn("Identification via other methods", out)
        self.assertIn("INCO --> INC", out)

    def test_exclusion_reasons_are_tabulated(self):
        out = pf.mermaid(counts_template1())
        self.assertIn("wrong population: 18", out)

    def test_zero_exclusions_render(self):
        out = pf.mermaid(counts_template1(reports_excluded={}))
        self.assertIn("n=0", out)


class TestMain(unittest.TestCase):
    """Exit-code contract: 0 clean/non-strict, 1 violation under --strict, 2 malformed."""

    def _run(self, payload, *args):
        stdin = io.StringIO(payload if isinstance(payload, str) else json.dumps(payload))
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["prisma_flow.py", *args]), \
                mock.patch.object(sys, "stdin", stdin), \
                redirect_stdout(out), redirect_stderr(err):
            code = pf.main()
        return code, out.getvalue(), err.getvalue()

    def test_clean_exits_zero(self):
        code, out, _ = self._run(counts_template1())
        self.assertEqual(code, 0)
        self.assertIn("reconcile", out)

    def test_violation_without_strict_exits_zero(self):
        code, out, _ = self._run(counts_template1(studies_included_total=40))
        self.assertEqual(code, 0)
        self.assertIn("do NOT reconcile", out)

    def test_violation_with_strict_exits_one(self):
        code, _, _ = self._run(counts_template1(studies_included_total=40), "--strict")
        self.assertEqual(code, 1)

    def test_invalid_json_exits_two(self):
        code, _, err = self._run("{not json", "--strict")
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)

    def test_non_object_exits_two(self):
        code, _, err = self._run([1, 2, 3], "--strict")
        self.assertEqual(code, 2)
        self.assertIn("object", err)

    def test_bad_count_exits_two_not_one(self):
        """Malformed input must be distinguishable from a review being wrong."""
        code, _, err = self._run(counts_template1(duplicates_removed=True), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("duplicates_removed", err)

    def test_malformed_emits_no_artifact(self):
        """A record that cannot be read must not produce an authoritative-looking document."""
        _, out, _ = self._run(counts_template1(duplicates_removed=True), "--strict")
        self.assertNotIn("```mermaid", out)


if __name__ == "__main__":
    unittest.main()
