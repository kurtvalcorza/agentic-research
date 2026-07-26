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
    },
    "risk-of-bias.md": {
        "script": "skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
        "argv0": "rob_appraisal.py",
        "args": lambda: ["--strict"],
        "expect": 0,
        "why": "complete record, presented as valid",
    },
    "prisma-checklist.md": {
        "script": "skills/prisma-flow/scripts/prisma_checklist.py",
        "argv0": "prisma_checklist.py",
        "args": lambda: ["--strict"],
        "expect": 1,
        "why": "excerpt: 4 of 42 rows, so Rule 1 fires",
        "doc_says": "excerpt, not a complete record",
    },
    "review-units.md": {
        "script": "skills/verify-review/scripts/review_units.py",
        "argv0": "review_units.py",
        "args": lambda: [],
        "expect": 1,
        "why": "complete record in a mid-review state: units outstanding, so not verified",
        "doc_says": "units still outstanding",
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
