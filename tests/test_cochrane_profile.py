from __future__ import annotations

import copy
import unittest

from _load import load

cp = load("skills/cochrane-intervention/scripts/cochrane_profile.py")


def human(identifier, decision=None, value=None, judgment=None):
    row = {"id": identifier, "actor_type": "human"}
    if decision is not None:
        row["decision"] = decision
    if value is not None:
        row["value"] = value
    if judgment is not None:
        row["judgment"] = judgment
    return row


def valid_record():
    return {
        "schema_version": "1.0",
        "review_type": "systematic",
        "profile": "cochrane_intervention",
        "protocol": {
            "question": "In adults, does intervention A improve outcome O versus control?",
            "planned_comparisons": ["A versus control"],
            "eligibility_criteria": ["Adults", "RCT or eligible NRSI"],
            "outcomes": ["Outcome O"],
            "time_points": ["12 months"],
            "eligible_designs": ["rct", "nrsi"],
            "search_update_plan": "Update before final synthesis.",
            "effect_measures": ["risk ratio"],
            "rob_tools": ["RoB 2", "ROBINS-I"],
            "synthesis_decision_rules": "Meta-analyse only when clinical/statistical pooling is justified.",
            "missing_results_bias_plan": "Assess missing results at synthesis level.",
            "grade_plan": "GRADE each important outcome.",
            "team": [
                {"id": "alice", "actor_type": "human", "roles": ["screening", "extraction"], "expertise": ["systematic review methods"]},
                {"id": "bob", "actor_type": "human", "roles": ["screening", "RoB"], "expertise": ["clinical domain expertise"]},
            ],
            "conflicts_of_interest": ["No relevant conflicts declared by Alice or Bob."],
            "stakeholder_involvement": "Patient/public input considered during outcome prioritisation.",
            "amendment_log": ["No amendments at protocol lock."],
        },
        "search": {
            "sources": [
                {
                    "name": "CENTRAL", "interface": "Cochrane Library", "strategy": "A AND O",
                    "controlled_vocabulary": "Cochrane terms", "free_text": "A; outcome O",
                    "last_searched": "2026-09-04", "coverage": "all available years",
                    "filters_limits": "none",
                },
                {
                    "name": "MEDLINE", "interface": "PubMed", "strategy": "A AND O",
                    "controlled_vocabulary": "MeSH terms", "free_text": "A; outcome O",
                    "last_searched": "2026-09-04", "coverage": "1946-present",
                    "filters_limits": "none",
                },
            ],
            "embase": {"available": False, "searched": False, "justification": "No licensed Embase access."},
            "imported_corpus": False,
            "acquisition_manifest": "not applicable",
        },
        "studies": [
            {"study_id": "S1", "reports": ["R1", "R2"], "primary_report": "R1", "design": "rct"}
        ],
        "screening": [
            {
                "report_id": "R1",
                "reviewer_a": human("alice", decision="include"),
                "reviewer_b": human("bob", decision="include"),
                "reconciled_decision": "include",
                "reconciliation_note": "Agreement.",
                "exclusion_reason": "",
            },
            {
                "report_id": "R2",
                "reviewer_a": human("alice", decision="include"),
                "reviewer_b": human("bob", decision="include"),
                "reconciled_decision": "include",
                "reconciliation_note": "Agreement.",
                "exclusion_reason": "",
            },
        ],
        "extractions": [
            {
                "result_id": "O1", "study_id": "S1", "comparison": "A vs control",
                "outcome": "Outcome O", "outcome_definition": "Binary event",
                "time_point": "12 months", "analysis_population": "intention-to-treat",
                "effect_measure": "risk ratio", "source_location": "R1 p.7",
                "extractor_a": human("alice", value={"events": [10, 20], "n": [100, 100]}),
                "extractor_b": human("bob", value={"events": [10, 20], "n": [100, 100]}),
                "reconciled_value": {"events": [10, 20], "n": [100, 100]},
                "reconciliation_note": "Agreement.",
            }
        ],
        "risk_of_bias": [
            {
                "result_id": "O1", "study_id": "S1", "design": "rct", "instrument": "RoB 2",
                "assessor_a": human("alice", judgment="low"),
                "assessor_b": human("bob", judgment="low"),
                "reconciled_judgment": "low", "reconciliation_note": "Agreement.",
            }
        ],
        "synthesis": {
            "method": "non_meta",
            "prespecified_decision_rule": "Pool only when effect estimates are sufficiently comparable.",
            "rationale": "Only one eligible study, so no meta-analysis was appropriate.",
        },
        "missing_results_bias": [
            {"result_id": "O1", "judgment": "not suspected", "rationale": "Protocol and reported outcomes were compared."}
        ],
        "grade_linkage": {"missing_results_bias_feeds_grade": True},
    }


