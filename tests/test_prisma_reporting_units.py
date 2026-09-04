"""The strengthened PRISMA reporting units reach the verdict, or the verdict is held.

WHAT WAS BROKEN. The three strengthened PRISMA reporting checks shipped as
standalone scripts: `review_units.py` rejected `U_prisma_compliance` outright as an
unknown unit, nothing invoked the sub-gate, and its `gates: {"underived": [...]}`
field could not have been ingested had it been registered. So a review could reach
`VERIFIED` on location-only addressability (`U_checklist`) while substantive
compliance was never derived at all — RFC #21's verify-review acceptance criterion,
unmet not by omission but mechanically.

WHAT THIS PINS. Each half of the fix, from the consumer's side:

  * the units are representable, and DERIVED from a run rather than asserted;
  * a compliance record with no repairable defect but unsigned assertions cannot
    reach VERIFIED, because the confirmation is a human gate;
  * a unit declared in scope whose record was not supplied is UNDERIVED, not zero.

Standard library only.
"""
from __future__ import annotations

import json
import pathlib
import unittest

from _load import load

REPO = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"

ru = load("skills/verify-review/scripts/review_units.py")

PRISMA_UNITS = ("U_prisma_compliance", "U_prisma_abstract", "U_prisma_updated")
BASE_SCOPE = ["U_cite_external", "U_cite_internal", "U_consistency", "U_prisma",
              "U_checklist"]


def runner():
    return ru.CheckRunner(records_root=FIXTURES, skills_root=REPO)


def reporting_entry(**overrides):
    entry = {"record": "prisma-compliance.valid.json",
             "abstract_record": "prisma-abstract.compliance.json",
             "updated_flow_record": "prisma-updated-flow.valid.json"}
    entry.update(overrides)
    return entry


def record(*, scope_extra=(), units=None, checks=None, gates=None):
    """A systematic review whose PRISMA reporting units are in scope."""
    u = {"U_cite_external": 0, "U_cite_internal": 0}
    if units:
        u.update(units)
    return {
        "schema_version": ru.SCHEMA_VERSION,
        "review_type": "systematic",
        "units_in_scope": BASE_SCOPE + list(scope_extra),
        "units": u,
        "consistency": {"score": 90, "critical_breaks": 0},
        "gates": dict({"H_rob": 0, "H_screen_adj": 0, "H_cite_manual": 0, "H_numeric": 0},
                      **(gates or {})),
        "checks": dict({"prisma_flow": {"record": "counts.valid.json"},
                        "prisma_checklist": {"record": "checklist.valid.json"}},
                       **(checks or {})),
    }


def verdict(data):
    return ru.verdict(data, ru.DEFAULT_WEIGHTS, ru.CEILING, runner())


class TestTheUnitsAreRepresentable(unittest.TestCase):
    """The chokepoint itself: these names were rejected as unknown."""

    def test_each_unit_is_a_known_unit_with_a_weight(self):
        for unit in PRISMA_UNITS:
            with self.subTest(unit=unit):
                self.assertIn(unit, ru.DEFAULT_WEIGHTS)

    def test_each_unit_is_derived_by_the_reporting_sub_gate(self):
        for unit in PRISMA_UNITS:
            with self.subTest(unit=unit):
                self.assertEqual("prisma_reporting_checks", ru.DERIVED_BY[unit])

    def test_the_human_gate_is_a_known_gate_owned_by_the_sub_gate(self):
        self.assertIn("H_prisma_evidence", ru.GATE_KEYS)
        self.assertEqual("prisma_reporting_checks", ru.DERIVED_BY_GATE["H_prisma_evidence"])

    def test_a_units_map_naming_them_is_accepted(self):
        r = verdict(record(scope_extra=PRISMA_UNITS,
                           units={u: 0 for u in PRISMA_UNITS},
                           checks={"prisma_reporting_checks": reporting_entry()}))
        for unit in PRISMA_UNITS:
            self.assertIn(unit, r["units_evaluated"])


class TestTheCountsComeFromTheRun(unittest.TestCase):
    def test_a_clean_reporting_record_reaches_verified(self):
        r = verdict(record(scope_extra=PRISMA_UNITS,
                           units={u: 0 for u in PRISMA_UNITS},
                           checks={"prisma_reporting_checks": reporting_entry()}))
        self.assertEqual("VERIFIED", r["state"], msg=json.dumps(r, indent=2)[:2000])

    def test_a_self_reported_zero_does_not_override_the_check(self):
        """The point of registering the check rather than the unit alone: a record
        asserting zero over a record the check disagrees with is not believed."""
        r = verdict(record(
            scope_extra=PRISMA_UNITS,
            units={u: 0 for u in PRISMA_UNITS},
            checks={"prisma_reporting_checks": reporting_entry(
                record="prisma-compliance.unconfirmed.json")}))
        self.assertNotEqual("VERIFIED", r["state"])

    def test_a_location_only_checklist_no_longer_carries_the_whole_claim(self):
        """`U_checklist` clean and the compliance unit UNDERIVED is not VERIFIED.

        This is the shape of the original defect: addressability satisfied, nothing
        said about substantive compliance. Declaring the unit in scope without
        supplying the record now holds the verdict instead of passing it.
        """
        r = verdict(record(scope_extra=PRISMA_UNITS, units={u: 0 for u in PRISMA_UNITS}))
        self.assertNotEqual("VERIFIED", r["state"])
        for unit in PRISMA_UNITS:
            self.assertIn(unit, r["underived_units"])


