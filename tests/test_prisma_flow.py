"""Coverage for skills/prisma-flow/scripts/prisma_flow.py.

The flow check is the repository's flagship gate — the README leads with it — and
until now it had no tests. Standard library only.
"""
from __future__ import annotations

import io
import json
import pathlib
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

pf = load("skills/prisma-flow/scripts/prisma_flow.py")


def counts_template1(**overrides):
    """A reconciling databases-and-registers-only flow (PRISMA 2020 Template 1)."""
    c = {
        "schema_version": "1.0",
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


class TestSharedCliContractConformance(unittest.TestCase):
    """contracts/cli-contract.md binds ALL FOUR checks — "a check that deviates is
    non-conforming regardless of whether its own rules are correct".

    This one, the oldest, enforced neither the schema version nor a closed key set
    while the three added by this feature enforced both. A misspelled count key
    dropped silently out of the record, the remaining arithmetic reconciled, and
    the diagram printed an authoritative ✅ over a number nobody had checked.
    """

    def run_record(self, rec, *args):
        out, err = io.StringIO(), io.StringIO()
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / "counts.json"
        p.write_text(json.dumps(rec), encoding="utf-8")
        with mock.patch.object(sys, "argv", ["prisma_flow.py", str(p), *args]), \
                redirect_stdout(out), redirect_stderr(err):
            code = pf.main()
        return code, out.getvalue(), err.getvalue()

    def test_a_missing_schema_version_is_malformed(self):
        rec = counts_template1()
        del rec["schema_version"]
        code, out, err = self.run_record(rec, "--strict")
        self.assertEqual(code, 2)
        self.assertIn("schema_version", err)
        self.assertNotIn("✅", out)

    def test_an_unrecognised_schema_version_is_malformed(self):
        code, _, err = self.run_record(counts_template1(schema_version="9.9"), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("schema_version", err)

    def test_an_unhashable_schema_version_does_not_raise(self):
        """isinstance before set membership: `[] in {"1.0"}` is a TypeError, which
        would surface as a traceback and exit 1 rather than the documented 2."""
        code, _, err = self.run_record(counts_template1(schema_version=[]), "--strict")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_a_misspelled_count_key_is_rejected_not_ignored(self):
        """The fail-open this closes: read past, the count drops out of the record
        and the arithmetic still reconciles over what is left."""
        code, out, err = self.run_record(
            counts_template1(recrods_screenedd=999), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("recrods_screenedd", err)
        self.assertNotIn("✅", out)
        self.assertNotIn("```mermaid", out)      # no artifact on malformed input

    def test_a_conforming_record_still_passes(self):
        code, out, err = self.run_record(counts_template1(), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("✅", out)

    def test_every_key_the_script_reads_is_in_the_closed_schema(self):
        """A key the script consumes but the schema omits would be rejected as
        unknown — the check refusing its own documented input."""
        source = pathlib.Path(
            pf.__file__ if hasattr(pf, "__file__") else "").read_text(encoding="utf-8")
        consumed = set(re.findall(r'c\.get\("([a-z_]+)"', source))
        self.assertTrue(consumed)
        self.assertEqual(consumed - pf.RECORD_KEYS, set())


class _RunRecord(unittest.TestCase):
    """Run the CLI over a record and return (exit code, stdout, stderr)."""

    def run_record(self, rec, *args):
        out, err = io.StringIO(), io.StringIO()
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / "counts.json"
        p.write_text(json.dumps(rec), encoding="utf-8")
        with mock.patch.object(sys, "argv", ["prisma_flow.py", str(p), *args]), \
                redirect_stdout(out), redirect_stderr(err):
            code = pf.main()
        return code, out.getvalue(), err.getvalue()


class TestAnExplicitZeroIsChecked(_RunRecord):
    """An edge is checked when both its counts were SUPPLIED, not when both are truthy.

    Truthiness could not tell an omitted count from one recorded as `0`, so a record
    stating 500 identified, 96 removed and `records_screened: 0` disabled three edges
    at once and reconciled clean under --strict. The closed schema was added to stop a
    MISSPELLED key producing exactly that; a correctly spelled zero did it too.
    """

    def test_an_explicit_zero_does_not_disable_its_edges(self):
        code, out, _ = self.run_record(counts_template1(records_screened=0), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("records_screened = 0", out)
        self.assertNotIn("✅", out)

    def test_an_omitted_count_still_skips_its_edges(self):
        """The distinction the truthiness test could not draw: a record that simply
        does not carry a count is incomplete, not contradictory."""
        rec = counts_template1()
        del rec["records_screened"]
        del rec["records_excluded_title_abstract"]
        code, out, err = self.run_record(rec, "--strict")
        self.assertEqual(code, 0, msg=out + err)

    def test_a_zero_included_count_is_still_reconciled(self):
        """A review that included nothing is a real outcome, and its arithmetic still
        has to add up."""
        rec = counts_template1(studies_included_databases=0, studies_included_total=0)
        code, out, _ = self.run_record(rec, "--strict")
        self.assertEqual(code, 1)
        self.assertIn("studies_included_databases = 0", out)


class TestARecordMustNameBothEndsOfTheFlow(_RunRecord):
    """A record supplying no counts produced a diagram that certified itself.

    Every node read `n=0` and the reconciliation line said "counts reconcile end
    to end", exit 0, unchanged by --strict. Nothing was wrong with the arithmetic:
    with nothing supplied, no edge is checked, and the check could not distinguish
    "no edge was checked" from "no edge was broken". Zero is what absent counts
    defaulted to, which the constitution forbids in as many words — report missing
    rather than defaulting to zero.

    The flow runs from records identified to studies included, so a record naming
    neither end is not an under-specified diagram; it is not a diagram.
    """

    def test_a_record_with_no_counts_is_rejected(self):
        code, out, err = self.run_record({"schema_version": "1.0"})
        self.assertEqual(code, 2, msg=out + err)
        self.assertIn("no identification count supplied", err)
        self.assertNotIn("reconcile end to end", out)
        self.assertNotIn("flowchart", out, msg="no artifact may be emitted")

    def test_strict_does_not_rescue_it(self):
        """--strict was the strongest gate on offer and it returned 0 as well."""
        code, out, err = self.run_record({"schema_version": "1.0"}, "--strict")
        self.assertEqual(code, 2, msg=out + err)

    def test_identification_without_inclusion_is_rejected(self):
        rec = counts_template1()
        for k in ("studies_included_databases", "studies_included_total"):
            del rec[k]
        code, _, err = self.run_record(rec)
        self.assertEqual(code, 2)
        self.assertIn("no inclusion count supplied", err)

    def test_inclusion_without_identification_is_rejected(self):
        rec = counts_template1()
        for k in ("identified_databases", "identified_registers"):
            del rec[k]
        code, _, err = self.run_record(rec)
        self.assertEqual(code, 2)
        self.assertIn("no identification count supplied", err)

    def test_any_one_key_from_each_end_suffices(self):
        """The gate asks for a named beginning and end, not a complete record.
        A partially reported flow is still reportable — that is what the
        supplied-versus-truthy edge logic exists to handle."""
        code, out, err = self.run_record({
            "schema_version": "1.0",
            "identified_other": {"citation searching": 5},
            "studies_included_total": 5,
        })
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("flowchart", out)

    def test_a_zero_count_still_counts_as_supplied(self):
        """A review that identified nothing is a real, reportable outcome. The gate
        is about presence, never magnitude — the whole point of the distinction."""
        code, out, err = self.run_record({
            "schema_version": "1.0",
            "identified_databases": {"OpenAlex": 0},
            "studies_included_total": 0,
        })
        self.assertEqual(code, 0, msg=out + err)


class TestBreakdownKeysMustBeObjects(_RunRecord):
    """Closing the key set said which keys may appear, never what may appear under
    them. The five breakdown keys are read with `.items()`, so a truthy non-mapping
    reached it unguarded and died with an AttributeError traceback at exit 1 —
    where the contract promises a structured error at exit 2, and where exit 1
    additionally means "method violation, artifact emitted". Fifteen shapes did
    this. The scalar count keys were never affected: _int() already rejected every
    wrong type.
    """

    WRONG = {"int": 500, "str": "500", "list": [1], "bool": True}

    def test_every_breakdown_key_rejects_every_non_object(self):
        for key in sorted(pf.BREAKDOWN_KEYS):
            for label, value in self.WRONG.items():
                with self.subTest(key=key, given=label):
                    code, out, err = self.run_record(counts_template2(**{key: value}))
                    self.assertEqual(code, 2, msg=f"{out}\n{err}")
                    self.assertIn(key, err)
                    self.assertNotIn("Traceback", err)

    def test_the_message_says_what_was_expected(self):
        code, _, err = self.run_record(counts_template1(identified_databases=500))
        self.assertEqual(code, 2)
        self.assertIn("expected an object mapping each source to its count", err)

    def test_null_still_reads_as_absent(self):
        """Explicit null has always meant "not supplied" here, and still does."""
        code, out, err = self.run_record(counts_template2(other_reports_excluded=None))
        self.assertNotEqual(code, 2, msg=out + err)

    def test_sum_refuses_a_non_mapping_on_its_own(self):
        """validate_record is the gate; this is the backstop. A future caller
        reaching _sum directly must still get CountError, not AttributeError."""
        with self.assertRaises(pf.CountError):
            pf._sum(500, "identified_databases")
        with self.assertRaises(pf.CountError):
            pf._sum("500", "identified_databases")
        self.assertEqual(pf._sum(None, "identified_databases"), 0)
