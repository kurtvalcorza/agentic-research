"""Portability checks for the bundled Claude Code Speckit skills."""
from __future__ import annotations

import pathlib
import re
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / ".claude" / "skills"
SCRIPT_ROOT = REPO_ROOT / ".specify" / "scripts"
DIRECT_PS1 = re.compile(
    r"(?<!pwsh )\.specify/scripts/powershell/[A-Za-z0-9.-]+\.ps1"
)
PS1_REFERENCE = re.compile(
    r"\.specify/scripts/powershell/(?P<name>[A-Za-z0-9.-]+)\.ps1"
)


class TestPowerShellInvocation(unittest.TestCase):
    def test_scripts_are_invoked_through_pwsh(self):
        """Non-executable 100644 .ps1 files cannot be launched directly on Unix."""
        direct = []
        references = 0
        for path in sorted(SKILL_ROOT.rglob("SKILL.md")):
            text = path.read_text(encoding="utf-8")
            references += text.count(".ps1")
            for match in DIRECT_PS1.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                direct.append(f"{path.relative_to(REPO_ROOT)}:{line}")

        self.assertGreaterEqual(references, 8, "expected downstream Speckit setup scripts")
        self.assertEqual(
            direct,
            [],
            "PowerShell scripts must be invoked as `pwsh <script>` so the skills "
            "work on Unix and Linux:\n" + "\n".join(direct),
        )

    def test_shell_backend_is_bundled_for_unix_hosts(self):
        expected = {
            "common.sh",
            "check-prerequisites.sh",
            "create-new-feature.sh",
            "setup-plan.sh",
            "setup-tasks.sh",
        }
        self.assertEqual(
            {path.name for path in (SCRIPT_ROOT / "bash").glob("*.sh")},
            expected,
        )

    def test_every_documented_powershell_setup_has_a_shell_alternative(self):
        missing = []
        references = 0
        for path in sorted(SKILL_ROOT.rglob("SKILL.md")):
            text = path.read_text(encoding="utf-8")
            for match in PS1_REFERENCE.finditer(text):
                references += 1
                shell_command = (
                    f"bash .specify/scripts/bash/{match.group('name')}.sh"
                )
                if shell_command not in text:
                    missing.append(
                        f"{path.relative_to(REPO_ROOT)} -> {shell_command}"
                    )

        self.assertGreaterEqual(references, 8)
        self.assertEqual(
            missing,
            [],
            "Every Windows setup command must document its bundled Unix "
            "alternative:\n" + "\n".join(missing),
        )


if __name__ == "__main__":
    unittest.main()
