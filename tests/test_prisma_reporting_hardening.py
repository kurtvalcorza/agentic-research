"""Regression coverage for hardened PRISMA compliance unit attribution.

The RFC #21 compliance checker and the verify-review wiring are separate layers.
When the checker gained anti-vacuity rules, the derived unit predicate had to gain
the same mechanical rules; otherwise a strict child failure could be reported as
zero repairable work by the parent verdict.
"""
from __future__ import annotations

import unittest

from _load import load

pc = load("skills/prisma-flow/scripts/prisma_compliance.py")


def rows():
    return [
        {
            "number": number,
            "location": f"Manuscript section for PRISMA item {number}",
            "evidence": f"The manuscript substantively reports requirement {number} here.",
            "human_confirmed": True,
        }
        for _section, number, _topic in pc.PRISMA_2020
    ]


def entries(data):
    return pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})


class HardenedComplianceUnitsTests(unittest.TestCase):
    def test_placeholder_evidence_is_a_mechanical_unit(self):
        data = rows()
        data[0]["evidence"] = "x"
        parsed = entries(data)
        self.assertTrue(pc.check(parsed))
        self.assertIn("1", pc.mechanical_defects(parsed))

    def test_location_repeated_as_evidence_is_a_mechanical_unit(self):
        data = rows()
        data[0]["evidence"] = data[0]["location"]
        parsed = entries(data)
        self.assertTrue(pc.check(parsed))
        self.assertIn("1", pc.mechanical_defects(parsed))

    def test_illegal_na_is_a_mechanical_unit(self):
        data = rows()
        data[0] = {
            "number": "1",
            "not_applicable": "A long but invalid blanket N/A justification.",
            "human_confirmed": True,
        }
        parsed = entries(data)
        self.assertTrue(pc.check(parsed))
        self.assertIn("1", pc.mechanical_defects(parsed))

    def test_vacuous_conditional_na_is_a_mechanical_unit(self):
        data = rows()
        idx = next(i for i, row in enumerate(data) if row["number"] == "10b")
        data[idx] = {"number": "10b", "not_applicable": "n", "human_confirmed": True}
        parsed = entries(data)
        self.assertTrue(pc.check(parsed))
        self.assertIn("10b", pc.mechanical_defects(parsed))

    def test_confirmation_only_gap_remains_a_human_gate(self):
        data = rows()
        data[0]["human_confirmed"] = False
        parsed = entries(data)
        self.assertTrue(pc.check(parsed))
        self.assertNotIn("1", pc.mechanical_defects(parsed))
        self.assertEqual(1, pc.unconfirmed_assertions(parsed))


if __name__ == "__main__":
    unittest.main()
