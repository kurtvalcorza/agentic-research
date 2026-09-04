from __future__ import annotations

import unittest

from _load import load

pf = load("skills/prisma-flow/scripts/prisma_updated_flow.py")


def db_only():
    return {
        "schema_version": "1.0",
        "variant": "updated_databases_registers",
        "identified_databases": {"MEDLINE": 100},
        "identified_registers": {"CENTRAL": 20},
        "duplicates_removed": 20,
        "removed_other_reasons": 0,
        "records_screened": 100,
        "records_excluded_title_abstract": 70,
        "reports_sought": 30,
        "reports_not_retrieved": 2,
        "reports_assessed": 28,
        "reports_excluded": {"wrong population": 18},
        "new_studies_included_databases": 10,
        "previous_studies_included": 15,
        "previous_reports_included": 18,
        "new_studies_included": 10,
        "new_reports_included": 12,
        "updated_studies_included": 25,
        "updated_reports_included": 30,
    }


def with_other():
    r = db_only()
    r["variant"] = "updated_databases_registers_other_methods"
    r.update({
        "identified_other": {"citation searching": 6},
        "other_reports_sought": 6,
        "other_reports_not_retrieved": 1,
        "other_reports_assessed": 5,
        "other_reports_excluded": {"wrong outcome": 2},
        "new_studies_included_other": 3,
        "new_studies_included": 13,
        "new_reports_included": 15,
        "updated_studies_included": 28,
        "updated_reports_included": 33,
    })
    return r


class PrismaUpdatedFlowTests(unittest.TestCase):
    def test_databases_registers_variant_reconciles(self):
        self.assertEqual([], pf.check(pf.parse(db_only())))

    def test_other_methods_variant_reconciles(self):
        self.assertEqual([], pf.check(pf.parse(with_other())))

    def test_variant_is_explicit_and_required(self):
        r = db_only()
        del r["variant"]
        with self.assertRaises(pf.CountError):
            pf.parse(r)

    def test_database_only_variant_rejects_other_arm_fields(self):
        r = db_only()
        r["identified_other"] = {"citation searching": 0}
        with self.assertRaises(pf.CountError):
            pf.parse(r)

    def test_other_variant_requires_complete_other_arm(self):
        r = with_other()
        del r["other_reports_assessed"]
        with self.assertRaises(pf.CountError):
            pf.parse(r)

    def test_previous_plus_new_studies_must_equal_updated_total(self):
        r = db_only()
        r["updated_studies_included"] = 99
        errors = pf.check(pf.parse(r))
        self.assertTrue(any("updated_studies_included" in e for e in errors))

    def test_previous_plus_new_reports_must_equal_updated_total(self):
        r = db_only()
        r["updated_reports_included"] = 99
        errors = pf.check(pf.parse(r))
        self.assertTrue(any("updated_reports_included" in e for e in errors))

    def test_new_reports_cannot_be_fewer_than_new_studies(self):
        r = db_only()
        r["new_reports_included"] = 5
        r["updated_reports_included"] = 23
        errors = pf.check(pf.parse(r))
        self.assertTrue(any("cannot be fewer" in e for e in errors))

    def test_wrong_database_arithmetic_fails(self):
        r = db_only()
        r["records_screened"] = 101
        errors = pf.check(pf.parse(r))
        self.assertTrue(any("records_screened" in e for e in errors))

    def test_wrong_other_arm_arithmetic_fails(self):
        r = with_other()
        r["other_reports_assessed"] = 4
        errors = pf.check(pf.parse(r))
        self.assertTrue(any("other-methods arm" in e for e in errors))

    def test_unknown_field_is_malformed(self):
        r = db_only()
        r["typo"] = 1
        with self.assertRaises(pf.CountError):
            pf.parse(r)

    def test_quoted_count_is_malformed(self):
        r = db_only()
        r["records_screened"] = "100"
        with self.assertRaises(pf.CountError):
            pf.parse(r)


if __name__ == "__main__":
    unittest.main()
