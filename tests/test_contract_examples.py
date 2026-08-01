"""Every JSON example in specs/001-.../contracts/ must actually run.

Round 8 found the canonical grade-profile example failing the very command
printed above it: it declared `basis: confirmed_rob` but omitted the
`appraised_result` that basis requires, so a reader who copied it got exit 1
instead of the advertised clean result.

A contract example is documentation that claims to be executable. Nothing was
executing it, so it drifted the moment the schema changed. This module runs
every example through its own check and pins the result, which is the only
way the claim stays true across future schema changes.

Standard library only.
"""
from __future__ import annotations

import io
import json
import pathlib
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load, fixture  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
CONTRACTS = REPO / "specs" / "001-standards-enforcement-parity" / "contracts"

# contract file -> how to run its example, and what the contract claims will happen.
#
# The expected exit is declared per contract rather than assumed to be 0. Two of
# these are deliberately not clean runs, and asserting 0 across the board would
# have forced a doc to lie to satisfy a test:
#
#   prisma-checklist.md prints an EXCERPT — four rows of forty-two. Rule 1 makes
#   that exit 1, which is the check working. Pinning 1 keeps the excerpt honest
#   without swamping the contract with a 42-row record.
#
#   review_units.py has no --strict flag; its verdict is the output, not the exit
#   code. Passing --strict anywhere here would be testing an interface that does
#   not exist.
CHECKS = {
    "grade-profile.md": {
        "script": "skills/validate-evidence/scripts/grade_profile.py",
        "argv0": "grade_profile.py",
        # The example declares confirmed_rob, so traceability needs the companion
        # appraisal record the contract's own invocation line names.
        "args": lambda: ["--rob", str(fixture("risk-of-bias.contract-example.json")),
                         "--strict"],
        "expect": 0,
        "why": "complete record, presented as valid",
        "stdout_has": ["moderate"],
    },
    "risk-of-bias.md": {
        "script": "skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
        "argv0": "rob_appraisal.py",
        "args": lambda: ["--strict"],
        "expect": 0,
        "why": "complete record, presented as valid",
        "stdout_has": ["1 appraisal of 1 study", "**H_rob: 0**"],
    },
    "prisma-flow.md": {
        "script": "skills/prisma-flow/scripts/prisma_flow.py",
        "argv0": "prisma_flow.py",
        "args": lambda: ["--strict"],
        "expect": 0,
        "why": "reconciling Template-1 record, presented as valid",
        # The flow check had no contract at all, so its schema lived only in a
        # docstring and NOTHING executed the example — the one check exempt from
        # the guard this module exists to be. It changed twice in this feature.
        # "5 of 5 stages checked", not "end to end" and no longer "attempted":
        # every edge now gates on all of its operands, so a listed stage really
        # did compare supplied numbers, and the denominator is the stages that
        # APPLY to a one-arm record rather than a fixed eight.
        "stdout_has": ["```mermaid", "✅ Counts reconcile — 5 of 5 stages checked"],
    },
    "prisma-checklist.md": {
        "script": "skills/prisma-flow/scripts/prisma_checklist.py",
        "argv0": "prisma_checklist.py",
        "args": lambda: ["--strict"],
        "expect": 1,
        "why": "excerpt: 4 of 42 rows, so Rule 1 fires",
        "doc_says": "excerpt, not a complete record",
        # The exact shortfall, so a NEW violation cannot hide behind the same exit 1.
        "stdout_has": ["4 of 42 rows addressed", "38 row(s) not addressed"],
    },
    "review-units.md": {
        "script": "skills/verify-review/scripts/review_units.py",
        "argv0": "review_units.py",
        "args": lambda: [],
        "expect": 1,
        "why": "complete record in a mid-review state: units outstanding, so not verified",
        "doc_says": "units still outstanding",
        # This check emits JSON, so assert the parsed verdict rather than substrings.
        # `missing_units: []` is the load-bearing one: round 9 found the example was
        # failing for a DIFFERENT reason (a required unit reported missing) that an
        # exit-code assertion could not distinguish from the documented outcome.
        "json_is": {
            "missing_units": [],
            "ignored_inputs": [],
            # The example declares scope and ships no `checks` block, because it is
            # run from a scratch directory and cannot carry four artifact files.
            # Pinned rather than left unsaid: the contract now tells the reader this
            # verdict is held for a reason the seven outstanding units do not
            # explain, and an unpinned field is how that sentence goes stale.
            "underived_units": ["U_checklist", "U_grade", "U_prisma", "U_rob_trace"],
            "unattributed_issues": [],
            "by_unit": {"U_cite_external": 0.0, "U_cite_internal": 0.0,
                        "U_consistency": 0.0, "U_screen": 0.0, "U_extract": 0.0,
                        "U_prisma": 0.0, "U_grade": 2.0, "U_rob_trace": 1.0,
                        "U_checklist": 4.0},
            "gates_remaining": 3,
        },
    },
}

