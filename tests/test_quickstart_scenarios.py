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

# ANY fenced block, whatever its info string. Matching only ```bash meant a
# scenario written in a ```sh or ```console fence was invisible to this runner —
# a module whose whole purpose is "an unchecked command fails the suite" must not
# have a way to opt out of it by accident.
CODE_BLOCK = re.compile(r"^```[^\n]*\n(.*?)^```", re.S | re.M)
# `# exit N` on the command itself or on a continuation line beneath it, and the
# `echo $?    # N` idiom the guide also uses.
EXIT_COMMENT = re.compile(r"#\s*exit\s+(\d+)")
ECHO_STATUS = re.compile(r"^\s*echo \$\?\s*#\s*(\d+)")

# Any invocation of a skill script, however it is spelled: `python3`, an env
# prefix, extra whitespace, a leading indent, or a pipeline stage. Recognising it
# is deliberately separate from being able to RUN it — see run_command, which
# fails on a form it cannot execute rather than passing over it.
INVOCATION = re.compile(r"(?<![\w./-])(skills/[\w-]+/scripts/\w+\.py)")
PYTHON_HEAD = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*python[0-9.]*\s")
# Shell constructs this runner cannot honour in-process. A documented command
# using one is not skipped; it fails, naming what to do about it.
SHELL_METACHARS = ("|", "<", ">", ";", "&", "`", "$(")

SCRIPT_ARGV0 = {
    "skills/validate-evidence/scripts/grade_profile.py": "grade_profile.py",
    "skills/appraise-risk-of-bias/scripts/rob_appraisal.py": "rob_appraisal.py",
    "skills/prisma-flow/scripts/prisma_checklist.py": "prisma_checklist.py",
    "skills/prisma-flow/scripts/prisma_flow.py": "prisma_flow.py",
    "skills/verify-review/scripts/review_units.py": "review_units.py",
}

# Scenario 3's table: fixture -> the exit the guide claims. Parsed from the table
# itself rather than restated here, so editing one without the other is caught.
# Deliberately NOT anchored to a fixture-name prefix: a row this pattern cannot
# read is an unchecked claim, and pinning the prefix made such a row invisible
# while the "did we parse the table" guard still passed.
TABLE_ROW = re.compile(r"^\|\s*`([^`]+\.json)`\s*\|\s*(\d)\s*\|")
ANY_TABLE_ROW = re.compile(r"^\|(?!\s*:?-)(?!\s*Fixture)\s*\S")


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
    """Every skill-script invocation in the guide, with its declared exit."""
    found: list[tuple[str, int]] = []
    for block in CODE_BLOCK.findall(QUICKSTART.read_text(encoding="utf-8")):
        lines = _logical_lines(block)
        for i, line in enumerate(lines):
            if not INVOCATION.search(line.split("#", 1)[0]):
                continue
            declared = None
            # The declaration may sit on the command, on a comment-only line under
            # it, or in the `echo $?` idiom the guide uses in Scenario 2.
            for candidate in (line, *lines[i + 1:i + 3]):
                if INVOCATION.search(candidate.split("#", 1)[0]):
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


class Unrunnable(AssertionError):
    """A documented command this runner cannot execute in-process.

    Raised rather than skipped. A command the runner quietly passes over is an
    unchecked claim in the guide, which is the exact failure this module exists to
    prevent — so an unsupported form has to break the suite and say what to do.
    """


