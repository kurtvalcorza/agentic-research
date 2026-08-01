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

        It asserts the GATE passed — not that the record reconciles. The first
        version of this test used `studies_included_total` as its inclusion key
        and asserted `code == 0` without --strict, so it passed green while the
        artifact it produced said the counts do NOT reconcile: the merge edge
        fires whenever the grand total is supplied, and compares it against arm
        totals defaulting to zero. Asserting the wrong thing is how a test agrees
        with a claim the code does not make.
        """
        code, out, err = self.run_record({
            "schema_version": "1.0",
            "identified_other": {"citation searching": 5},
            "studies_included_other": 5,
        }, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("flowchart", out)
        self.assertNotIn("do NOT reconcile", out)

    def test_the_grand_total_alone_checks_nothing(self):
        """The merge edge obeys the same both-counts-supplied rule as the rest.

        It used to fire on the grand total alone, comparing it against arm totals
        defaulting to zero — reporting a contradiction for `total: 5` and, worse,
        a satisfied check for `total: 0`, where 0 + 0 == 0 was recorded as a
        stage checked. Neither was a comparison of two supplied numbers.
        """
        code, out, err = self.run_record({
            "schema_version": "1.0",
            "identified_other": {"citation searching": 5},
            "studies_included_total": 5,
        }, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("Nothing was reconciled", out)
        self.assertNotIn("✅", out)

    def test_a_zero_grand_total_no_longer_reconciles_vacuously(self):
        """The case both reviewers converged on: 0 + 0 == 0 read as a stage
        checked, so the record earned a tick for a comparison of two defaults."""
        code, out, err = self.run_record({
            "schema_version": "1.0",
            "identified_databases": {"OpenAlex": 1},
            "studies_included_total": 0,
        }, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertNotIn("stages checked: merge", out)
        self.assertIn("Nothing was reconciled", out)

    def test_the_merge_edge_still_fires_when_an_arm_is_supplied(self):
        """The guard must not cost the check. With an arm total present, the
        grand total is compared as before."""
        code, out, _ = self.run_record(
            counts_template1(studies_included_total=40), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("studies_included_total = 40", out)


    def test_a_zero_count_still_counts_as_supplied(self):
        """A review that identified nothing is a real, reportable outcome. The gate
        is about presence, never magnitude — the whole point of the distinction."""
        code, out, err = self.run_record({
            "schema_version": "1.0",
            "identified_databases": {"OpenAlex": 0},
            "studies_included_total": 0,
        })
        self.assertEqual(code, 0, msg=out + err)

    def test_an_explicit_null_does_not_satisfy_the_gate(self):
        """The first version of this gate tested key PRESENCE, so a record naming
        both ends as null passed it and then reproduced the exact defect the gate
        was added to stop: every reader downstream treats null as absent, so no
        edge was checked, and the all-zero diagram printed "counts reconcile end
        to end" at exit 0 under --strict. Supplied means carrying a value."""
        rec = {"schema_version": "1.0",
               "identified_databases": None, "studies_included_total": None}
        code, out, err = self.run_record(rec, "--strict")
        self.assertEqual(code, 2, msg=out + err)
        self.assertIn("no identification count supplied", err)
        self.assertNotIn("reconcile end to end", out)
        self.assertNotIn("flowchart", out)

    def test_null_at_either_end_alone_is_also_rejected(self):
        for null_key, expected in (("identified_databases", "identification"),
                                   ("studies_included_total", "inclusion")):
            with self.subTest(null_key=null_key):
                rec = {"schema_version": "1.0",
                       "identified_databases": {"OpenAlex": 5},
                       "studies_included_total": 5}
                rec[null_key] = None
                code, _, err = self.run_record(rec)
                self.assertEqual(code, 2)
                self.assertIn(f"no {expected} count supplied", err)

    def test_one_real_value_survives_a_null_sibling(self):
        """Null must not disqualify an end that another key genuinely supplies."""
        code, out, err = self.run_record({
            "schema_version": "1.0",
            "identified_databases": None,
            "identified_other": {"citation searching": 5},
            "studies_included_other": 5,
        })
        self.assertEqual(code, 0, msg=out + err)

    def test_an_empty_breakdown_does_not_satisfy_the_gate(self):
        """The third door onto the same defect, after omission and null.

        `{}` is not None, so it passed a not-None test — and it names no source
        and sums to zero, so the record behaved exactly like the empty one and
        emitted the all-zero diagram again. The constitution names this case
        directly: an empty collection must report failure, not vacuous success.
        """
        for key in ("identified_databases", "identified_registers", "identified_other"):
            with self.subTest(key=key):
                code, out, err = self.run_record(
                    {"schema_version": "1.0", key: {}, "studies_included_total": 0},
                    "--strict")
                self.assertEqual(code, 2, msg=out + err)
                self.assertIn("no identification count supplied", err)
                self.assertNotIn("flowchart", out)

    def test_an_empty_breakdown_on_the_inclusion_end_too(self):
        code, out, err = self.run_record(
            {"schema_version": "1.0",
             "identified_databases": {"OpenAlex": 5},
             "reports_excluded": {}}, "--strict")
        self.assertEqual(code, 2, msg=out + err)
        self.assertIn("no inclusion count supplied", err)


