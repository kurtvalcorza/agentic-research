from __future__ import annotations

import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

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
                "appraised_result": "All-cause mortality at 12 months",
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
                        "unit": "proportion",
                        "direction": "below",
                        "rationale": "Prespecified threshold for an important mortality benefit.",
                    }
                ],
                "target_of_certainty": "true absolute mortality effect is beyond the threshold for important benefit",
                "target_threshold": {
                    "threshold_label": "important benefit",
                    "effect_basis": "absolute",
                    "claim": "meets",
                    "effect_unit": "proportion",
                },
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


def _rob_study(sid: str, *, confirmed=True):
    row = {
        "id": sid,
        "design": "rct",
        "instrument": "rob2",
        "result_assessed": "All-cause mortality at 12 months",
        "domains": {
            "randomization": "low",
            "deviations": "low",
            "missing_data": "low",
            "measurement": "low",
            "selection_of_result": "low",
        },
        "overall": "low",
    }
    if confirmed:
        row["confirmed_by"] = "Human reviewer"
        row["confirmed_at"] = "2026-09-04"
    return row


def valid_appraisal():
    return {
        "schema_version": "1.0",
        "studies": [_rob_study("S1"), _rob_study("S2")],
    }


def checked(record=None, appraisal=None):
    parsed, warnings = gp.parse(record or valid_record())
    app = gp.parse_appraisal(appraisal or valid_appraisal())
    return parsed, warnings, gp.check(parsed, app)


