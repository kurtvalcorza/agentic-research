"""Coverage for skills/verify-review/scripts/review_units.py.

This is the script that decides whether a review may be reported VERIFIED, so its
fail-closed behaviour matters more than any other check's. It had no tests until now.
Standard library only.
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

ru = load("skills/verify-review/scripts/review_units.py")

FLOOR = {"U_cite_external": 0, "U_cite_internal": 0}
CLEAN_CONSISTENCY = {"score": 90, "critical_breaks": 0}
NO_GATES = {"H_rob": 0, "H_screen_adj": 0, "H_cite_manual": 0, "H_numeric": 0}


def verdict(data):
    return ru.verdict(data, ru.DEFAULT_WEIGHTS, ru.CEILING)


def systematic(units=None, gates=None, **extra):
    """A fully-scoped systematic review record."""
    scope = ["U_cite_external", "U_cite_internal", "U_consistency", "U_screen",
             "U_extract", "U_prisma", "U_grade", "U_rob_trace", "U_checklist"]
    u = {k: 0 for k in scope if k != "U_consistency"}
    if units:
        u.update(units)
    d = {"schema_version": ru.SCHEMA_VERSION,
         "units_in_scope": scope, "units": u, "consistency": CLEAN_CONSISTENCY,
         "gates": dict(NO_GATES, **(gates or {}))}
    d.update(extra)
    return d


class TestNewUnitsRegistered(unittest.TestCase):
    def test_new_units_have_weight_one(self):
        self.assertEqual(ru.DEFAULT_WEIGHTS["U_rob_trace"], 1)
        self.assertEqual(ru.DEFAULT_WEIGHTS["U_checklist"], 1)

    def test_citation_integrity_still_dominates_routing(self):
        self.assertEqual(ru.DEFAULT_WEIGHTS["U_cite_external"], 3)

    def test_universal_floor_is_not_extended(self):
        """The new units are review-type dependent, so they belong in the declared
        scope, not the floor every review type must satisfy."""
        self.assertEqual(ru.UNIVERSAL_FLOOR,
                         ("U_cite_external", "U_cite_internal", "U_consistency"))

    def test_h_rob_remains_a_gate(self):
        self.assertIn("H_rob", ru.GATE_KEYS)


class TestVerifiedRequiresEverything(unittest.TestCase):
    def test_complete_clean_systematic_review_verifies(self):
        self.assertEqual(verdict(systematic())["state"], "VERIFIED")

    def test_outstanding_grade_unit_continues(self):
        r = verdict(systematic({"U_grade": 2}))
        self.assertEqual(r["state"], "CONTINUE")
        self.assertFalse(r["auto_units_zero"])

    def test_outstanding_rob_trace_continues(self):
        self.assertEqual(verdict(systematic({"U_rob_trace": 1}))["state"], "CONTINUE")

    def test_outstanding_checklist_continues(self):
        self.assertEqual(verdict(systematic({"U_checklist": 15}))["state"], "CONTINUE")

    def test_missing_in_scope_unit_blocks_verification(self):
        """The headline fail-closed property: an applicable check that was never
        reported is MISSING, not zero."""
        d = systematic()
        del d["units"]["U_checklist"]
        r = verdict(d)
        self.assertIn("U_checklist", r["missing_units"])
        self.assertNotEqual(r["state"], "VERIFIED")

    def test_missing_unit_is_not_mislabelled_plateau(self):
        d = systematic(history=[5, 5, 5, 5])
        del d["units"]["U_grade"]
        self.assertEqual(verdict(d)["state"], "CONTINUE")

    def test_no_routing_while_a_unit_is_missing(self):
        d = systematic({"U_cite_external": 4})
        del d["units"]["U_grade"]
        self.assertIsNone(verdict(d)["dominant_unit"])


class TestScopeResolution(unittest.TestCase):
    def test_narrative_review_omits_checklist_without_penalty(self):
        """An inapplicable unit is ABSENT, not zero-to-achieve."""
        d = {"schema_version": ru.SCHEMA_VERSION,
             "units_in_scope": ["U_cite_external", "U_cite_internal", "U_consistency"],
             "units": dict(FLOOR), "consistency": CLEAN_CONSISTENCY, "gates": dict(NO_GATES)}
        r = verdict(d)
        self.assertEqual(r["state"], "VERIFIED")
        self.assertEqual(r["missing_units"], [])

    def test_unknown_unit_in_scope_rejected(self):
        d = systematic()
        d["units_in_scope"].append("U_vibes")
        with self.assertRaises(ru.InputError):
            verdict(d)

    def test_unknown_unit_in_units_rejected(self):
        d = systematic()
        d["units"]["U_vibes"] = 0
        with self.assertRaises(ru.InputError):
            verdict(d)


class TestFailClosed(unittest.TestCase):
    def test_unknown_root_key_is_rejected(self):
        d = systematic()
        d["critical_break"] = 2
        with self.assertRaisesRegex(ru.InputError, "critical_break"):
            verdict(d)

    def test_misspelled_consistency_key_is_rejected(self):
        d = systematic()
        d["consistency"] = {"score": 82, "critical_break": 2}
        with self.assertRaisesRegex(ru.InputError, "critical_break"):
            verdict(d)

    def test_unversioned_legacy_record_is_rejected(self):
        d = systematic()
        del d["schema_version"]
        with self.assertRaisesRegex(ru.InputError, "schema_version"):
            verdict(d)

    def test_unknown_schema_version_is_rejected(self):
        with self.assertRaisesRegex(ru.InputError, "schema_version"):
            verdict(systematic(schema_version="0.9"))

    def test_empty_units_map_cannot_verify(self):
        r = verdict({"schema_version": ru.SCHEMA_VERSION, "units": {}, "gates": {}})
        self.assertNotEqual(r["state"], "VERIFIED")
        self.assertTrue(r["missing_units"])

    def test_citationless_map_cannot_verify(self):
        r = verdict({"schema_version": ru.SCHEMA_VERSION, "units": {"U_grade": 0},
                     "consistency": CLEAN_CONSISTENCY, "gates": {}})
        self.assertNotEqual(r["state"], "VERIFIED")
        self.assertIn("U_cite_external", r["missing_units"])

    def test_consistency_without_score_stays_absent(self):
        """A consistency object with no score means the check was not measured."""
        d = systematic()
        d["consistency"] = {"critical_breaks": 0}
        r = verdict(d)
        self.assertIn("U_consistency", r["missing_units"])
        self.assertNotEqual(r["state"], "VERIFIED")

    def test_consistency_cannot_be_faked_via_units(self):
        """A directly-supplied U_consistency is ignored; only a real score counts."""
        d = systematic()
        d["units"]["U_consistency"] = 0
        d["consistency"] = {"critical_breaks": 0}
        self.assertIn("U_consistency", verdict(d)["missing_units"])

    def test_gates_required_as_object_when_scope_declared(self):
        d = systematic()
        del d["gates"]
        with self.assertRaises(ru.InputError):
            verdict(d)

    def test_boolean_count_rejected(self):
        with self.assertRaises(ru.InputError):
            verdict(systematic({"U_grade": True}))

    def test_numeric_string_rejected(self):
        """Agrees with prisma_flow.py and the new checks — one definition of malformed."""
        with self.assertRaises(ru.InputError):
            verdict(systematic({"U_grade": "0"}))

    def test_negative_count_rejected(self):
        with self.assertRaises(ru.InputError):
            verdict(systematic({"U_grade": -1}))

    def test_non_finite_rejected(self):
        for bad in (float("nan"), float("inf")):
            with self.subTest(value=bad), self.assertRaises(ru.InputError):
                verdict(systematic({"U_grade": bad}))

    def test_fractional_gate_rejected(self):
        """0.9 truncating to 0 would silently drop a pending human gate."""
        with self.assertRaises(ru.InputError):
            verdict(systematic(gates={"H_rob": 0.9}))


class TestHumanGates(unittest.TestCase):
    def test_pending_h_rob_blocks_on_human_not_verified(self):
        r = verdict(systematic(gates={"H_rob": 3}))
        self.assertEqual(r["state"], "BLOCKED_ON_HUMAN")
        self.assertEqual(r["gates_remaining"], 3)

    def test_unconfirmed_appraisals_are_not_also_auto_units(self):
        """H_rob exclusively owns matching-but-unconfirmed appraisals."""
        r = verdict(systematic({"U_rob_trace": 0}, gates={"H_rob": 3}))
        self.assertEqual(r["state"], "BLOCKED_ON_HUMAN")
        self.assertTrue(r["auto_units_zero"])
        self.assertIsNone(r["dominant_unit"])

    def test_gate_never_auto_zeroes_across_cycles(self):
        """No number of cycles satisfies a human gate."""
        for cycle in (1, 5, 12, ru.CEILING):
            with self.subTest(cycle=cycle):
                r = verdict(systematic(gates={"H_rob": 2}, cycle=cycle))
                self.assertEqual(r["gates_remaining"], 2)
                self.assertNotEqual(r["state"], "VERIFIED")

    def test_unknown_gate_key_rejected(self):
        d = systematic()
        d["gates"]["H_vibes"] = 0
        with self.assertRaises(ru.InputError):
            verdict(d)


class TestPlateauAndCeiling(unittest.TestCase):
    def test_plateau_after_k_flat_cycles(self):
        d = systematic({"U_grade": 5}, history=[5, 5, 5, 5])
        self.assertEqual(verdict(d)["state"], "PLATEAU")

    def test_improvement_breaks_the_plateau_run(self):
        d = systematic({"U_grade": 3}, history=[9, 8, 7, 5])
        self.assertEqual(verdict(d)["state"], "CONTINUE")

    def test_ceiling_reached(self):
        d = systematic({"U_grade": 1}, cycle=ru.CEILING)
        self.assertEqual(verdict(d)["state"], "CEILING")

    def test_history_must_be_numeric(self):
        with self.assertRaises(ru.InputError):
            verdict(systematic(history=["five"]))


class TestFloorGuard(unittest.TestCase):
    """Anti-gaming: a unit driven to zero by REMOVING content, not by fixing it.

    Returns a status string: "ok", or a tagged description of the drops.
    """

    def test_dropped_denominator_flagged_as_unlogged(self):
        status = ru.floor_guard_status({"citations": 40}, {"citations": 30}, False)
        self.assertIn("UNLOGGED", status)
        self.assertIn("40->30", status)

    def test_dropped_denominator_with_logged_exclusion_is_tagged_differently(self):
        status = ru.floor_guard_status({"citations": 40}, {"citations": 30}, True)
        self.assertIn("logged-exclusion", status)
        self.assertNotIn("UNLOGGED", status)

    def test_stable_denominator_is_ok(self):
        self.assertEqual(ru.floor_guard_status({"citations": 40}, {"citations": 40}, False), "ok")

    def test_growth_is_ok(self):
        self.assertEqual(ru.floor_guard_status({"citations": 40}, {"citations": 50}, False), "ok")

    def test_no_prior_baseline_is_ok(self):
        self.assertEqual(ru.floor_guard_status({}, {"citations": 30}, False), "ok")

    def test_vanished_key_is_flagged(self):
        """Removing a denominator entirely is the largest possible content removal."""
        status = ru.floor_guard_status({"citations": 40}, {}, False)
        self.assertIn("removed", status)

    def test_wiping_all_denominators_is_not_silently_ok(self):
        status = ru.floor_guard_status({"citations": 40, "studies": 12}, {}, False)
        self.assertIn("citations", status)
        self.assertIn("studies", status)


class TestDryRun(unittest.TestCase):
    def test_preview_lists_new_units_in_scope(self):
        preview = ru.dry_run_preview(systematic(), ru.CEILING)
        self.assertTrue(preview["dry_run"])
        self.assertIn("U_checklist", preview["units_in_scope"])
        self.assertIn("U_rob_trace", preview["units_in_scope"])
        self.assertIn("U_grade", preview["units_in_scope"])
        self.assertEqual(preview["ceiling"], ru.CEILING)

    def test_preview_names_the_gates_that_will_fire(self):
        preview = ru.dry_run_preview(systematic(gates={"H_rob": 2}), ru.CEILING)
        self.assertIn("H_rob", preview["human_gates_that_will_fire"])

    def test_preview_writes_no_state(self):
        self.assertIn("no state written", preview_note := ru.dry_run_preview(
            systematic(), ru.CEILING)["note"])
        self.assertIn("preview only", preview_note)


if __name__ == "__main__":
    unittest.main()


class TestIgnoredInputsAreReported(unittest.TestCase):
    """Round 9: U_consistency supplied under `units` is deliberately dropped, so a
    hand-written zero cannot satisfy the universal floor without a real score. But
    reporting only 'missing' told a caller who DID supply it to add the very key
    being ignored. The drop is correct; saying nothing about it was not."""

    def record(self, **over):
        rec = {"schema_version": ru.SCHEMA_VERSION, "review_type": "systematic",
               "units_in_scope": ["U_cite_external", "U_cite_internal", "U_consistency"],
               "units": {"U_cite_external": 0, "U_cite_internal": 0},
               "consistency": {"score": 90, "critical_breaks": 0},
               "gates": {}, "cycle": 1}
        rec.update(over)
        return rec

    def test_supplying_the_unit_directly_is_reported_not_silent(self):
        rec = self.record(units={"U_cite_external": 0, "U_cite_internal": 0,
                                 "U_consistency": 0})
        del rec["consistency"]
        v = ru.verdict(rec, ru.DEFAULT_WEIGHTS, ru.CEILING)
        self.assertIn("U_consistency", v["missing_units"])
        self.assertEqual(len(v["ignored_inputs"]), 1)
        self.assertIn("is ignored", v["ignored_inputs"][0])
        self.assertIn("consistency", v["ignored_inputs"][0])

    def test_a_hand_written_zero_still_cannot_satisfy_the_floor(self):
        """The guard itself is unchanged — only the diagnostic is new."""
        rec = self.record(units={"U_cite_external": 0, "U_cite_internal": 0,
                                 "U_consistency": 0})
        del rec["consistency"]
        v = ru.verdict(rec, ru.DEFAULT_WEIGHTS, ru.CEILING)
        self.assertNotEqual(v["state"], "VERIFIED")

    def test_nothing_reported_when_the_object_is_used_properly(self):
        v = ru.verdict(self.record(), ru.DEFAULT_WEIGHTS, ru.CEILING)
        self.assertEqual(v["ignored_inputs"], [])
        self.assertEqual(v["missing_units"], [])


class TestConflictingConsistencyInputIsReported(unittest.TestCase):
    """Round 10: hanging the diagnostic off `elif` left the WORST case silent.

    Supply a valid `consistency` object AND a contradicting `U_consistency`, and
    derivation wins (correct) while the disagreement is concealed (not). The
    record reached VERIFIED with ignored_inputs empty.
    """

    def run_it(self, units, consistency=None):
        rec = {"schema_version": ru.SCHEMA_VERSION, "review_type": "systematic",
               "units_in_scope": ["U_cite_external", "U_cite_internal", "U_consistency"],
               "units": units, "gates": {}, "cycle": 1}
        if consistency is not None:
            rec["consistency"] = consistency
        return ru.verdict(rec, ru.DEFAULT_WEIGHTS, ru.CEILING)

    BASE = {"U_cite_external": 0, "U_cite_internal": 0}

    def test_conflict_is_reported_even_though_derivation_succeeds(self):
        v = self.run_it({**self.BASE, "U_consistency": 999},
                        {"score": 90, "critical_breaks": 0})
        self.assertEqual(v["state"], "VERIFIED")          # derivation is authoritative
        self.assertEqual(len(v["ignored_inputs"]), 1)      # but it is not silent
        note = v["ignored_inputs"][0]
        self.assertIn("999", note)
        self.assertIn("authoritative", note)

    def test_message_distinguishes_the_two_cases(self):
        """No usable object is a different problem from a conflicting one, and the
        remedy differs: supply the object vs. remove the direct key."""
        absent = self.run_it({**self.BASE, "U_consistency": 0})["ignored_inputs"][0]
        conflict = self.run_it({**self.BASE, "U_consistency": 999},
                               {"score": 90, "critical_breaks": 0})["ignored_inputs"][0]
        self.assertIn("Supply", absent)
        self.assertIn("Remove the direct key", conflict)
        self.assertNotEqual(absent, conflict)

    def test_correct_usage_reports_nothing(self):
        v = self.run_it(self.BASE, {"score": 90, "critical_breaks": 0})
        self.assertEqual(v["ignored_inputs"], [])
        self.assertEqual(v["state"], "VERIFIED")
