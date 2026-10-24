"""`council-adversary-read.ps1` fails closed and reads runner exit codes.

The Council Mode fan-out script used to exit 0 for an empty or malformed job spec
("0 of 0 personas OK") and for a run where every runner failed, and it never read
a runner's exit code. The constitution's fail-closed principle and exit-code
contract say otherwise, so this module pins:

- malformed input (missing/unparseable spec, unknown keys, missing or non-string
  required fields, empty `personas`, unknown runner, more than 26 personas) exits 2
  and writes nothing;
- a run where no persona returns a usable read exits 1;
- a runner's non-zero exit code marks its read UNAVAILABLE even when the text looks
  valid;
- a partial council exits 0, or 1 under `-Strict`.

Every runner CLI (`gemini`, `codex`, `cursor-agent`) is replaced by a stub in a
directory placed FIRST on PATH, so an installed real runner can never be reached:
no network, no quota, no model output. What this cannot verify: a real runner's
behaviour. Skipped when PowerShell 7 (`pwsh`) is not installed.

Standard library only.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "tools-for-thought" / "scripts" / "council-adversary-read.ps1"
PWSH = shutil.which("pwsh")
RUNNER_COMMANDS = ("gemini", "codex", "cursor-agent")

PERSONA = {"label": "L", "runner": "gemini", "brief": "b", "voiceAsk": "v"}
VALID = {"artifact": "a", "coreClaim": "c", "personas": [PERSONA]}

# Stub behaviours: (print a well-formed read?, exit code)
VALID_READ = ("**What you care about (1 sentence):** x", "**Primary attack vector:** y")
STUBS = {
    "ok": (True, 0),
    "fail": (False, 7),
    "valid_text_exit_3": (True, 3),
}


def _write_stub(directory: pathlib.Path, command: str, behaviour: str) -> None:
    prints_read, code = STUBS[behaviour]
    if os.name == "nt":
        # `more >nul` drains stdin, as `codex exec` reads its prompt from there.
        lines = ["@echo off", "more >nul"]
        lines += [f"echo {line}" for line in VALID_READ] if prints_read else []
        lines.append(f"exit /b {code}")
        (directory / f"{command}.cmd").write_text("\r\n".join(lines) + "\r\n", encoding="ascii")
    else:
        lines = ["#!/bin/sh", "cat >/dev/null"]
        lines += [f"printf '%s\\n' '{line}'" for line in VALID_READ] if prints_read else []
        lines.append(f"exit {code}")
        path = directory / command
        path.write_text("\n".join(lines) + "\n", encoding="ascii")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@unittest.skipUnless(PWSH, "PowerShell 7 (pwsh) not installed")
class TestCouncilFailsClosed(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.stubs = self.tmp / "stubs"
        self.stubs.mkdir()
        self.use_stubs()

    def use_stubs(self, **behaviours: str) -> None:
        """Stub every runner; unnamed ones fail. Keys use `_` for `-`."""
        for command in RUNNER_COMMANDS:
            behaviour = behaviours.get(command.replace("-", "_"), "fail")
            _write_stub(self.stubs, command, behaviour)

    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        # Stubs first: they shadow any real runner later on PATH.
        env["PATH"] = os.pathsep.join([str(self.stubs), str(pathlib.Path(PWSH).parent), env.get("PATH", "")])
        return env

    def _run(self, spec_text: str, *extra: str) -> tuple[int, pathlib.Path, str]:
        spec = self.tmp / "job spec.json"  # space on purpose: paths with spaces must work
        spec.write_text(spec_text, encoding="utf-8")
        out = self.tmp / "out" / "reads.md"
        proc = subprocess.run(
            [PWSH, "-NoProfile", "-File", str(SCRIPT),
             "-JobSpec", str(spec), "-OutFile", str(out), "-TimeoutSec", "60", *extra],
            capture_output=True, text=True, env=self._env(), timeout=180,
        )
        return proc.returncode, out, proc.stderr

    def _status(self, out: pathlib.Path) -> dict:
        return json.loads((out.parent / (out.name + ".status.json")).read_text(encoding="utf-8-sig"))

    def assert_malformed(self, spec_text: str, message: str) -> None:
        code, out, stderr = self._run(spec_text)
        self.assertEqual(code, 2, stderr)
        self.assertIn(message, stderr)
        self.assertFalse(out.exists(), "nothing may be written for malformed input")

    # --- malformed input: exit 2, nothing written -------------------------

    def test_empty_file(self):
        self.assert_malformed("", "top level must be a JSON object")

    def test_invalid_json(self):
        self.assert_malformed("{not json", "not valid JSON")

    def test_unknown_top_level_key(self):
        self.assert_malformed(json.dumps({**VALID, "extra": 1}), "unknown key 'extra'")

    def test_missing_artifact(self):
        spec = {k: v for k, v in VALID.items() if k != "artifact"}
        self.assert_malformed(json.dumps(spec), "'artifact' must be a non-empty string")

    def test_non_string_artifact(self):
        self.assert_malformed(json.dumps({**VALID, "artifact": {"x": 1}}), "'artifact' must be a non-empty string")

    def test_non_string_assumption(self):
        self.assert_malformed(json.dumps({**VALID, "assumptions": [3]}), "'assumptions' entries must be non-empty strings")

    def test_empty_personas(self):
        self.assert_malformed(json.dumps({**VALID, "personas": []}), "'personas' must be a non-empty array")

    def test_persona_missing_runner(self):
        persona = {k: v for k, v in PERSONA.items() if k != "runner"}
        self.assert_malformed(json.dumps({**VALID, "personas": [persona]}), "persona 1: 'runner' must be a non-empty string")

    def test_numeric_runner(self):
        persona = {**PERSONA, "runner": 5}
        self.assert_malformed(json.dumps({**VALID, "personas": [persona]}), "persona 1: 'runner' must be a non-empty string")

    def test_non_string_brief(self):
        persona = {**PERSONA, "brief": {"b": 1}}
        self.assert_malformed(json.dumps({**VALID, "personas": [persona]}), "persona 1: 'brief' must be a non-empty string")

    def test_persona_unknown_key(self):
        persona = {**PERSONA, "temperature": 0}
        self.assert_malformed(json.dumps({**VALID, "personas": [persona]}), "persona 1: unknown key 'temperature'")

    def test_unknown_runner(self):
        persona = {**PERSONA, "runner": "llama"}
        self.assert_malformed(json.dumps({**VALID, "personas": [persona]}), "unknown runner 'llama'")

    def test_more_than_26_personas(self):
        self.assert_malformed(json.dumps({**VALID, "personas": [PERSONA] * 27}), "at most 26 personas")

    # --- dispatched runs ----------------------------------------------------

    def test_usable_read_exits_0(self):
        self.use_stubs(gemini="ok")
        code, out, stderr = self._run(json.dumps(VALID))
        self.assertEqual(code, 0, stderr)
        status = self._status(out)
        self.assertEqual((status["total"], status["ok"]), (1, 1))
        self.assertEqual(status["personas"][0]["status"], "OK")

    def test_no_usable_read_exits_1(self):
        code, out, stderr = self._run(json.dumps(VALID))
        self.assertEqual(code, 1, stderr)
        status = self._status(out)
        self.assertEqual((status["total"], status["ok"]), (1, 0))
        self.assertEqual(status["personas"][0]["reason"], "runner exited 7")
        self.assertIn("NO USABLE READS", out.read_text(encoding="utf-8-sig"))

    def test_nonzero_exit_overrides_valid_looking_text(self):
        # The text would pass the section-header check; only the exit code can reject it.
        self.use_stubs(gemini="valid_text_exit_3")
        code, out, stderr = self._run(json.dumps(VALID))
        self.assertEqual(code, 1, stderr)
        persona = self._status(out)["personas"][0]
        self.assertEqual((persona["status"], persona["reason"]), ("UNAVAILABLE", "runner exited 3"))

    def test_codex_reads_prompt_from_stdin(self):
        self.use_stubs(codex="ok")
        spec = {**VALID, "personas": [{**PERSONA, "runner": "codex"}]}
        code, out, stderr = self._run(json.dumps(spec))
        self.assertEqual(code, 0, stderr)
        self.assertEqual(self._status(out)["personas"][0]["status"], "OK")

    def test_partial_council_exits_0_without_strict(self):
        self.use_stubs(gemini="ok")
        spec = {**VALID, "personas": [PERSONA, {**PERSONA, "runner": "codex"}]}
        code, out, stderr = self._run(json.dumps(spec))
        self.assertEqual(code, 0, stderr)
        status = self._status(out)
        self.assertEqual((status["total"], status["ok"]), (2, 1))

    def test_partial_council_exits_1_under_strict(self):
        self.use_stubs(gemini="ok")
        spec = {**VALID, "personas": [PERSONA, {**PERSONA, "runner": "codex"}]}
        code, _, stderr = self._run(json.dumps(spec), "-Strict")
        self.assertEqual(code, 1, stderr)

    def test_complete_council_exits_0_under_strict(self):
        self.use_stubs(gemini="ok", codex="ok")
        spec = {**VALID, "personas": [PERSONA, {**PERSONA, "runner": "codex"}]}
        code, _, stderr = self._run(json.dumps(spec), "-Strict")
        self.assertEqual(code, 0, stderr)


if __name__ == "__main__":
    unittest.main()
