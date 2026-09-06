"""The PRISMA reporting sub-gate's aggregation contract.

`aggregate()` is what `review_units.py` ends up ingesting, so the shape matters as
much as the arithmetic: `units` carries only what actually ran, `gates` carries
COUNTS under the one gate key the table assigns this check, and an absent child is
absent rather than zero.
"""
from __future__ import annotations

import unittest

from _load import load

vr = load("skills/verify-review/scripts/prisma_reporting_checks.py")


def env(check, units, gates=None, issues=0, detail=None):
    body = {
        "check": check,
        "schema_version": "1.0",
        "issues": issues,
        "units": units,
        "gates": gates or {},
        "unattributed": 0,
    }
    if detail is not None:
        body["detail"] = detail
    return body


def compliance(units=0, gate=0, issues=0):
    return env("prisma_compliance", {"U_prisma_compliance": units},
               {"H_prisma_evidence": gate}, issues=issues)


def abstract(units=0, gate=0, issues=0, verification="compliance"):
    return env("prisma_abstract_checklist", {"U_prisma_abstract": units},
               {"H_prisma_evidence": gate}, issues=issues,
               detail={"verification": verification})


def updated(units=0, issues=0):
    return env("prisma_updated_flow", {"U_prisma_updated": units}, {}, issues=issues)


class TestTheAggregateShape(unittest.TestCase):
    def test_a_compliance_only_run_reports_one_unit_and_the_gate(self):
        out = vr.aggregate(compliance())
        self.assertEqual({"U_prisma_compliance": 0}, out["units"])
        self.assertEqual({"H_prisma_evidence": 0}, out["gates"])
        self.assertEqual(vr.CHECK_NAME, out["check"])
        self.assertTrue(out["detail"]["not_certification"])

    def test_an_absent_child_is_absent_from_units_not_zero(self):
        """The distinction the earlier `gates: {"underived": [...]}` field tried to
        carry, now expressed where the consumer already models it: a unit the run
        did not derive is simply not reported, and `review_units.py` holds the
        verdict through its own `conditional_units` mapping."""
        out = vr.aggregate(compliance())
        self.assertNotIn("U_prisma_abstract", out["units"])
        self.assertNotIn("U_prisma_updated", out["units"])
        self.assertEqual(["U_prisma_abstract", "U_prisma_updated"],
                         out["detail"]["underived"])

    def test_every_child_reports_its_own_unit(self):
        out = vr.aggregate(compliance(units=3, issues=5), abstract(units=2, issues=2),
                           updated(units=4, issues=4))
        self.assertEqual(11, out["issues"])
        self.assertEqual({"U_prisma_compliance": 3, "U_prisma_abstract": 2,
                          "U_prisma_updated": 4}, out["units"])
        self.assertEqual([], out["detail"]["underived"])


class TestTheHumanGate(unittest.TestCase):
    def test_the_gate_sums_the_children_that_count_confirmations(self):
        out = vr.aggregate(compliance(gate=4), abstract(gate=2), updated())
        self.assertEqual(6, out["gates"]["H_prisma_evidence"])

    def test_pending_confirmations_survive_zero_repairable_defects(self):
        """The failure mode this gate exists for: every row located and evidenced,
        no unit outstanding, and not one confirmation given. Before the gate the two
        records were indistinguishable at the verdict."""
        out = vr.aggregate(compliance(units=0, gate=42, issues=42))
        self.assertEqual(0, out["units"]["U_prisma_compliance"])
        self.assertEqual(42, out["gates"]["H_prisma_evidence"])

    def test_an_addressability_abstract_record_is_refused(self):
        """Aggregating it would report a satisfied human gate over a record that
        never asserted compliance and so owes no confirmation."""
        with self.assertRaises(vr.InputError) as caught:
            vr.aggregate(compliance(), abstract(verification="addressability"))
        self.assertIn("compliance", str(caught.exception))


class TestChildOutputIsNotTrusted(unittest.TestCase):
    def test_a_child_claiming_another_identity_is_rejected(self):
        with self.assertRaises(vr.InputError):
            vr.aggregate(env("prisma_checklist", {"U_prisma_compliance": 0},
                             {"H_prisma_evidence": 0}))

    def test_a_negative_or_non_integer_count_is_rejected(self):
        for bad in (-1, 1.5, True, "0", None):
            with self.subTest(value=bad):
                with self.assertRaises(vr.InputError):
                    vr.aggregate(env("prisma_compliance", {"U_prisma_compliance": bad},
                                     {"H_prisma_evidence": 0}))

    def test_a_negative_issue_count_is_rejected(self):
        with self.assertRaises(vr.InputError):
            vr.aggregate(compliance(issues=-2))

    def test_a_child_that_drops_its_own_unit_is_not_read_as_clean(self):
        """Absent is not zero on the unit side."""
        with self.assertRaises(vr.InputError):
            vr.aggregate(env("prisma_compliance", {}, {"H_prisma_evidence": 0}))

    def test_a_child_with_no_confirmations_may_omit_the_gate(self):
        """The other half of the same rule: `prisma_updated_flow` has no
        confirmations to count and reports `gates: {}`, which is not a gap."""
        out = vr.aggregate(compliance(), None, updated())
        self.assertEqual(0, out["gates"]["H_prisma_evidence"])
        self.assertIn("U_prisma_updated", out["units"])


if __name__ == "__main__":
    unittest.main()
