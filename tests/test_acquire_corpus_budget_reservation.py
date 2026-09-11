"""Regression for PR #33 reviewer finding: failure-budget calls must not overshoot."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from _load import load

acq = load("skills/acquire-corpus/scripts/acquire_corpus.py")


class FailureBudgetReservationTests(unittest.TestCase):
    def test_sub_timeout_remainder_is_not_treated_as_room_for_another_full_call(self):
        budget = acq._FailureBudget(limit=15.0)
        budget.charge(5.0)
        budget.charge(5.0)
        budget.charge(0.1)

        self.assertLess(budget.waited, budget.limit)
        self.assertFalse(budget.can_start())
        self.assertTrue(budget.exhausted)
        self.assertGreater(budget.waited + acq.ORX_TIMEOUT_SECONDS, budget.limit)

    def test_metadata_completion_is_skipped_before_resolver_when_full_timeout_will_not_fit(self):
        budget = acq._FailureBudget(limit=15.0)
        budget.charge(5.0)
        budget.charge(5.0)
        budget.charge(0.1)
        calls = []

        def resolver(_rec, _config):
            calls.append(True)
            return {"authors": ["Ada Lovelace"], "year": 2025}

        completer = acq._BoundedMetadataCompleter(resolver, budget)
        with tempfile.TemporaryDirectory() as td:
            config = acq.AcquisitionConfig(
                queries=("widgets",), output_dir=Path(td), run_date="2026-09-11"
            )
            with self.assertRaises(acq.EnrichmentFailure) as ctx:
                completer(
                    {
                        "source": "orx",
                        "sub_source": "alphaxiv",
                        "source_id": "2401.12345",
                        "title": "Widgets",
                        "year": 2025,
                    },
                    config,
                )

        self.assertEqual(ctx.exception.reason, "metadata-completion-skipped:run-failure-budget-exhausted")
        self.assertEqual(calls, [])
        self.assertEqual(completer.attempts, 0)

    def test_exact_remaining_timeout_is_admissible(self):
        budget = acq._FailureBudget(limit=15.0)
        budget.charge(5.0)
        budget.charge(5.0)
        self.assertTrue(budget.can_start())
        self.assertFalse(budget.exhausted)
        budget.charge(5.0)
        self.assertEqual(budget.waited, 15.0)
        self.assertTrue(budget.exhausted)


if __name__ == "__main__":
    unittest.main()
