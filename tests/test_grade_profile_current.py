from __future__ import annotations

import unittest

from _load import load

gp = load("skills/validate-evidence/scripts/grade_profile_current.py")


def valid_record():
    return {
        "schema_version": "2.0",
        "review_type": "systematic",
        "synthesis_mode": "outcome",
        "grade_guidance": {
            "source": "GRADE Book",
            "profile": "current",
            "as_of": "2026-09-04",
        },
        "results": [
            {
                "id": "O1",
                "label": "Mortality at 12 months",
                "outcome": "All-cause mortality",
                "time_point": "12 months",
                "study_ids": ["S1", "S2"],
                "design_mix": {"rct": 2},
                "starting_level": "high",
                "effect": {
                    "type": "dichotomous",
                    "measure": "risk ratio",
                    "relative_estimate": 0.8,
                    "relative_interval": {"lower": 0.7, "upper": 0.92},
                    "baseline_risk": 0.20,
                    "absolute_effect": -0.04,
                    "absolute_interval": {"lower": -0.06, "upper": -0.016},
                    "participants": 1200,
                    "studies": 2,
                },
                "decision_thresholds": [
                    {
                        "label": "important benefit",
                        "value": -0.02,
                        "unit": "risk difference",
                        "direction": "below",
                        "rationale": "Prespecified threshold for an important mortality benefit.",
                    }
                ],
                "target_of_certainty": "true absolute mortality effect is beyond the threshold for important benefit",
                "domains": {
                    "risk_of_bias": {"rating": 0, "note": "Confirmed RoB appraisals show no serious concern.", "basis": "confirmed_rob"},
                    "inconsistency": {"rating": 0, "note": "Effects are compatible across studies."},
                    "indirectness": {"rating": 0, "note": "Population, intervention and outcome match the target."},
                    "imprecision": {"rating": 0, "note": "Interval remains beyond the prespecified threshold."},
                    "dissemination_bias": {"rating": 0, "note": "No important dissemination-bias signal identified."},
                },
                "domain_overlap": [],
                "upgrades": {},
                "final": "high",
                "certainty_statement": "High certainty that the true effect exceeds the prespecified threshold for important benefit.",
                "footnotes": ["Decision threshold was prespecified in the protocol."],
            }
        ],
    }


class CurrentGradeProfileTests(unittest.TestCase):
    def test_valid_current_profile_is_clean(self):
        record, warnings = gp.parse(valid_record())
        self.assertEqual([], warnings)
        self.assertEqual([], gp.check(record))

    def test_guidance_provenance_is_required(self):
        r = valid_record()
        del r["grade_guidance"]
        with self.assertRaises(gp.InputError):
            gp.parse(r)

    def test_target_of_certainty_is_required(self):
        r = valid_record()
        del r["results"][0]["target_of_certainty"]
        with self.assertRaises(gp.InputError):
            gp.parse(r)

    def test_decision_thresholds_cannot_be_empty(self):
        r = valid_record()
        r["results"][0]["decision_thresholds"] = []
        with self.assertRaises(gp.InputError):
            gp.parse(r)

    def test_dichotomous_effect_requires_baseline_and_absolute_effect(self):
        r = valid_record()
        del r["results"][0]["effect"]["baseline_risk"]
        del r["results"][0]["effect"]["absolute_effect"]
        record, _ = gp.parse(r)
        errors = gp.check(record)
        self.assertTrue(any("baseline_risk" in e and "absolute_effect" in e for e in errors))

    def test_continuous_effect_requires_estimate_and_interval(self):
        r = valid_record()
        effect = r["results"][0]["effect"]
        r["results"][0]["effect"] = {
            "type": "continuous",
            "measure": "mean difference",
            "participants": effect["participants"],
            "studies": effect["studies"],
        }
        record, _ = gp.parse(r)
        errors = gp.check(record)
        self.assertTrue(any("continuous outcome missing" in e for e in errors))

    def test_minus_three_is_accepted_with_justification(self):
        r = valid_record()
        r["results"][0]["domains"]["risk_of_bias"] = {
            "rating": -3,
            "note": "Extremely serious limitations.",
            "justification": "All contributing evidence is critically compromised for this target.",
            "basis": "confirmed_rob",
        }
        r["results"][0]["final"] = "very_low"
        record, _ = gp.parse(r)
        self.assertEqual([], gp.check(record))

    def test_minus_three_requires_explicit_justification(self):
        r = valid_record()
        r["results"][0]["domains"]["risk_of_bias"]["rating"] = -3
        r["results"][0]["final"] = "very_low"
        record, _ = gp.parse(r)
        errors = gp.check(record)
        self.assertTrue(any("rating -3 requires" in e for e in errors))

    def test_half_step_is_malformed(self):
        r = valid_record()
        r["results"][0]["domains"]["imprecision"]["rating"] = -0.5
        with self.assertRaises(gp.InputError):
            gp.parse(r)

    def test_publication_bias_alias_migrates(self):
        r = valid_record()
        domains = r["results"][0]["domains"]
        domains["publication_bias"] = domains.pop("dissemination_bias")
        record, warnings = gp.parse(r)
        self.assertIn("dissemination_bias", record["results"][0]["domains"])
        self.assertTrue(any("publication_bias" in warning for warning in warnings))
        self.assertEqual([], gp.check(record))

    def test_both_bias_names_are_malformed(self):
        r = valid_record()
        r["results"][0]["domains"]["publication_bias"] = {
            "rating": 0, "note": "legacy duplicate"
        }
        with self.assertRaises(gp.InputError):
            gp.parse(r)

    def test_explicit_overlap_blocks_double_downgrade(self):
        r = valid_record()
        domains = r["results"][0]["domains"]
        domains["inconsistency"]["rating"] = -1
        domains["imprecision"]["rating"] = -1
        r["results"][0]["domain_overlap"] = [
            {
                "domains": ["inconsistency", "imprecision"],
                "shared_cause": "heterogeneity widens the interval across the threshold",
                "accounted_in": "imprecision",
            }
        ]
        r["results"][0]["final"] = "low"
        record, _ = gp.parse(r)
        errors = gp.check(record)
        self.assertTrue(any("double-counts" in e for e in errors))

    def test_overlap_is_clean_when_accounted_once(self):
        r = valid_record()
        domains = r["results"][0]["domains"]
        domains["imprecision"]["rating"] = -1
        r["results"][0]["domain_overlap"] = [
            {
                "domains": ["inconsistency", "imprecision"],
                "shared_cause": "heterogeneity widens the interval across the threshold",
                "accounted_in": "imprecision",
            }
        ]
        r["results"][0]["final"] = "moderate"
        record, _ = gp.parse(r)
        self.assertEqual([], gp.check(record))

    def test_strict_systematic_requires_confirmed_rob_basis(self):
        r = valid_record()
        r["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        record, _ = gp.parse(r)
        errors = gp.check(record)
        self.assertTrue(any("requires risk_of_bias basis confirmed_rob" in e for e in errors))

    def test_no_cross_result_aggregate_key(self):
        r = valid_record()
        r["overall_certainty"] = "high"
        with self.assertRaises(gp.InputError):
            gp.parse(r)

    def test_sof_contains_effect_and_threshold_context(self):
        record, warnings = gp.parse(valid_record())
        rendered = gp.render(record, [], warnings, "record.json")
        self.assertIn("Summary of Findings", rendered)
        self.assertIn("baseline=0.2", rendered)
        self.assertIn("important benefit below -0.02 risk difference", rendered)
        self.assertIn("High certainty for the declared target", rendered)


if __name__ == "__main__":
    unittest.main()
