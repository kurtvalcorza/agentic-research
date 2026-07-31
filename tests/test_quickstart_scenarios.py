"""Every command in quickstart.md must actually do what the guide says it does.

The guide closed by asserting that "every scenario in this guide was executed end
to end during T058" — a claim about a moment in the past that nothing rechecked.
By the time a reviewer copied Scenario 2, the record it names had gained a
`confirmed_rob` basis, so the advertised passing command exited 1 for want of the
`--rob` it never mentioned.

This is the same defect round 8 found in the contract examples and fixed for
`contracts/` alone: documentation that claims to be executable, with nothing
executing it. The fix has to cover the guide too, or the next schema change puts
it straight back.

What this module does:
  * extracts every `python skills/...` invocation from the guide's bash blocks,
  * runs it in-process and asserts the exit code the guide declares beside it,
  * REFUSES any command that declares no expected exit, so a new scenario cannot
    be added unpinned,
  * runs Scenario 3's fixture table and asserts each listed exit, plus that an
    exit-1 row fails for its OWN reason rather than the generic
    basis-claimed-without-an-appraisal violation the table is not about.

Standard library only.
"""
from __future__ import annotations

import io
import pathlib
import re
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load, fixture  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
QUICKSTART = REPO / "specs" / "001-standards-enforcement-parity" / "quickstart.md"

BASH_BLOCK = re.compile(r"^```bash\n(.*?)^```", re.S | re.M)
# `# exit N` on the command itself or on a continuation line beneath it, and the
# `echo $?    # N` idiom the guide also uses.
EXIT_COMMENT = re.compile(r"#\s*exit\s+(\d+)")
ECHO_STATUS = re.compile(r"^\s*echo \$\?\s*#\s*(\d+)")

SCRIPT_ARGV0 = {
    "skills/validate-evidence/scripts/grade_profile.py": "grade_profile.py",
    "skills/appraise-risk-of-bias/scripts/rob_appraisal.py": "rob_appraisal.py",
    "skills/prisma-flow/scripts/prisma_checklist.py": "prisma_checklist.py",
    "skills/prisma-flow/scripts/prisma_flow.py": "prisma_flow.py",
    "skills/verify-review/scripts/review_units.py": "review_units.py",
}

# Scenario 3's table: fixture -> the exit the guide claims. Parsed from the table
# itself rather than restated here, so editing one without the other is caught.
TABLE_ROW = re.compile(r"^\|\s*`(grade-profile\.[^`]+\.json)`\s*\|\s*(\d)\s*\|")


def _logical_lines(block: str) -> list[str]:
    """Join backslash-continued lines, keeping any trailing comment on either part."""
    out: list[str] = []
    buf = ""
    for line in block.splitlines():
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buf += stripped[:-1].rstrip() + " "
            continue
        out.append((buf + stripped).strip())
        buf = ""
    if buf:
        out.append(buf.strip())
    return out


def commands() -> list[tuple[str, int]]:
    """Every `python skills/...` invocation in the guide, with its declared exit."""
    found: list[tuple[str, int]] = []
    for block in BASH_BLOCK.findall(QUICKSTART.read_text(encoding="utf-8")):
        lines = _logical_lines(block)
        for i, line in enumerate(lines):
            if not line.startswith("python skills/"):
                continue
            declared = None
            # The declaration may sit on the command, on a comment-only line under
            # it, or in the `echo $?` idiom the guide uses in Scenario 2.
            for candidate in (line, *lines[i + 1:i + 3]):
                if candidate.startswith("python "):
                    if candidate is not line:
                        break                    # the next command, not this one's note
                    m = EXIT_COMMENT.search(candidate)
                else:
                    m = ECHO_STATUS.match(candidate) or (
                        EXIT_COMMENT.search(candidate)
                        if candidate.lstrip().startswith("#") else None)
                if m:
                    declared = int(m.group(1))
                    break
            found.append((line, declared))
    return found