def run_command(line: str) -> tuple[int, str, str]:
    """Run one documented invocation in-process, from the repository root."""
    body = line.split("#", 1)[0].strip()
    for meta in SHELL_METACHARS:
        if meta in body:
            raise Unrunnable(
                f"cannot run in-process (contains {meta!r}): {body}\n"
                f"Either write the scenario as a plain invocation, or extend "
                f"tests/test_quickstart_scenarios.py to execute this form.")
    if not PYTHON_HEAD.match(body):
        raise Unrunnable(
            f"not a plain `python <script> ...` invocation: {body}\n"
            f"The runner executes the script in-process, so the command must "
            f"start with python (an env-var prefix is allowed).")
    # Drop the interpreter and any env-var prefix; what remains is script + args.
    parts = body.split()
    while parts and not parts[0].startswith("python"):
        parts.pop(0)
    parts.pop(0)
    script, *raw_args = parts
    if script not in SCRIPT_ARGV0:
        raise Unrunnable(f"unregistered script {script!r} — add it to SCRIPT_ARGV0")
    args = []
    for raw in raw_args:
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
                for script in INVOCATION.findall(line.split("#", 1)[0]):
                    self.assertIn(script, SCRIPT_ARGV0)

    def test_an_unrunnable_form_fails_rather_than_being_skipped(self):
        """The runner's own fail-closed property, asserted rather than assumed.

        Every form below names a real skill script, so each is a claim the guide
        would be making. Recognising a command and being unable to run it must
        raise, because the alternative — passing over it — is how a runner ends up
        reporting green on documentation it never executed.
        """
        for form in (
            "cat rec.json | python skills/prisma-flow/scripts/prisma_flow.py",
            "python skills/prisma-flow/scripts/prisma_flow.py rec.json > out.md",
            "./skills/prisma-flow/scripts/prisma_flow.py rec.json",
            "python skills/made-up/scripts/nonexistent.py rec.json",
        ):
            with self.subTest(form=form):
                with self.assertRaises(Unrunnable):
                    run_command(form)

    def test_alternative_spellings_are_still_recognised(self):
        """`python3`, an env prefix and an indent are the same claim as `python`."""
        for form in (
            "python3 skills/prisma-flow/scripts/prisma_flow.py",
            "  PYTHONWARNINGS=error python skills/prisma-flow/scripts/prisma_flow.py",
        ):
            with self.subTest(form=form):
                self.assertTrue(INVOCATION.search(form))
                # Reaches the script rather than being rejected as unrunnable.
                code, _, _ = run_command(form + " " + str(fixture("checklist.valid.json")))
                self.assertIn(code, (0, 1, 2))


class TestScenarioThreeTable(unittest.TestCase):
    """The fixture table is a list of claims about exit codes, in prose form."""

    def table_lines(self) -> list[str]:
        """The data rows of Scenario 3's table, as written."""
        text = QUICKSTART.read_text(encoding="utf-8")
        section = text.split("## Scenario 3", 1)[1].split("\n## ", 1)[0]
        return [ln for ln in section.splitlines() if ANY_TABLE_ROW.match(ln)]

    def rows(self) -> list[tuple[str, int]]:
        return [(m.group(1), int(m.group(2)))
                for m in (TABLE_ROW.match(ln) for ln in self.table_lines()) if m]

    def test_every_row_in_the_table_is_parsed(self):
        """A row this module cannot read is an unchecked claim.

        Counting only the rows that parsed made the guard self-fulfilling: a row
        the pattern could not read never entered the count, so the count still
        matched and the row went unrun. Compare against the rows actually PRESENT.
        """
        self.assertEqual(len(self.rows()), len(self.table_lines()),
                         "some rows of Scenario 3's table were not parsed:\n  "
                         + "\n  ".join(self.table_lines()))
        self.assertGreaterEqual(len(self.rows()), 7)

    def test_every_row_names_a_certainty_fixture(self):
        """Scenario 3 runs grade_profile.py, so a row naming another record type is
        a claim this runner would silently mis-execute. Fail instead."""
        for name, _ in self.rows():
            with self.subTest(fixture=name):
                self.assertTrue(name.startswith("grade-profile."),
                                f"{name} is not a certainty record; Scenario 3 runs "
                                f"grade_profile.py over every row")
                self.assertTrue(fixture(name).is_file(), f"{name} does not exist")

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