class CochraneProfileTests(unittest.TestCase):
    def parsed(self, record=None):
        return cp.parse(record or valid_record())

    def test_valid_profile_is_clean(self):
        self.assertEqual([], cp.check(self.parsed()))

    def test_generic_systematic_cannot_accidentally_enter_profile(self):
        r = valid_record()
        r["profile"] = "generic"
        with self.assertRaises(cp.InputError):
            cp.parse(r)

    def test_two_agents_do_not_count_as_two_humans_for_screening(self):
        r = valid_record()
        r["screening"][0]["reviewer_b"]["actor_type"] = "agent"
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("both independent reviewers" in e for e in errors))

    def test_same_person_twice_is_not_independent(self):
        r = valid_record()
        r["screening"][0]["reviewer_b"]["id"] = "alice"
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("must be distinct people" in e for e in errors))

    def test_every_linked_report_requires_full_text_record(self):
        r = valid_record()
        r["screening"] = r["screening"][:1]
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("screening R2" in e for e in errors))

    def test_excluded_full_text_requires_reason(self):
        r = valid_record()
        row = r["screening"][0]
        row["reviewer_a"]["decision"] = "exclude"
        row["reviewer_b"]["decision"] = "exclude"
        row["reconciled_decision"] = "exclude"
        row["exclusion_reason"] = ""
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("requires an exclusion reason" in e for e in errors))

    def test_duplicate_outcome_extraction_requires_two_humans(self):
        r = valid_record()
        r["extractions"][0]["extractor_b"]["actor_type"] = "agent"
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("extraction" in e and "human actors" in e for e in errors))

    def test_rct_routes_to_rob2(self):
        r = valid_record()
        r["risk_of_bias"][0]["instrument"] = "ROBINS-I"
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("must route to RoB 2" in e for e in errors))

    def test_nrsi_routes_to_robins_i_not_nos(self):
        r = valid_record()
        r["studies"][0]["design"] = "nrsi"
        r["risk_of_bias"][0]["design"] = "nrsi"
        r["risk_of_bias"][0]["instrument"] = "Newcastle-Ottawa"
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("must route to ROBINS-I" in e for e in errors))

    def test_missing_rob_for_extracted_result_fails(self):
        r = valid_record()
        r["risk_of_bias"] = []
        # Empty is malformed rather than a clean profile.
        with self.assertRaises(cp.InputError):
            cp.parse(r)

    def test_required_search_sources_fail_closed_at_method_layer(self):
        r = valid_record()
        r["search"]["sources"] = [s for s in r["search"]["sources"] if s["name"] != "CENTRAL"]
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("CENTRAL is required" in e for e in errors))

    def test_available_embase_must_be_searched(self):
        r = valid_record()
        r["search"]["embase"] = {"available": True, "searched": False, "justification": ""}
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("available but was not documented as searched" in e for e in errors))

    def test_unavailable_embase_needs_justification(self):
        r = valid_record()
        r["search"]["embase"]["justification"] = ""
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("unavailability requires" in e for e in errors))

    def test_imported_corpus_requires_manifest(self):
        r = valid_record()
        r["search"]["imported_corpus"] = True
        r["search"]["acquisition_manifest"] = ""
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("imported/pre-collected corpora" in e for e in errors))

    def test_report_cannot_link_to_two_studies(self):
        r = valid_record()
        r["studies"].append({"study_id": "S2", "reports": ["R2"], "primary_report": "R2", "design": "rct"})
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("linked to more than one study" in e for e in errors))

    def test_missing_results_bias_is_first_class_and_required(self):
        r = valid_record()
        r["missing_results_bias"] = [{"result_id": "OTHER", "judgment": "unclear", "rationale": "No data."}]
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("O1" in e and "assessment is required" in e for e in errors))

    def test_missing_results_bias_must_feed_grade(self):
        r = valid_record()
        r["grade_linkage"]["missing_results_bias_feeds_grade"] = False
        errors = cp.check(self.parsed(r))
        self.assertTrue(any("must explicitly feed" in e for e in errors))

    def test_unknown_field_is_malformed(self):
        r = valid_record()
        r["typo"] = True
        with self.assertRaises(cp.InputError):
            cp.parse(r)

    def test_malformed_actor_type_is_not_coerced(self):
        r = valid_record()
        r["screening"][0]["reviewer_a"]["actor_type"] = True
        with self.assertRaises(cp.InputError):
            cp.parse(r)

    def test_parse_does_not_mutate_input(self):
        r = valid_record()
        before = copy.deepcopy(r)
        cp.parse(r)
        self.assertEqual(before, r)


if __name__ == "__main__":
    unittest.main()
