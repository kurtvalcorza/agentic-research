from __future__ import annotations

import unittest

from _load import load

pc = load("skills/prisma-flow/scripts/prisma_checklist.py")


def complete_items(*, evidence=True, confirmed=True):
    rows = []
    for _, number, _ in pc.PRISMA_2020:
        row = {"number": number, "location": f"Section for {number}"}
        if evidence:
            row["evidence"] = f"Substantive reporting evidence for {number}."
        if confirmed is not None:
            row["human_confirmed"] = confirmed
        rows.append(row)
    return rows


class PrismaComplianceModeTests(unittest.TestCase):
    def test_legacy_parse_defaults_to_addressability(self):
        table, entries, verification = pc.parse_record({
            "schema_version": "1.0",
            "variant": "prisma_2020",
            "items": complete_items(evidence=False, confirmed=None),
        })
        self.assertEqual("addressability", verification)
        self.assertEqual([], pc.check(table, entries))

    def test_location_only_cannot_pass_compliance(self):
        table, entries, verification = pc.parse_record({
            "schema_version": "1.0",
            "variant": "prisma_2020",
            "verification": "compliance",
            "items": complete_items(evidence=False, confirmed=None),
        })
        self.assertEqual("compliance", verification)
        errors = pc.check_compliance(table, entries)
        self.assertEqual(84, len(errors))
        self.assertTrue(any("no substantive evidence" in e for e in errors))
        self.assertTrue(any("not human-confirmed" in e for e in errors))

    def test_complete_evidenced_human_confirmed_record_passes(self):
        table, entries, _ = pc.parse_record({
            "schema_version": "1.0",
            "variant": "prisma_2020",
            "verification": "compliance",
            "items": complete_items(),
        })
        self.assertEqual([], pc.check_compliance(table, entries))

    def test_not_applicable_requires_human_confirmation(self):
        rows = complete_items()
        item = next(row for row in rows if row["number"] == "13e")
        item.pop("location")
        item.pop("evidence")
        item["not_applicable"] = "No heterogeneity exploration was applicable."
        item["human_confirmed"] = False
        table, entries, _ = pc.parse_record({
            "schema_version": "1.0",
            "variant": "prisma_2020",
            "verification": "compliance",
            "items": rows,
        })
        errors = pc.check_compliance(table, entries)
        self.assertTrue(any(e.startswith("item 13e ") and "not human-confirmed" in e for e in errors))

    def test_evidence_and_confirmation_types_fail_closed(self):
        rows = complete_items()
        rows[0]["evidence"] = ["not text"]
        with self.assertRaises(pc.InputError):
            pc.parse_record({
                "schema_version": "1.0",
                "variant": "prisma_2020",
                "verification": "compliance",
                "items": rows,
            })


if __name__ == "__main__":
    unittest.main()