def run_command(line: str) -> tuple[int, str, str]:
    """Run one documented invocation in-process, from the repository root."""
    parts = [p for p in line.split("#", 1)[0].split() if p]
    script = parts[1]
    args = []
    for raw in parts[2:]:
        # Paths in the guide are repo-root-relative, as its prerequisites state.
        args.append(str(REPO / raw) if raw.startswith("tests/") else raw)
    mod = load(script)
    out, err = io.StringIO(), io.StringIO()
    argv = [SCRIPT_ARGV0[script], *args]
    with mock.patch.object(sys, "argv", argv), \
            redirect_stdout(out), redirect_stderr(err):
        code = mod.main()
    return code, out.getvalue(), err.getvalue()


class TestQuickstartCommandsAreExecutable(unittest.TestCase):
    maxDiff = None

    def test_the_guide_actually_contains_commands(self):
        """Guard against the runner passing because it parsed nothing."""
        self.assertGreaterEqual(len(commands()), 6)

    def test_every_command_declares_its_expected_exit(self):
        """An undeclared command is an unchecked claim.

        Exit codes are the only part of a scenario this module can verify
        mechanically, so a command with no declaration is documentation that
        asserts nothing testable — it fails here rather than being skipped.
        """
        undeclared = [line for line, declared in commands() if declared is None]
        self.assertEqual(
            undeclared, [],
            "these quickstart commands declare no expected exit; add a trailing "
            "`# exit N`:\n  " + "\n  ".join(undeclared))

    def test_every_command_exits_as_documented(self):
        for line, declared in commands():
            if declared is None:
                continue                          # reported by the test above
            with self.subTest(command=line):
                code, out, err = run_command(line)
                self.assertEqual(code, declared,
                                 msg=f"{line}\nexit {code}, guide says {declared}\n"
                                     f"{out}\n{err}")

    def test_every_referenced_script_is_known_to_the_runner(self):
        """A new script in the guide must be registered here, not silently skipped."""
        for line, _ in commands():
            with self.subTest(command=line):
                self.assertIn(line.split()[1], SCRIPT_ARGV0)


class TestScenarioThreeTable(unittest.TestCase):
    """The fixture table is a list of claims about exit codes, in prose form."""

    def rows(self) -> list[tuple[str, int]]:
        text = QUICKSTART.read_text(encoding="utf-8")
        return [(m.group(1), int(m.group(2)))
                for m in (TABLE_ROW.match(ln) for ln in text.splitlines()) if m]

    def test_the_table_was_parsed(self):
        self.assertEqual(len(self.rows()), 7)

    def test_each_fixture_fails_as_the_table_says(self):
        rob = str(fixture("risk-of-bias.valid.json"))
        for name, expected in self.rows():
            with self.subTest(fixture=name):
                code, out, err = run_command(
                    f"python skills/validate-evidence/scripts/grade_profile.py "
                    f"tests/fixtures/{name} --rob {rob} --strict")
                self.assertEqual(code, expected, msg=f"{name}\n{out}\n{err}")

    def test_each_failure_is_its_own_failure(self):
        """"Each must fail for its own reason, not a generic one" — the guide's words.

        The cheapest way for this table to go quietly wrong is for a record to stop
        exercising its named defect and start tripping the basis-claimed-without-an
        -appraisal rule instead, which also exits 1. Supplying `--rob` removes that
        possibility; this asserts it stayed removed.
        """
        rob = str(fixture("risk-of-bias.valid.json"))
        for name, expected in self.rows():
            if expected != 1:
                continue
            with self.subTest(fixture=name):
                _, out, _ = run_command(
                    f"python skills/validate-evidence/scripts/grade_profile.py "
                    f"tests/fixtures/{name} --rob {rob} --strict")
                self.assertNotIn("no appraisal record was supplied", out)


if __name__ == "__main__":
    unittest.main()