class TestTheHumanGateHoldsTheVerdict(unittest.TestCase):
    def test_unsigned_assertions_are_a_gate_not_a_unit(self):
        """Zero repairable defects, three confirmations owed. The unit count is
        clean and the review is still not verified — no number of agent cycles can
        clear a signature, so it must never be booked as auto-reducible work."""
        r = verdict(record(
            scope_extra=PRISMA_UNITS,
            units={u: 0 for u in PRISMA_UNITS},
            checks={"prisma_reporting_checks": reporting_entry(
                record="prisma-compliance.unconfirmed.json")}))
        self.assertEqual(0, r["units_evaluated"]["U_prisma_compliance"])
        self.assertEqual(3, r["gates_evaluated"]["H_prisma_evidence"])
        self.assertEqual(3, r["gates_remaining"])
        # Not merely "not VERIFIED": the review is blocked on a PERSON, which is the
        # state a loop cannot cycle its way out of.
        self.assertEqual("BLOCKED_ON_HUMAN", r["state"])

    def test_the_gate_is_required_whenever_its_proxy_unit_is_in_scope(self):
        """A review that must count compliance defects must also have its
        compliance assertions signed — the `H_rob`/`U_rob_trace` pairing."""
        self.assertEqual("U_prisma_compliance", ru.GATE_SCOPE_PROXY["H_prisma_evidence"])
        r = verdict(record(scope_extra=PRISMA_UNITS, units={u: 0 for u in PRISMA_UNITS}))
        self.assertIn("H_prisma_evidence", r["underived_gates"])


class TestTheSubGateEnvelopeIsIngestible(unittest.TestCase):
    """Round-trip through the consumer's own validator, which is stricter than the
    sub-gate's own output test: units and gates must match the table EXACTLY."""

    def envelope_for(self, entry):
        argv = runner().argv_for("prisma_reporting_checks", entry)
        import subprocess
        proc = subprocess.run(argv, capture_output=True, text=True)
        self.assertIn(proc.returncode, (0, 1), msg=proc.stderr)
        return proc.stdout

    def test_the_full_envelope_validates_against_the_table(self):
        entry = reporting_entry()
        units, gates, unattributed = ru._validated_envelope(
            "prisma_reporting_checks", self.envelope_for(entry),
            ru._would_derive("prisma_reporting_checks", entry))
        self.assertEqual({"U_prisma_compliance": 0, "U_prisma_abstract": 0,
                          "U_prisma_updated": 0}, units)
        self.assertEqual({"H_prisma_evidence": 0}, gates)
        self.assertEqual(0, unattributed)

    def test_a_compliance_only_envelope_validates_against_the_narrower_prediction(self):
        entry = {"record": "prisma-compliance.valid.json"}
        units, gates, _ = ru._validated_envelope(
            "prisma_reporting_checks", self.envelope_for(entry),
            ru._would_derive("prisma_reporting_checks", entry))
        self.assertEqual({"U_prisma_compliance": 0}, units)
        self.assertEqual({"H_prisma_evidence": 0}, gates)

    def test_an_addressability_abstract_record_fails_closed_at_the_cli(self):
        """Exit 2, not a quietly smaller aggregate: an addressability record asserts
        no compliance, so folding it in would report a satisfied human gate over a
        record that never claimed one."""
        import subprocess
        argv = runner().argv_for("prisma_reporting_checks", reporting_entry(
            abstract_record="prisma-abstract.addressability.json"))
        proc = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(2, proc.returncode, msg=proc.stdout)
        self.assertIn("compliance", proc.stderr)

    def test_the_old_underived_gates_shape_would_be_rejected(self):
        """Why the field had to move to `detail`: `gates` carries counts under the
        gate keys the table assigns, so a list under an invented key cannot be read.
        """
        stale = json.dumps({"check": "prisma_reporting_checks", "schema_version": "1.0",
                            "issues": 0, "units": {"U_prisma_compliance": 0},
                            "gates": {"underived": ["U_prisma_updated"]},
                            "unattributed": 0})
        with self.assertRaises(ru.InputError):
            ru._validated_envelope("prisma_reporting_checks", stale,
                                   {"U_prisma_compliance"})


if __name__ == "__main__":
    unittest.main()