class CurrentGradeProfileTests(unittest.TestCase):
    def test_valid_current_profile_is_clean(self):
        record, warnings, errors = checked()
        self.assertEqual([], warnings)
        self.assertEqual([], errors)

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

    def test_structured_target_threshold_is_required(self):
        r = valid_record()
        del r["results"][0]["target_threshold"]
        with self.assertRaises(gp.InputError):
            gp.parse(r)

    def test_target_threshold_must_name_declared_threshold(self):
        r = valid_record()
        r["results"][0]["target_threshold"]["threshold_label"] = "not declared"
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
        errors = gp.check(record, gp.parse_appraisal(valid_appraisal()))
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
        r["results"][0]["target_threshold"]["effect_basis"] = "continuous"
        record, _ = gp.parse(r)
        errors = gp.check(record, gp.parse_appraisal(valid_appraisal()))
        self.assertTrue(any("continuous outcome missing" in e for e in errors))
        self.assertTrue(any("continuous_interval" in e for e in errors))

    def test_minus_three_is_accepted_with_justification(self):
        r = valid_record()
        r["results"][0]["domains"]["risk_of_bias"] = {
            "rating": -3,
            "note": "Extremely serious limitations.",
            "justification": "All contributing evidence is critically compromised for this target.",
            "basis": "confirmed_rob",
        }
        r["results"][0]["final"] = "very_low"
        _, _, errors = checked(r)
        self.assertEqual([], errors)

    def test_minus_three_requires_explicit_justification(self):
        r = valid_record()
        r["results"][0]["domains"]["risk_of_bias"]["rating"] = -3
        r["results"][0]["final"] = "very_low"
        record, _ = gp.parse(r)
        errors = gp.check(record, gp.parse_appraisal(valid_appraisal()))
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
        self.assertEqual([], gp.check(record, gp.parse_appraisal(valid_appraisal())))

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
        errors = gp.check(record, gp.parse_appraisal(valid_appraisal()))
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
        _, _, errors = checked(r)
        self.assertEqual([], errors)

    def test_strict_systematic_requires_confirmed_rob_basis(self):
        r = valid_record()
        r["results"][0]["domains"]["risk_of_bias"]["basis"] = "heuristic"
        record, _ = gp.parse(r)
        errors = gp.check(record, gp.parse_appraisal(valid_appraisal()))
        self.assertTrue(any("requires risk_of_bias basis confirmed_rob" in e for e in errors))

    def test_confirmed_rob_basis_requires_external_appraisal(self):
        record, _ = gp.parse(valid_record())
        errors = gp.check(record)
        self.assertTrue(any("requires --rob appraisal evidence" in e for e in errors))

    def test_every_cited_study_must_resolve_at_exact_result(self):
        appraisal = valid_appraisal()
        appraisal["studies"] = appraisal["studies"][:1]
        record, _ = gp.parse(valid_record())
        errors = gp.check(record, gp.parse_appraisal(appraisal))
        self.assertTrue(any("study 'S2' does not resolve" in e for e in errors))

    def test_unconfirmed_appraisal_cannot_back_current_grade(self):
        appraisal = valid_appraisal()
        appraisal["studies"][1] = _rob_study("S2", confirmed=False)
        record, _ = gp.parse(valid_record())
        errors = gp.check(record, gp.parse_appraisal(appraisal))
        self.assertTrue(any("study 'S2'" in e and "not human-confirmed" in e for e in errors))

    def test_design_mix_is_reconciled_to_resolved_appraisals(self):
        r = valid_record()
        r["results"][0]["design_mix"] = {"rct": 1, "nrsi": 1}
        r["results"][0]["starting_level"] = "low"
        r["results"][0]["final"] = "low"
        record, _ = gp.parse(r)
        errors = gp.check(record, gp.parse_appraisal(valid_appraisal()))
        self.assertTrue(any("design_mix" in e and "resolved appraisal designs" in e for e in errors))

    def test_interval_wholly_opposite_declared_target_is_flagged(self):
        r = valid_record()
        effect = r["results"][0]["effect"]
        effect["absolute_effect"] = -0.001
        effect["absolute_interval"] = {"lower": -0.002, "upper": -0.0005}
        record, _ = gp.parse(r)
        errors = gp.check(record, gp.parse_appraisal(valid_appraisal()))
        self.assertTrue(any("lies wholly on the opposite side" in e for e in errors))

    def test_threshold_crossing_is_not_inferred_as_a_contradiction(self):
        r = valid_record()
        r["results"][0]["effect"]["absolute_interval"] = {"lower": -0.03, "upper": -0.01}
        _, _, errors = checked(r)
        self.assertFalse(any("opposite side" in e for e in errors))

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
        self.assertIn("important benefit below -0.02 proportion", rendered)
        self.assertIn("High certainty for the declared target", rendered)

    def test_cli_with_matching_rob_passes_strict(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            record_path = root / "grade.json"
            rob_path = root / "rob.json"
            record_path.write_text(json.dumps(valid_record()), encoding="utf-8")
            rob_path.write_text(json.dumps(valid_appraisal()), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(
                sys, "argv", ["grade_profile_current.py", str(record_path), "--rob", str(rob_path), "--strict"]
            ), redirect_stdout(out), redirect_stderr(err):
                code = gp.main()
        self.assertEqual(0, code, msg=out.getvalue() + err.getvalue())
        self.assertIn("checks passed", out.getvalue())


class ThresholdUnitsMustBeBoundBeforeComparisonTests(unittest.TestCase):
    """Negative controls for F26-06.

    ``decision_thresholds[].unit`` was required but never read: the gate compared
    ``threshold.value`` directly against the effect interval, and the effect record
    carries no scale of its own. Numerically equivalent representations therefore
    produced opposite outcomes, so the F26-03 closure could validate the wrong
    target relation while claiming the comparison was mechanically decidable.
    """

    def _record(self, *, threshold_unit, effect_unit, value, interval, claim="meets",
                direction="below"):
        r = valid_record()
        result = r["results"][0]
        result["decision_thresholds"][0]["unit"] = threshold_unit
        result["decision_thresholds"][0]["value"] = value
        result["decision_thresholds"][0]["direction"] = direction
        result["effect"]["absolute_interval"] = {"lower": interval[0], "upper": interval[1]}
        result["target_threshold"]["effect_unit"] = effect_unit
        result["target_threshold"]["claim"] = claim
        return r

    def _check(self, record):
        parsed, _ = gp.parse(record)
        return gp.check(parsed, gp.parse_appraisal(valid_appraisal()))

    def test_effect_unit_is_required(self):
        r = valid_record()
        del r["results"][0]["target_threshold"]["effect_unit"]
        with self.assertRaises(gp.InputError):
            gp.parse(r)

    def test_the_reviewers_falsifier_no_longer_reads_as_met(self):
        """A proportion interval against a per-1000 threshold.

        Raw numbers say 0.03 < 20, i.e. 'meets'. On a common scale the interval is
        [10, 30] per 1000, which crosses 20 — so the claim is not established and
        the gate must not confirm it.
        """
        r = self._record(
            threshold_unit="per 1000", effect_unit="proportion",
            value=20, interval=(0.01, 0.03), claim="meets", direction="below",
        )
        parsed, _ = gp.parse(r)
        self.assertEqual(0.02, gp._threshold_value_on_effect_scale(parsed["results"][0]))
        self.assertEqual("crosses", gp._threshold_position(parsed["results"][0]))

    def test_conversion_catches_a_target_claim_that_is_actually_contradicted(self):
        # [0.03, 0.05] proportion is wholly above 20 per 1000 (= 0.02), so a
        # 'below' claim is contradicted. Without conversion, 0.05 < 20 would have
        # made this look satisfied.
        r = self._record(
            threshold_unit="per 1000", effect_unit="proportion",
            value=20, interval=(0.03, 0.05), claim="meets", direction="below",
        )
        errors = self._check(r)
        self.assertTrue(any("lies wholly on the opposite side" in e for e in errors), errors)
        self.assertTrue(any("0.02" in e for e in errors), errors)

    def test_equivalent_representations_agree(self):
        """The same quantity on two scales must reach the same verdict."""
        as_proportion = self._record(
            threshold_unit="proportion", effect_unit="proportion",
            value=0.02, interval=(0.01, 0.03),
        )
        as_per_1000 = self._record(
            threshold_unit="per 1000", effect_unit="proportion",
            value=20, interval=(0.01, 0.03),
        )
        parsed_a, _ = gp.parse(as_proportion)
        parsed_b, _ = gp.parse(as_per_1000)
        self.assertEqual(
            gp._threshold_position(parsed_a["results"][0]),
            gp._threshold_position(parsed_b["results"][0]),
        )

    def test_percentage_points_convert(self):
        r = self._record(
            threshold_unit="percentage points", effect_unit="proportion",
            value=2, interval=(0.01, 0.03),
        )
        parsed, _ = gp.parse(r)
        self.assertAlmostEqual(0.02, gp._threshold_value_on_effect_scale(parsed["results"][0]))

    def test_unconvertible_units_fail_closed(self):
        """A ratio and a risk difference are not the same kind of quantity.

        Converting them needs a baseline risk, not a factor, so the check must
        report the claim as undecidable rather than compare the raw numbers.
        """
        r = self._record(
            threshold_unit="risk ratio", effect_unit="proportion",
            value=0.9, interval=(0.01, 0.03),
        )
        errors = self._check(r)
        self.assertTrue(any("not mechanically decidable" in e for e in errors), errors)

    def test_an_unrecognised_unit_is_not_silently_compared(self):
        r = self._record(
            threshold_unit="widgets per fortnight", effect_unit="proportion",
            value=0.02, interval=(0.01, 0.03),
        )
        errors = self._check(r)
        self.assertTrue(any("not mechanically decidable" in e for e in errors), errors)
        parsed, _ = gp.parse(r)
        self.assertIsNone(gp._threshold_value_on_effect_scale(parsed["results"][0]))

    def test_identical_units_need_no_conversion_table_entry(self):
        """Units outside the risk-scale table still compare when they match exactly.

        This is what keeps continuous and relative measures working: 'mean
        difference in points' is not convertible to anything, but it is comparable
        with itself.
        """
        r = self._record(
            threshold_unit="mean difference in points",
            effect_unit="mean difference in points",
            value=0.02, interval=(0.01, 0.03),
        )
        parsed, _ = gp.parse(r)
        self.assertEqual(0.02, gp._threshold_value_on_effect_scale(parsed["results"][0]))
        self.assertEqual([], [e for e in self._check(r) if "decidable" in e])

    def test_unit_spelling_is_folded_but_meaning_is_not(self):
        for spelling in ("Per 1000", "per_1000", "  per 1000  "):
            with self.subTest(spelling=spelling):
                r = self._record(
                    threshold_unit=spelling, effect_unit="proportion",
                    value=20, interval=(0.01, 0.03),
                )
                parsed, _ = gp.parse(r)
                self.assertAlmostEqual(
                    0.02, gp._threshold_value_on_effect_scale(parsed["results"][0])
                )

    def test_narrative_basis_still_declares_a_unit_but_is_not_compared(self):
        r = valid_record()
        r["results"][0]["target_threshold"]["effect_basis"] = "narrative"
        parsed, _ = gp.parse(r)
        self.assertIsNone(gp._threshold_position(parsed["results"][0]))

    def test_narrative_basis_is_exempt_from_unit_reconciliation(self):
        """A narrative claim compares nothing, so unrelated units are not a defect.

        This goes through check(), not _threshold_position alone: the regression it
        pins was in _check_targets, which called the reconciliation unconditionally
        while the adjacent interval-presence check already exempted narrative. The
        two unit strings here are deliberately unrelated and unconvertible — a
        fixture that reused one string for both would mask exactly this bug.
        """
        r = valid_record()
        result = r["results"][0]
        result["target_threshold"]["effect_basis"] = "narrative"
        result["target_threshold"]["effect_unit"] = "narrative summary"
        result["decision_thresholds"][0]["unit"] = "risk difference"
        parsed, _ = gp.parse(r)
        errors = gp.check(parsed, gp.parse_appraisal(valid_appraisal()))
        self.assertEqual([], [e for e in errors if "mechanically decidable" in e], errors)
        self.assertIsNone(gp._threshold_position(parsed["results"][0]))

    def test_a_non_narrative_basis_is_still_reconciled(self):
        """The narrative exemption must not become a general escape hatch."""
        r = valid_record()
        result = r["results"][0]
        result["target_threshold"]["effect_basis"] = "absolute"
        result["target_threshold"]["effect_unit"] = "narrative summary"
        result["decision_thresholds"][0]["unit"] = "risk difference"
        parsed, _ = gp.parse(r)
        errors = gp.check(parsed, gp.parse_appraisal(valid_appraisal()))
        self.assertTrue(any("mechanically decidable" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
