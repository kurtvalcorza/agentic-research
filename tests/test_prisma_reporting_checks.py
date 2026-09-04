from __future__ import annotations

import unittest

from _load import load

vr = load("skills/verify-review/scripts/prisma_reporting_checks.py")


def env(check, units, issues=0):
    return {
        "check": check,
        "schema_version": "1.0",
        "issues": issues,
        "units": units,
        "gates": {},
        "unattributed": 0,
    }


class PrismaReportingChecksTests(unittest.TestCase):
    def test_clean_new_review_aggregate(self):
        out = vr.aggregate(
            env("prisma_abstract_checklist", {"U_prisma_abstract": 0}),
            env("prisma_compliance", {"U_prisma_compliance": 0}),
            None,
            require_updated=False,
        )
        self.assertEqual(0, out["issues"])
        self.assertEqual([], out["gates"]["underived"])
        self.assertTrue(out["detail"]["not_certification"])

    def test_required_updated_flow_is_explicitly_underived(self):
        out = vr.aggregate(
            env("prisma_abstract_checklist", {"U_prisma_abstract": 0}),
            env("prisma_compliance", {"U_prisma_compliance": 0}),
            None,
            require_updated=True,
        )
        self.assertEqual(["U_prisma_updated"], out["gates"]["underived"])
        self.assertEqual(1, out["issues"])

    def test_updated_flow_units_are_consumed_not_rederived(self):
        out = vr.aggregate(
            env("prisma_abstract_checklist", {"U_prisma_abstract": 2}, issues=2),
            env("prisma_compliance", {"U_prisma_compliance": 3}, issues=5),
            env("prisma_updated_flow", {"U_prisma_updated": 4}, issues=4),
            require_updated=True,
        )
        self.assertEqual(11, out["issues"])
        self.assertEqual(2, out["units"]["U_prisma_abstract"])
        self.assertEqual(3, out["units"]["U_prisma_compliance"])
        self.assertEqual(4, out["units"]["U_prisma_updated"])
        self.assertEqual([], out["gates"]["underived"])


if __name__ == "__main__":
    unittest.main()
