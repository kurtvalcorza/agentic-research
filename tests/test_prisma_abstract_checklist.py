from __future__ import annotations

import unittest

from _load import load

MOD = load("skills/prisma-flow/scripts/prisma_abstract_checklist.py")


def _items(*, evidence=True, confirmed=True):
    rows = []
    for number, _ in MOD.PRISMA_ABSTRACTS:
        row = {"number": number, "location": f"Abstract sentence {number}"}
        if evidence:
            row["evidence"] = f"Item {number} is explicitly reported."
        if confirmed is not None:
            row["human_confirmed"] = confirmed
        rows.append(row)
    return rows


class PrismaAbstractChecklistTests(unittest.TestCase):
    def test_source_has_twelve_items(self):
        self.assertEqual(12, len(MOD.PRISMA_ABSTRACTS))
        self.assertEqual({str(i) for i in range(1, 13)}, {n for n, _ in MOD.PRISMA_ABSTRACTS})

    def test_complete_compliance_record_is_clean(self):
        verification, entries = MOD.parse({
            "schema_version": "1.0",
            "variant": "prisma_2020_abstracts",
            "verification": "compliance",
            "items": _items(),
        })
        errors, statuses = MOD.check(verification, entries)
        self.assertEqual([], errors)
        self.assertTrue(all(status == "verified" for status in statuses.values()))

    def test_location_only_is_not_compliance(self):
        verification, entries = MOD.parse({
            "schema_version": "1.0",
            "variant": "prisma_2020_abstracts",
            "verification": "compliance",
            "items": _items(evidence=False, confirmed=None),
        })
        errors, _ = MOD.check(verification, entries)
        self.assertEqual(24, len(errors))
        self.assertTrue(any("no substantive evidence" in e for e in errors))
        self.assertTrue(any("not human-confirmed" in e for e in errors))

    def test_location_only_is_valid_addressability(self):
        verification, entries = MOD.parse({
            "schema_version": "1.0",
            "variant": "prisma_2020_abstracts",
            "verification": "addressability",
            "items": _items(evidence=False, confirmed=None),
        })
        errors, statuses = MOD.check(verification, entries)
        self.assertEqual([], errors)
        self.assertTrue(all(status == "addressed" for status in statuses.values()))

    def test_missing_item_fails(self):
        verification, entries = MOD.parse({
            "schema_version": "1.0",
            "variant": "prisma_2020_abstracts",
            "verification": "compliance",
            "items": _items()[:-1],
        })
        errors, _ = MOD.check(verification, entries)
        self.assertTrue(any(e.startswith("item 12 ") for e in errors))

    def test_na_requires_human_confirmation_in_compliance_mode(self):
        rows = _items()
        rows[-1] = {"number": "12", "not_applicable": "Review was not registered."}
        verification, entries = MOD.parse({
            "schema_version": "1.0",
            "variant": "prisma_2020_abstracts",
            "verification": "compliance",
            "items": rows,
        })
        errors, _ = MOD.check(verification, entries)
        self.assertTrue(any(e.startswith("item 12 ") and "human-confirmed" in e for e in errors))

    def test_unknown_field_fails_closed(self):
        with self.assertRaises(MOD.InputError):
            MOD.parse({
                "schema_version": "1.0",
                "variant": "prisma_2020_abstracts",
                "verification": "compliance",
                "items": [{"number": "1", "location": "Abstract", "typo": True}],
            })

    def test_both_location_and_na_is_malformed(self):
        with self.assertRaises(MOD.InputError):
            MOD.parse({
                "schema_version": "1.0",
                "variant": "prisma_2020_abstracts",
                "verification": "compliance",
                "items": [{
                    "number": "1",
                    "location": "Title",
                    "not_applicable": "no",
                }],
            })


if __name__ == "__main__":
    unittest.main()
