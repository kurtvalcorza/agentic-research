"""Cross-script conformance: all four gates must agree on what malformed input is.

The coercion helpers are DUPLICATED across the checks rather than shared, because
constitution Principle III requires each skill directory to stay copyable on its
own. Duplication is only safe if it cannot drift — this test is what stops it.

If you change one script's coercion, this fails until you change them all.
Standard library only.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

pf = load("skills/prisma-flow/scripts/prisma_flow.py")
gp = load("skills/validate-evidence/scripts/grade_profile.py")
ru = load("skills/verify-review/scripts/review_units.py")

# (script label, callable raising on malformed input, its error type)
COERCERS = [
    ("prisma_flow._int", lambda v: pf._int(v, "x"), pf.CountError),
    ("grade_profile._int", lambda v: gp._int(v, "x"), gp.InputError),
    ("review_units._as_nonneg_count", lambda v: ru._as_nonneg_count(v, "x"), ru.InputError),
]

# Values every gate must REJECT, with why it matters.
REJECTED = [
    (True, "bool is an int subclass; true would silently count as 1"),
    (False, "false would silently count as 0 and satisfy an all-zero predicate"),
    (-1, "a negative count could cancel a positive one to a false zero"),
    (float("nan"), "NaN blinds comparisons and emits invalid JSON"),
    (float("inf"), "infinity blinds comparisons and emits invalid JSON"),
    ("3", "a quoted count is a wrong type, not a number to coerce"),
    ("many", "a non-numeric string is not a count"),
    (None, "null is not a count"),
    ([], "a list is not a count"),
    ({}, "an object is not a count"),
]

# Fractional values are the ONE justified divergence, so they are tested apart.
#
# The three artifact checks count discrete things — records, studies, checklist
# rows — so 3.5 of them is meaningless and rejected. review_units' unit scalar is
# different in kind: U_consistency is GRADED, derived as
# `critical_breaks + max(0, 75 - score)`, and a score of 82.5 legitimately yields a
# fractional unit. Whole numbers are still enforced where they must be, by
# _as_int_count for gates and cycle, so 0.9 cannot truncate a pending human gate
# to zero.
DISCRETE_COUNTERS = [
    ("prisma_flow._int", lambda v: pf._int(v, "x"), pf.CountError),
    ("grade_profile._int", lambda v: gp._int(v, "x"), gp.InputError),
    ("review_units._as_int_count", lambda v: ru._as_int_count(v, "x"), ru.InputError),
]

# Values every gate must ACCEPT.
ACCEPTED = [0, 1, 42]


class TestRejectionConformance(unittest.TestCase):
    def test_all_gates_reject_the_same_values(self):
        for value, why in REJECTED:
            for label, fn, exc in COERCERS:
                with self.subTest(value=repr(value), script=label, reason=why):
                    with self.assertRaises(exc):
                        fn(value)

    def test_all_gates_accept_whole_non_negative_numbers(self):
        for value in ACCEPTED:
            for label, fn, _ in COERCERS:
                with self.subTest(value=value, script=label):
                    self.assertEqual(int(fn(value)), value)


class TestIntegralFloats(unittest.TestCase):
    """3.0 is a whole number written as a float — JSON has one number type."""

    def test_accepted_everywhere(self):
        for label, fn, _ in COERCERS:
            with self.subTest(script=label):
                self.assertEqual(int(fn(3.0)), 3)


class TestFractionalValues(unittest.TestCase):
    """The one justified divergence — see the DISCRETE_COUNTERS note above."""

    def test_discrete_counters_reject_fractions(self):
        for label, fn, exc in DISCRETE_COUNTERS:
            with self.subTest(script=label):
                with self.assertRaises(exc):
                    fn(3.5)

    def test_graded_unit_scalar_permits_fractions(self):
        """U_consistency is graded, not counted: score 82.5 is a legitimate input."""
        self.assertAlmostEqual(ru._as_nonneg_count(3.5, "x"), 3.5)

    def test_derived_consistency_unit_can_be_fractional(self):
        unit = ru.derive_consistency_unit({"score": 70.5, "critical_breaks": 0})
        self.assertAlmostEqual(unit, 4.5)

    def test_fractional_gate_still_rejected(self):
        """0.9 truncating to 0 would silently drop a pending human gate."""
        with self.assertRaises(ru.InputError):
            ru._as_int_count(0.9, "gates.H_rob")


class TestExitCodeContract(unittest.TestCase):
    """All four checks share one outcome contract (contracts/cli-contract.md)."""

    def test_every_check_documents_the_same_codes(self):
        scripts = [
            "skills/prisma-flow/scripts/prisma_flow.py",
            "skills/prisma-flow/scripts/prisma_checklist.py",
            "skills/validate-evidence/scripts/grade_profile.py",
            "skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
        ]
        root = pathlib.Path(__file__).resolve().parent.parent
        for rel in scripts:
            text = (root / rel).read_text(encoding="utf-8")
            with self.subTest(script=rel):
                self.assertIn("EXIT CODES", text)
                self.assertIn("--strict", text)

    def test_every_check_documents_what_it_cannot_verify(self):
        """Constitution Principle VI: a gate must state its own limits.

        Uniform requirement — the original flow check was missing this block until
        the Phase 8 audit, which is precisely why it is asserted rather than assumed.
        """
        root = pathlib.Path(__file__).resolve().parent.parent
        for rel in ["skills/prisma-flow/scripts/prisma_flow.py",
                    "skills/prisma-flow/scripts/prisma_checklist.py",
                    "skills/validate-evidence/scripts/grade_profile.py",
                    "skills/appraise-risk-of-bias/scripts/rob_appraisal.py"]:
            text = (root / rel).read_text(encoding="utf-8")
            with self.subTest(script=rel):
                self.assertIn("WHAT THIS CANNOT CHECK", text)

    def test_every_owning_skill_states_the_limit_too(self):
        """Principle VI says 'in its skill', not only in the script."""
        root = pathlib.Path(__file__).resolve().parent.parent
        for rel in ["skills/prisma-flow/SKILL.md",
                    "skills/validate-evidence/SKILL.md",
                    "skills/appraise-risk-of-bias/SKILL.md"]:
            text = (root / rel).read_text(encoding="utf-8")
            with self.subTest(skill=rel):
                self.assertIn("CANNOT verify", text)


if __name__ == "__main__":
    unittest.main()
