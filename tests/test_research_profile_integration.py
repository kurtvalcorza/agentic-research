from __future__ import annotations

import unittest

from _load import load

ru = load("skills/verify-review/scripts/review_units.py")


class ResearchProfileIntegrationTests(unittest.TestCase):
    def test_new_units_are_registered_with_weights(self):
        self.assertEqual(1, ru.DEFAULT_WEIGHTS["U_grade_current"])
        self.assertEqual(1, ru.DEFAULT_WEIGHTS["U_cochrane"])
        self.assertEqual("grade_profile_current", ru.DERIVED_BY["U_grade_current"])
        self.assertEqual("cochrane_profile", ru.DERIVED_BY["U_cochrane"])

    def test_current_grade_reuses_the_appraisal_identity_rule(self):
        self.assertIn(("grade_profile_current", "rob_record"), ru.APPRAISAL_ROUTES)
        self.assertEqual(
            (("rob_record", "--rob"),),
            ru.CHECK_TABLE["grade_profile_current"]["optional_records"],
        )

    def test_cochrane_profile_activates_its_unit_without_manual_scope_entry(self):
        scope, declared = ru._validated_scope({
            "review_type": "systematic",
            "profile": "cochrane_intervention",
        })
        self.assertTrue(declared)
        self.assertIn("U_cochrane", scope)

    def test_cochrane_profile_augments_existing_frozen_scope(self):
        scope, declared = ru._validated_scope({
            "review_type": "systematic",
            "profile": "cochrane_intervention",
            "units_in_scope": ["U_screen", "U_prisma"],
        })
        self.assertTrue(declared)
        self.assertEqual(["U_screen", "U_prisma", "U_cochrane"], scope)

    def test_cochrane_profile_cannot_be_declared_on_another_review_type(self):
        with self.assertRaises(ru.InputError):
            ru._validated_scope({
                "review_type": "rapid",
                "profile": "cochrane_intervention",
            })

    def test_unknown_profile_fails_closed(self):
        with self.assertRaises(ru.InputError):
            ru._validated_scope({
                "review_type": "systematic",
                "profile": "cochrane-ish",
            })

    def test_profile_unit_is_predicted_by_the_declared_check(self):
        self.assertEqual(
            {"U_cochrane"},
            ru._would_derive("cochrane_profile", {"record": "cochrane.json"}),
        )

    def test_current_grade_unit_is_predicted_with_or_without_rob_record(self):
        for entry in (
            {"record": "grade.json"},
            {"record": "grade.json", "rob_record": "rob.json"},
        ):
            with self.subTest(entry=entry):
                self.assertEqual(
                    {"U_grade_current"},
                    ru._would_derive("grade_profile_current", entry),
                )

    def test_legacy_runner_contract_remains_present(self):
        # Integration is additive. The PRISMA and legacy GRADE registrations from
        # the parent stack must not disappear when profile checks are added.
        for name in (
            "prisma_flow",
            "prisma_checklist",
            "prisma_reporting_checks",
            "grade_profile",
            "rob_appraisal",
        ):
            self.assertIn(name, ru.CHECK_TABLE)


if __name__ == "__main__":
    unittest.main()