JSON_BLOCK = re.compile(r"^```json\n(.*?)^```", re.S | re.M)


def examples(name: str) -> list[str]:
    return JSON_BLOCK.findall((CONTRACTS / name).read_text(encoding="utf-8"))


class TestContractExamplesAreValidJson(unittest.TestCase):
    def test_every_example_parses(self):
        """A fenced ```json block must be JSON — no trailing commas, no comments.

        Prose belongs outside the fence; a `// note` inside it makes the block
        uncopyable, which defeats the point of printing it.
        """
        for name in CHECKS:
            for i, block in enumerate(examples(name)):
                with self.subTest(contract=name, block=i):
                    try:
                        json.loads(block)
                    except json.JSONDecodeError as e:
                        self.fail(f"{name} example {i} is not valid JSON: {e}")

    def test_each_contract_prints_an_example(self):
        for name in CHECKS:
            with self.subTest(contract=name):
                self.assertTrue(examples(name), f"{name} has no ```json example")


class TestContractExamplesBehaveAsDocumented(unittest.TestCase):
    """The stronger claim: the example is not merely well-formed, it does what the
    surrounding prose says it does."""

    def run_example(self, contract: str, block: str):
        spec = CHECKS[contract]
        mod = load(spec["script"])
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "example.json"
            p.write_text(block, encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            argv = [spec["argv0"], str(p), *spec["args"]()]
            with mock.patch.object(sys, "argv", argv), \
                    redirect_stdout(out), redirect_stderr(err):
                code = mod.main()
        return code, out.getvalue(), err.getvalue()

    def test_examples_exit_as_the_contract_says(self):
        for name, spec in CHECKS.items():
            for i, block in enumerate(examples(name)):
                with self.subTest(contract=name, block=i):
                    code, out, err = self.run_example(name, block)
                    self.assertEqual(
                        code, spec["expect"],
                        msg=(f"{name} example {i} exits {code}, contract says "
                             f"{spec['expect']} ({spec['why']}).\n{out}\n{err}"))

    def test_examples_produce_the_documented_diagnostics(self):
        """The exit code alone is far too coarse.

        Every method violation maps to 1, so an example can start failing for an
        entirely different reason and a status-only assertion stays green. That is
        exactly what happened: `review-units.md` reported a REQUIRED UNIT MISSING
        rather than the documented seven-units-outstanding, and the exit-code check
        added in round 8 could not tell the two apart.
        """
        for name, spec in CHECKS.items():
            for i, block in enumerate(examples(name)):
                with self.subTest(contract=name, block=i):
                    _, out, err = self.run_example(name, block)
                    for needle in spec.get("stdout_has", ()):
                        self.assertIn(needle, out, msg=f"{name}\n{out}\n{err}")
                    if "json_is" in spec:
                        parsed = json.loads(out)
                        for key, want in spec["json_is"].items():
                            self.assertEqual(parsed.get(key), want,
                                             msg=f"{name}: {key}\n{out}")

    def test_every_example_is_pinned_by_more_than_its_exit_code(self):
        """No contract may rely on the status alone — see the docstring above."""
        for name, spec in CHECKS.items():
            with self.subTest(contract=name):
                self.assertTrue(
                    spec.get("stdout_has") or spec.get("json_is"),
                    f"{name} pins only an exit code, which cannot distinguish the "
                    f"documented outcome from any other violation")

    def test_a_non_clean_example_is_explained_in_the_doc(self):
        """A non-zero expectation is only acceptable if the doc warns the reader.

        Otherwise the pin quietly legitimises a broken example — the exact failure
        this module exists to catch. Each such contract declares the phrase that
        must appear, so satisfying this test means editing prose a reader sees,
        not adding a keyword the test happens to grep for.
        """
        for name, spec in CHECKS.items():
            if spec["expect"] == 0:
                self.assertNotIn("doc_says", spec,
                                 f"{name} expects a clean run; no warning needed")
                continue
            with self.subTest(contract=name):
                text = (CONTRACTS / name).read_text(encoding="utf-8").lower()
                self.assertIn(
                    spec["doc_says"].lower(), text,
                    f"{name}'s example is pinned to exit {spec['expect']} "
                    f"({spec['why']}) but the contract never tells the reader that")


if __name__ == "__main__":
    unittest.main()
