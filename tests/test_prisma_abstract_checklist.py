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


def _record(items, verification="compliance"):
    return {
        "schema_version": "1.0",
        "variant": "prisma_2020_abstracts",
        "verification": verification,
        "items": items,
    }


class AbstractComplianceIsNotFailOpenTests(unittest.TestCase):
    """Negative controls for F24-09.

    The 12-item checker shipped with a compliance mode that any non-empty
    ``not_applicable`` string satisfied, and that accepted one-character evidence.
    Both are the defect class the 42-row sibling already rejects, and both are
    reachable at the verdict once ``U_prisma_abstract`` is derived. These tests pin
    the closure: a compliance-looking PASS must not be reachable through blanket or
    illegitimate N/A, nor through vacuous or restating evidence.
    """

    def test_blanket_na_on_every_item_is_refused(self):
        rows = [
            {"number": number, "not_applicable": "x", "human_confirmed": True}
            for number, _ in MOD.PRISMA_ABSTRACTS
        ]
        verification, entries = MOD.parse(_record(rows))
        errors, statuses = MOD.check(verification, entries)
        # Every item errors: the eleven mandatory ones because N/A is not a
        # legitimate disposition, item 12 because "x" asserts nothing.
        self.assertEqual(12, len(errors))
        self.assertTrue(any(e.startswith("item 1 ") and "not a legitimate" in e for e in errors))
        self.assertTrue(any(e.startswith("item 2 ") and "not a legitimate" in e for e in errors))
        self.assertTrue(any(e.startswith("item 3 ") and "not a legitimate" in e for e in errors))
        self.assertTrue(any(e.startswith("item 12 ") and "too short" in e for e in errors))
        self.assertFalse(any(status == "verified" for status in statuses.values()))
        self.assertEqual(12, len(MOD.mechanical_defects(verification, entries)))

    def test_one_character_evidence_is_not_substantive(self):
        rows = [
            {
                "number": number,
                "location": f"Abstract sentence {number}",
                "evidence": "x",
                "human_confirmed": True,
            }
            for number, _ in MOD.PRISMA_ABSTRACTS
        ]
        verification, entries = MOD.parse(_record(rows))
        errors, _ = MOD.check(verification, entries)
        self.assertEqual(12, len(errors))
        self.assertTrue(all("too short to be substantive" in e for e in errors))
        self.assertEqual(12, len(MOD.mechanical_defects(verification, entries)))

    def test_evidence_that_merely_restates_the_location_is_refused(self):
        rows = [
            {
                "number": number,
                "location": f"Abstract sentence {number}",
                "evidence": f"abstract SENTENCE {number}",
                "human_confirmed": True,
            }
            for number, _ in MOD.PRISMA_ABSTRACTS
        ]
        verification, entries = MOD.parse(_record(rows))
        errors, _ = MOD.check(verification, entries)
        self.assertEqual(12, len(errors))
        self.assertTrue(all("merely restates the location" in e for e in errors))
        self.assertEqual(12, len(MOD.mechanical_defects(verification, entries)))

    def test_substantive_na_on_a_conditional_item_is_accepted(self):
        rows = [row for row in _items() if row["number"] != "12"]
        rows.append({
            "number": "12",
            "not_applicable": "The review was not registered in any register.",
            "human_confirmed": True,
        })
        verification, entries = MOD.parse(_record(rows))
        errors, statuses = MOD.check(verification, entries)
        self.assertEqual([], errors)
        self.assertTrue(all(status == "verified" for status in statuses.values()))
        self.assertEqual(set(), MOD.mechanical_defects(verification, entries))

    def test_addressability_mode_is_unchanged_by_the_na_policy(self):
        """Addressability asserts no compliance, so it owes no N/A policy.

        The sub-gate refuses an addressability record outright rather than reading a
        satisfied human gate off it; that refusal, not this predicate, is what keeps
        a location-only record out of the compliance verdict.
        """
        rows = [
            {"number": number, "not_applicable": "x"}
            for number, _ in MOD.PRISMA_ABSTRACTS
        ]
        verification, entries = MOD.parse(_record(rows, verification="addressability"))
        errors, statuses = MOD.check(verification, entries)
        self.assertEqual([], errors)
        self.assertTrue(all(status == "addressed" for status in statuses.values()))
        self.assertEqual(set(), MOD.mechanical_defects(verification, entries))
        self.assertEqual(0, MOD.unconfirmed_assertions(verification, entries))

    def test_conditional_set_is_a_subset_of_the_official_items(self):
        numbers = {number for number, _ in MOD.PRISMA_ABSTRACTS}
        self.assertTrue(MOD.CONDITIONALLY_APPLICABLE <= numbers)
        # Pinned deliberately: widening this set weakens every mandatory item, so a
        # change here should be a reviewed decision, not an incidental edit.
        self.assertEqual({"12"}, MOD.CONDITIONALLY_APPLICABLE)

    def test_substantiveness_floor_matches_the_42_row_checker(self):
        sibling = load("skills/prisma-flow/scripts/prisma_compliance.py")
        self.assertEqual(sibling.MIN_SUBSTANTIVE_CHARS, MOD.MIN_SUBSTANTIVE_CHARS)


if __name__ == "__main__":
    unittest.main()
