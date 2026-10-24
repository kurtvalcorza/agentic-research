"""`council-adversary-read.ps1` fails closed.

The Council Mode fan-out script used to exit 0 for an empty or malformed job spec
("0 of 0 personas OK") and for a run where every runner failed. The constitution's
fail-closed principle and exit-code contract say otherwise, so this module pins:

- malformed input (missing/unparseable spec, unknown keys, missing required fields,
  empty `personas`, unknown runner, more than 26 personas) exits 2 and dispatches
  nothing;
- a run where no persona returns a usable read exits 1.

What this cannot verify: a real runner's behaviour. No runner CLI is reachable on
the PATH given to the script, so every dispatched persona is UNAVAILABLE by
construction. Skipped when PowerShell 7 (`pwsh`) is not installed.

Standard library only.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "tools-for-thought" / "scripts" / "council-adversary-read.ps1"
PWSH = shutil.which("pwsh")

PERSONA = {"label": "L", "runner": "gemini", "brief": "b", "voiceAsk": "v"}
VALID = {"artifact": "a", "coreClaim": "c", "personas": [PERSONA]}


def _isolated_env() -> dict[str, str]:
    """PATH holding only pwsh and the OS, so no runner CLI can be found."""
    env = dict(os.environ)
    dirs = [str(pathlib.Path(PWSH).parent)]
    system_root = os.environ.get("SystemRoot")
    if system_root:
        dirs.append(str(pathlib.Path(system_root) / "System32"))
    else:
        dirs += ["/usr/bin", "/bin"]
    env["PATH"] = os.pathsep.join(dirs)
    return env


@unittest.skipUnless(PWSH, "PowerShell 7 (pwsh) not installed")
class TestCouncilFailsClosed(unittest.TestCase):

    def _run(self, spec_text: str) -> tuple[int, pathlib.Path, str]:
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        spec = tmp / "job spec.json"  # space on purpose: paths with spaces must work
        spec.write_text(spec_text, encoding="utf-8")
        out = tmp / "out" / "reads.md"
        proc = subprocess.run(
            [PWSH, "-NoProfile", "-File", str(SCRIPT),
             "-JobSpec", str(spec), "-OutFile", str(out), "-TimeoutSec", "60"],
            capture_output=True, text=True, env=_isolated_env(), timeout=180,
        )
        return proc.returncode, out, proc.stderr

    def assert_malformed(self, spec_text: str, message: str) -> None:
        code, out, stderr = self._run(spec_text)
        self.assertEqual(code, 2, stderr)
        self.assertIn(message, stderr)
        self.assertFalse(out.exists(), "nothing may be written for malformed input")

    def test_empty_file(self):
        self.assert_malformed("", "top level must be a JSON object")

    def test_invalid_json(self):
        self.assert_malformed("{not json", "not valid JSON")

    def test_unknown_top_level_key(self):
        self.assert_malformed(json.dumps({**VALID, "extra": 1}), "unknown key 'extra'")

    def test_missing_artifact(self):
        spec = {k: v for k, v in VALID.items() if k != "artifact"}
        self.assert_malformed(json.dumps(spec), "missing or empty 'artifact'")

    def test_empty_personas(self):
        self.assert_malformed(json.dumps({**VALID, "personas": []}), "'personas' must be a non-empty array")

    def test_persona_missing_runner(self):
        persona = {k: v for k, v in PERSONA.items() if k != "runner"}
        self.assert_malformed(json.dumps({**VALID, "personas": [persona]}), "persona 1: missing or empty 'runner'")

    def test_persona_unknown_key(self):
        persona = {**PERSONA, "temperature": 0}
        self.assert_malformed(json.dumps({**VALID, "personas": [persona]}), "persona 1: unknown key 'temperature'")

    def test_unknown_runner(self):
        persona = {**PERSONA, "runner": "llama"}
        self.assert_malformed(json.dumps({**VALID, "personas": [persona]}), "unknown runner 'llama'")

    def test_more_than_26_personas(self):
        self.assert_malformed(json.dumps({**VALID, "personas": [PERSONA] * 27}), "at most 26 personas")

    def test_no_usable_read_exits_1(self):
        code, out, stderr = self._run(json.dumps(VALID))
        self.assertEqual(code, 1, stderr)
        status = json.loads((out.parent / (out.name + ".status.json")).read_text(encoding="utf-8-sig"))
        self.assertEqual((status["total"], status["ok"]), (1, 0))
        self.assertEqual(status["personas"][0]["status"], "UNAVAILABLE")
        self.assertIn("NO USABLE READS", out.read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
