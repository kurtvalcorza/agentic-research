from __future__ import annotations

import unittest

from _load import load

pc = load("skills/prisma-flow/scripts/prisma_compliance.py")


def rows(*, evidence=True, confirmed=True):
    out = []
    for _, number, _ in pc.PRISMA_2020:
        row = {"number": number, "location": f"Manuscript section for {number}"}
        if evidence:
            row["evidence"] = f"Reporting requirement {number} is substantively described."
        if confirmed is not None:
            row["human_confirmed"] = confirmed
        out.append(row)
    return out


class PrismaComplianceTests(unittest.TestCase):
    def test_42_rows_are_modelled(self):
        self.assertEqual(42, len(pc.PRISMA_2020))

    def test_complete_evidence_bearing_record_passes(self):
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": rows()})
        self.assertEqual([], pc.check(entries))

    def test_location_only_cannot_look_compliant(self):
        entries = pc.parse({
            "schema_version": "1.0", "variant": "prisma_2020",
            "items": rows(evidence=False, confirmed=None),
        })
        errors = pc.check(entries)
        self.assertEqual(84, len(errors))
        self.assertTrue(any("no substantive reporting evidence" in e for e in errors))
        self.assertTrue(any("not human-confirmed" in e for e in errors))

    def test_partial_record_fails(self):
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": rows()[:-1]})
        errors = pc.check(entries)
        self.assertTrue(any("item 27" in e and "missing" in e for e in errors))

    def test_not_applicable_needs_human_confirmation_but_not_evidence(self):
        data = rows()
        data[-1] = {
            "number": "27",
            "not_applicable": "No additional data/code/materials were produced.",
            "human_confirmed": True,
        }
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})
        self.assertEqual([], pc.check(entries))

    def test_not_applicable_without_human_gate_fails(self):
        data = rows()
        data[-1] = {"number": "27", "not_applicable": "Nothing additional."}
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})
        errors = pc.check(entries)
        self.assertTrue(any("item 27" in e and "not human-confirmed" in e for e in errors))

    def test_location_and_na_are_mutually_exclusive(self):
        with self.assertRaises(pc.InputError):
            pc.parse({
                "schema_version": "1.0", "variant": "prisma_2020",
                "items": [{"number": "1", "location": "Title", "not_applicable": "no"}],
            })

    def test_wrong_variant_is_malformed(self):
        with self.assertRaises(pc.InputError):
            pc.parse({"schema_version": "1.0", "variant": "prisma_scr", "items": rows()})

    def test_unknown_item_field_is_malformed(self):
        data = rows()
        data[0]["typo"] = True
        with self.assertRaises(pc.InputError):
            pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})

    def test_blanket_not_applicable_record_fails(self):
        """F24-02 / V27-01: a 42-row record declaring every item not-applicable
        must not exit clean, even when every row is human-confirmed."""
        data = [{"number": number, "not_applicable": "n", "human_confirmed": True}
                for _, number, _ in pc.PRISMA_2020]
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})
        errors = pc.check(entries)
        self.assertTrue(errors)
        # Every mandatory item (i.e. every item outside CONDITIONALLY_APPLICABLE)
        # must be rejected for asserting N/A at all, not merely for a short
        # justification.
        self.assertTrue(any("not a legitimate disposition" in e and "item 1 " in e for e in errors))

    def test_one_character_evidence_fails(self):
        """F24-02: 'x' is not substantive evidence, even paired with a located row
        and human_confirmed=True."""
        data = [{"number": number, "location": "Manuscript, somewhere",
                  "evidence": "x", "human_confirmed": True}
                for _, number, _ in pc.PRISMA_2020]
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})
        errors = pc.check(entries)
        self.assertEqual(42, len(errors))
        self.assertTrue(all("too short to be substantive" in e for e in errors))

    def test_mandatory_item_cannot_be_marked_not_applicable(self):
        data = rows()
        data[0] = {"number": "1", "not_applicable": "Not applicable to this review.",
                   "human_confirmed": True}
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})
        errors = pc.check(entries)
        self.assertTrue(any("item 1 " in e and "not a legitimate disposition" in e for e in errors))

    def test_conditionally_applicable_item_permits_not_applicable(self):
        data = [row for row in rows() if row["number"] != "13f"] + [{
            "number": "13f", "not_applicable": "No sensitivity analyses were performed.",
            "human_confirmed": True,
        }]
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})
        errors = pc.check(entries)
        self.assertFalse(any("item 13f" in e for e in errors))

    def test_evidence_restating_the_location_is_rejected(self):
        data = rows()
        data[0] = {"number": "1", "location": "Manuscript title page",
                   "evidence": "Manuscript title page", "human_confirmed": True}
        entries = pc.parse({"schema_version": "1.0", "variant": "prisma_2020", "items": data})
        errors = pc.check(entries)
        self.assertTrue(any("item 1 " in e and "merely restates" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