class TestTheBringYourOwnCorpusRecord(_RunRecord):
    """The record three skill documents instruct an agent to write.

    Rule 8 broke this workflow — a regression, not a gap: the same record exits 0
    on main. It is documented in synthesize-research and orchestrate-research,
    which also forbade the obvious workaround ("do not invent identification
    numbers"), and two documents promised a screening-only mode that has never
    existed. Pinned here so the guidance and the check cannot drift apart again.
    """

    RECORD = {
        "schema_version": "1.0",
        "identified_databases": {"pre-collected corpus": 120},
        "duplicates_removed": 0,
        "records_screened": 120,
        "records_excluded_title_abstract": 80,
        "reports_sought": 40,
        "reports_not_retrieved": 0,
        "reports_assessed": 40,
        "reports_excluded": {"wrong population": 22},
        "studies_included_databases": 18,
        "studies_included_total": 18,
    }

    def test_the_documented_record_reconciles(self):
        code, out, err = self.run_record(dict(self.RECORD), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("✅", out)

    def test_it_renders_one_connected_arm(self):
        """The corpus belongs in the databases/registers arm because that is the
        only arm with a title/abstract screening stage. Putting it in
        identified_other reconciled just as well and drew two dead subgraphs —
        an identification box at n=0 feeding a screening box at n=120, beside an
        identification box at n=120 feeding a sought box at n=0."""
        _, out, _ = self.run_record(dict(self.RECORD))
        self.assertIn('ID["Records identified: n=120', out)
        self.assertIn('SCR["Records screened: n=120"]', out)
        self.assertNotIn("IDO[", out)          # no phantom other-methods arm
        self.assertNotIn('n=0<br/>"]', out)    # no identification box reading zero

    def test_omitting_identification_entirely_is_still_refused(self):
        """The rule this workflow has to satisfy rather than bypass."""
        rec = dict(self.RECORD)
        del rec["identified_databases"]
        code, _, err = self.run_record(rec, "--strict")
        self.assertEqual(code, 2)
        self.assertIn("no identification count supplied", err)


class TestTheTickMustBeEarned(_RunRecord):
    """An empty error list is "nothing failed", never "everything held".

    A record naming only its two ends supplies no edge with both counts, so no
    arithmetic runs and `reconcile()` returns [] for want of any check — which
    printed as "✅ Counts reconcile end to end" over a flow that had never been
    examined. Issue #9 asked for the message to be a function of how many edges
    were actually checked; a presence gate alone does not deliver that, because
    a record can pass the gate and still check nothing.
    """

    def test_a_record_checking_nothing_does_not_claim_reconciliation(self):
        code, out, err = self.run_record({
            "schema_version": "1.0",
            "identified_databases": {"OpenAlex": 500},
            "studies_included_databases": 500,
        }, "--strict")
        self.assertEqual(code, 0, msg=out + err)   # incomplete, not contradictory
        self.assertNotIn("✅", out)
        self.assertIn("Nothing was reconciled", out)
        self.assertIn("does not attest", out)

    def test_a_reconciling_record_says_how_much_it_checked(self):
        code, out, err = self.run_record(counts_template1(), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("✅", out)
        self.assertIn("5 of 5 stages checked", out)
        for stage in ("identification", "screening", "retrieval", "eligibility", "merge"):
            self.assertIn(stage, out)

    def test_the_denominator_is_the_applicable_stages(self):
        """"5 of 8" reported three stages as skipped that did not apply at all.

        A one-arm record has no other-methods stages to check. A two-arm record
        has eight, and template 2 supplies every count they read.
        """
        _, one_arm, _ = self.run_record(counts_template1())
        self.assertIn("5 of 5 stages checked", one_arm)
        _, two_arm, _ = self.run_record(counts_template2())
        self.assertIn("8 of 8 stages checked", two_arm)

    def checked_line(self, out):
        """The '✅ … stages checked: a, b, c.' line, without the unreached list."""
        return [ln for ln in out.splitlines() if "stages checked" in ln][0]

    def test_an_unreached_stage_is_named_in_the_artifact(self):
        """The artifact has to say WHICH stages it could not check.

        The first version of this test asserted the opposite of its own name:
        the code printed a bare count, the contract already promised names, and
        the assertion pinned the absence of them. A count tells a reader how much
        is missing without telling them what, which is the half they cannot act
        on.
        """
        rec = counts_template1()
        del rec["records_excluded_title_abstract"]     # disables `screening` only
        _, out, _ = self.run_record(rec)
        self.assertIn("4 of 5 stages checked", out)
        self.assertIn("Not checked: screening", out)
        self.assertNotIn("screening", self.checked_line(out))

    def test_the_count_comes_from_the_gates_themselves(self):
        """Not a second copy of the presence rules, which would be free to drift.
        Removing a count must remove exactly the edges it gated."""
        full, partial = [], []
        pf.reconcile(counts_template1(), full)
        rec = counts_template1()
        del rec["records_screened"]
        pf.reconcile(rec, partial)
        self.assertIn("screening", full)
        self.assertNotIn("screening", partial)
        self.assertLess(len(partial), len(full))

    def test_the_optional_parameter_leaves_existing_callers_alone(self):
        self.assertEqual(pf.reconcile(counts_template1()), [])
        self.assertEqual(pf.reconcile(counts_template2()), [])


class TestAnEdgeGatesOnAllOfItsOperands(_RunRecord):
    """Every count an edge reads, not merely the two its name mentions.

    Six of the eight stages used to gate on two counts and let any further
    operand default to zero, so `screening` was reported as checked with
    `records_excluded_title_abstract` never supplied — it had compared
    `screened - 0` against `sought`. Same shape as the defect this whole check
    exists to refuse: a number nobody gave being treated as if it were given.

    Each case below removes ONE operand from an otherwise complete record and
    asserts the stage it feeds drops out. Removing an operand must never turn a
    reconciling record into a failing one — an incomplete record is not a
    contradictory one — so each also asserts exit 0 under --strict.
    """

    # The unit to remove is the OPERAND, which for identification's removal box
    # is the whole group — deleting only `duplicates_removed` leaves
    # `removed_other_reasons` supplying it, which is the group rule working as
    # designed and is covered separately below.
    OPERANDS = {
        "identification": ("duplicates_removed", "removed_other_reasons"),
        "screening": ("records_excluded_title_abstract",),
        "retrieval": ("reports_not_retrieved",),
        "eligibility": ("reports_excluded",),
    }

    def test_removing_any_operand_drops_its_stage(self):
        for stage, keys in self.OPERANDS.items():
            with self.subTest(stage=stage, removed=keys):
                rec = counts_template1()
                for k in keys:
                    del rec[k]
                checked = []
                pf.reconcile(rec, checked)
                self.assertNotIn(stage, checked,
                                 f"{stage} was checked with {keys} never supplied")

    def test_removing_an_operand_never_creates_a_failure(self):
        for keys in self.OPERANDS.values():
            with self.subTest(removed=keys):
                rec = counts_template1()
                for k in keys:
                    del rec[k]
                code, out, err = self.run_record(rec, "--strict")
                self.assertEqual(code, 0, msg=f"{keys}\n{out}\n{err}")

    def test_the_other_arm_operands_too(self):
        for stage, key in (("other retrieval", "other_reports_not_retrieved"),
                           ("other eligibility", "other_reports_excluded"),
                           ("other identification", "identified_other")):
            with self.subTest(stage=stage, removed=key):
                rec = counts_template2()
                del rec[key]
                checked = []
                pf.reconcile(rec, checked)
                self.assertNotIn(stage, checked)

    def test_a_group_is_supplied_when_any_member_is(self):
        """`identified_registers` and `removed_other_reasons` are routinely
        omitted. Omitting one member of a group states that category is zero;
        omitting the whole group states nothing and must skip the edge."""
        rec = counts_template1()
        del rec["identified_registers"]          # group still has identified_databases
        del rec["removed_other_reasons"]         # group still has duplicates_removed
        checked = []
        self.assertEqual(pf.reconcile(rec, checked), [])
        self.assertIn("identification", checked)

        rec = counts_template1()
        del rec["duplicates_removed"]
        del rec["removed_other_reasons"]         # whole removal group gone
        checked = []
        pf.reconcile(rec, checked)
        self.assertNotIn("identification", checked)

    def test_the_merge_requires_every_arm_the_record_describes(self):
        """The `or` this replaces stopped the grand total being compared against
        two defaults, but in a two-arm record still let the other arm default."""
        rec = counts_template2()
        del rec["studies_included_other"]
        checked = []
        pf.reconcile(rec, checked)
        self.assertNotIn("merge", checked)

        rec = counts_template1()                 # one arm: databases only
        checked = []
        self.assertEqual(pf.reconcile(rec, checked), [])
        self.assertIn("merge", checked)

    def test_an_explicit_null_operand_does_not_count_as_supplied(self):
        """Supplied means carrying a value here too, not merely a key.

        `reconcile()` tested key presence while `validate_record()` tested for a
        value — one word, two meanings, one file. Most keys hid it because they
        are coerced through _int() before their edge is gated, so a null exits 2
        first. `studies_included_total` is read without eager coercion, so
        `"studies_included_total": null` satisfied presence, `merge` was recorded
        as checked as a side effect of the edge() call, and the arithmetic was
        then skipped by a guard AFTER it. A stage reported as confirmed with
        nothing compared.
        """
        rec = {"schema_version": "1.0",
               "identified_databases": {"x": 10}, "duplicates_removed": 0,
               "records_screened": 10, "studies_included_databases": 7,
               "studies_included_total": None}
        checked = []
        self.assertEqual(pf.reconcile(rec, checked), [])
        self.assertNotIn("merge", checked)
        _, out, _ = self.run_record(rec)
        # merge now appears in the artifact — as a stage NOT reached, which is
        # the point. It must not appear in the checked list.
        checked_line = [ln for ln in out.splitlines() if "stages checked" in ln][0]
        self.assertNotIn("merge", checked_line)
        self.assertIn("Not checked:", out)
        self.assertIn("merge", out.split("Not checked:")[1])

    def test_a_null_breakdown_operand_also_skips_its_edge(self):
        rec = counts_template1()
        rec["reports_excluded"] = None
        checked = []
        pf.reconcile(rec, checked)
        self.assertNotIn("eligibility", checked)

    def test_an_empty_breakdown_is_a_supplied_operand(self):
        """`{}` here means zero, itemised as nothing — a real claim.

        Deliberately NOT the stricter test rule 8 applies, where an empty
        breakdown is the vacuous case (`identified_databases: {}` names no
        source, and a record whose only identification key is empty exits 2).
        As an operand it is different: "we excluded nothing at full text" is an
        ordinary outcome, and 18 assessed − 0 = 18 included is an ordinary
        reconciliation. Requiring a non-empty breakdown would force a fabricated
        exclusion reason to get the stage checked.
        """
        rec = counts_template1(reports_excluded={}, studies_included_databases=72,
                               studies_included_total=72)
        checked = []
        self.assertEqual(pf.reconcile(rec, checked), [])
        self.assertIn("eligibility", checked)

    def test_the_applicable_stages_follow_the_arms_the_record_describes(self):
        """The denominator was one-sided: `_has_other` removed the other arm's
        stages while the databases arm was assumed always present, so an
        other-methods-only record was told four databases stages "could not be
        checked" for an arm it never claimed — the same complaint that made the
        denominator applicable rather than a fixed eight, mirrored."""
        other_only = {
            "schema_version": "1.0",
            "identified_other": {"citation searching": 20},
            "other_reports_sought": 20, "other_reports_not_retrieved": 0,
            "other_reports_assessed": 20,
            "other_reports_excluded": {"wrong outcome": 5},
            "studies_included_other": 15, "studies_included_total": 15,
        }
        self.assertEqual(
            pf.applicable_stages(other_only),
            ("other identification", "other retrieval", "other eligibility", "merge"))
        code, out, err = self.run_record(other_only, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("4 of 4 stages checked", out)
        self.assertNotIn("Not checked", out)
        # Compare the stage list itself rather than searching for substrings:
        # "other identification" contains "identification".
        listed = out.split("stages checked: ")[1].rstrip().rstrip(".").split(", ")
        self.assertEqual(listed, ["other identification", "other retrieval",
                                  "other eligibility", "merge"])
        checked = []
        pf.reconcile(other_only, checked)
        self.assertEqual(checked, listed)

    def test_applicable_stages_for_each_template(self):
        self.assertEqual(len(pf.applicable_stages(counts_template1())), 5)
        self.assertEqual(len(pf.applicable_stages(counts_template2())), 8)

    def test_the_numerator_can_never_exceed_the_denominator(self):
        """It could, and printed "5 of 0 stages checked".

        Applicability used a MAGNITUDE test for the databases arm while the
        edges gate on presence, and reconcile() does not gate that arm's block at
        all. So a record supplying the whole arm as real zeros checked five
        stages while the denominator counted none applicable — a fraction that
        does not parse, and worse than the wording this change removed.

        Applicability has to describe what reconcile() could actually have run,
        which is presence for the ungated arm and _has_other() for the gated one.
        """
        all_zero = {
            "schema_version": "1.0",
            "identified_databases": {"OpenAlex": 0}, "duplicates_removed": 0,
            "records_screened": 0, "records_excluded_title_abstract": 0,
            "reports_sought": 0, "reports_not_retrieved": 0, "reports_assessed": 0,
            "reports_excluded": {}, "studies_included_databases": 0,
            "studies_included_total": 0,
        }
        checked = []
        self.assertEqual(pf.reconcile(all_zero, checked), [])
        self.assertLessEqual(len(checked), len(pf.applicable_stages(all_zero)))
        code, out, err = self.run_record(all_zero, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("5 of 5 stages checked", out)

    def test_the_diagram_draws_only_the_arms_the_record_describes(self):
        """An other-methods-only record used to publish a complete databases
        column reading n=0 at every node, beside a reconciliation line calling
        those stages inapplicable. A fabricated column in the artifact is worse
        than a missing one, and the diagram must not describe a different flow
        from the verdict — both now use the same arm predicate."""
        other_only = {
            "schema_version": "1.0",
            "identified_other": {"citation searching": 20},
            "other_reports_sought": 20, "other_reports_not_retrieved": 0,
            "other_reports_assessed": 20,
            "other_reports_excluded": {"wrong outcome": 5},
            "studies_included_other": 15, "studies_included_total": 15,
        }
        _, out, _ = self.run_record(other_only)
        self.assertIn('subgraph OTHER', out)
        self.assertNotIn("DBREG", out)
        self.assertNotIn("INCDB", out)
        self.assertIn('INC["Studies included in review: n=15"]', out)
        # and the databases arm still renders for a record that describes it
        _, t1, _ = self.run_record(counts_template1())
        self.assertIn("DBREG", t1)

    def test_unreached_stages_are_named_on_the_failing_branch_too(self):
        """The names were computed only inside the clean branch, so a record with
        one failing stage and another it could not reach reported "2 of 5" and
        never said which was missing — the reader fixing the failure would not
        have learned there was a second gap."""
        rec = {"schema_version": "1.0", "identified_databases": {"x": 100},
               "duplicates_removed": 0, "records_screened": 50,   # identification fails
               "reports_sought": 50,                              # screening unreachable
               "studies_included_databases": 0, "studies_included_total": 0}
        code, out, _ = self.run_record(rec, "--strict")
        self.assertEqual(code, 1)
        self.assertIn("do NOT reconcile", out)
        self.assertIn("Not checked:", out)
        self.assertIn("screening", out.split("Not checked:")[1])

    def test_both_arms_are_detected_the_same_way(self):
        """Keeping one arm on magnitude while the other moved to presence left
        the same defect mirrored. Two shapes, both raised by both reviewers:

        A record supplying the whole other arm as real zeros — a citation search
        that found nothing — was treated as never having mentioned it: three
        stages gone from the count, its column gone from the diagram.

        And `{"identified_other": {"citation searching": 0},
        "studies_included_total": 0}` passes rule 8, described no arm under a
        magnitude test, so had NO applicable stages while the merge still fired
        on the grand total alone — printing `1 of 0 stages checked`.
        """
        mirror = {"schema_version": "1.0",
                  "identified_other": {"citation searching": 0},
                  "studies_included_total": 0}
        checked = []
        pf.reconcile(mirror, checked)
        self.assertLessEqual(len(checked), len(pf.applicable_stages(mirror)))
        _, out, _ = self.run_record(mirror)
        self.assertNotIn("1 of 0", out)
        self.assertIn("Nothing was reconciled", out)

    def test_an_arm_described_entirely_as_zeros_is_still_described(self):
        """Zero is an answer. A review that searched citations and found nothing
        described that arm, and presence is what this file uses everywhere else."""
        rec = counts_template2(
            identified_other={"citation searching": 0}, other_reports_sought=0,
            other_reports_not_retrieved=0, other_reports_assessed=0,
            other_reports_excluded={}, studies_included_other=0,
            studies_included_total=38)
        self.assertTrue(pf._has_other(rec))
        self.assertEqual(len(pf.applicable_stages(rec)), 8)
        code, out, err = self.run_record(rec, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("8 of 8 stages checked", out)
        self.assertIn("subgraph OTHER", out)

    def test_every_checked_stage_is_an_applicable_one(self):
        """The invariant behind it, across every record shape in the suite."""
        for name, rec in (("template1", counts_template1()),
                          ("template2", counts_template2()),
                          ("byo", {"schema_version": "1.0",
                                   "identified_databases": {"pre-collected corpus": 5},
                                   "duplicates_removed": 0, "records_screened": 5,
                                   "studies_included_databases": 5,
                                   "studies_included_total": 5})):
            with self.subTest(record=name):
                checked = []
                pf.reconcile(rec, checked)
                self.assertTrue(set(checked) <= set(pf.applicable_stages(rec)),
                                f"{set(checked) - set(pf.applicable_stages(rec))}")

    def test_identification_is_gated_on_presence_not_truthiness(self):
        """The old gate also required a non-zero identified count, which is the
        truthiness test this module's own docstring rejects. A record claiming
        zero identified and five screened is a contradiction, not a gap."""
        code, out, _ = self.run_record({
            "schema_version": "1.0",
            "identified_databases": {"OpenAlex": 0},
            "duplicates_removed": 0,
            "records_screened": 5,
            "studies_included_databases": 0,
            "studies_included_total": 0,
        }, "--strict")
        self.assertEqual(code, 1)
        self.assertIn("records_screened = 5", out)


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
