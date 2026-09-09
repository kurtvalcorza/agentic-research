"""The PRISMA reporting sub-gate's aggregation contract.

`aggregate()` is what `review_units.py` ends up ingesting, so the shape matters as
much as the arithmetic: `units` carries only what actually ran, `gates` carries
COUNTS under the one gate key the table assigns this check, and an absent child is
absent rather than zero.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from _load import load

vr = load("skills/verify-review/scripts/prisma_reporting_checks.py")


def env(check, units, gates=None, issues=0, detail=None):
    body = {
        "check": check,
        "schema_version": "1.0",
        "issues": issues,
        "units": units,
        "gates": gates or {},
        "unattributed": 0,
    }
    if detail is not None:
        body["detail"] = detail
    return body


def compliance(units=0, gate=0, issues=0):
    return env("prisma_compliance", {"U_prisma_compliance": units},
               {"H_prisma_evidence": gate}, issues=issues)


def abstract(units=0, gate=0, issues=0, verification="compliance"):
    return env("prisma_abstract_checklist", {"U_prisma_abstract": units},
               {"H_prisma_evidence": gate}, issues=issues,
               detail={"verification": verification})


def updated(units=0, issues=0):
    return env("prisma_updated_flow", {"U_prisma_updated": units}, {}, issues=issues)


class TestTheAggregateShape(unittest.TestCase):
    def test_a_compliance_only_run_reports_one_unit_and_the_gate(self):
        out = vr.aggregate(compliance())
        self.assertEqual({"U_prisma_compliance": 0}, out["units"])
        self.assertEqual({"H_prisma_evidence": 0}, out["gates"])
        self.assertEqual(vr.CHECK_NAME, out["check"])
        self.assertTrue(out["detail"]["not_certification"])

    def test_an_absent_child_is_absent_from_units_not_zero(self):
        """The distinction the earlier `gates: {"underived": [...]}` field tried to
        carry, now expressed where the consumer already models it: a unit the run
        did not derive is simply not reported, and `review_units.py` holds the
        verdict through its own `conditional_units` mapping."""
        out = vr.aggregate(compliance())
        self.assertNotIn("U_prisma_abstract", out["units"])
        self.assertNotIn("U_prisma_updated", out["units"])
        self.assertEqual(["U_prisma_abstract", "U_prisma_updated"],
                         out["detail"]["underived"])

    def test_every_child_reports_its_own_unit(self):
        out = vr.aggregate(compliance(units=3, issues=5), abstract(units=2, issues=2),
                           updated(units=4, issues=4))
        self.assertEqual(11, out["issues"])
        self.assertEqual({"U_prisma_compliance": 3, "U_prisma_abstract": 2,
                          "U_prisma_updated": 4}, out["units"])
        self.assertEqual([], out["detail"]["underived"])


class TestTheHumanGate(unittest.TestCase):
    def test_the_gate_sums_the_children_that_count_confirmations(self):
        out = vr.aggregate(compliance(gate=4), abstract(gate=2), updated())
        self.assertEqual(6, out["gates"]["H_prisma_evidence"])

    def test_pending_confirmations_survive_zero_repairable_defects(self):
        """The failure mode this gate exists for: every row located and evidenced,
        no unit outstanding, and not one confirmation given. Before the gate the two
        records were indistinguishable at the verdict."""
        out = vr.aggregate(compliance(units=0, gate=42, issues=42))
        self.assertEqual(0, out["units"]["U_prisma_compliance"])
        self.assertEqual(42, out["gates"]["H_prisma_evidence"])

    def test_an_addressability_abstract_record_is_refused(self):
        """Aggregating it would report a satisfied human gate over a record that
        never asserted compliance and so owes no confirmation."""
        with self.assertRaises(vr.InputError) as caught:
            vr.aggregate(compliance(), abstract(verification="addressability"))
        self.assertIn("compliance", str(caught.exception))


class TestChildOutputIsNotTrusted(unittest.TestCase):
    def test_a_child_claiming_another_identity_is_rejected(self):
        with self.assertRaises(vr.InputError):
            vr.aggregate(env("prisma_checklist", {"U_prisma_compliance": 0},
                             {"H_prisma_evidence": 0}))

    def test_a_negative_or_non_integer_count_is_rejected(self):
        for bad in (-1, 1.5, True, "0", None):
            with self.subTest(value=bad):
                with self.assertRaises(vr.InputError):
                    vr.aggregate(env("prisma_compliance", {"U_prisma_compliance": bad},
                                     {"H_prisma_evidence": 0}))

    def test_a_negative_issue_count_is_rejected(self):
        with self.assertRaises(vr.InputError):
            vr.aggregate(compliance(issues=-2))

    def test_a_child_that_drops_its_own_unit_is_not_read_as_clean(self):
        """Absent is not zero on the unit side."""
        with self.assertRaises(vr.InputError):
            vr.aggregate(env("prisma_compliance", {}, {"H_prisma_evidence": 0}))

    def test_a_child_with_no_confirmations_may_omit_the_gate(self):
        """The other half of the same rule: `prisma_updated_flow` has no
        confirmations to count and reports `gates: {}`, which is not a gap."""
        out = vr.aggregate(compliance(), None, updated())
        self.assertEqual(0, out["gates"]["H_prisma_evidence"])
        self.assertIn("U_prisma_updated", out["units"])


class SubGateHonoursTheOperatorsSkillsRootTests(unittest.TestCase):
    """The sub-gate is itself a runner, so it needs the same root as its parent.

    ``review_units.py`` resolves every check under ``--skills-root``. This check
    then shells out to prisma-flow, and it used to resolve those children relative
    to its own ``__file__`` instead. An operator who relocated the skills tree got a
    sub-gate that was found but whose children were not — a Principle III gap that
    only appears in exactly the layout the option exists to support.
    """

    def _compliance_record(self, directory):
        compliance = load("skills/prisma-flow/scripts/prisma_compliance.py")
        rows = [
            {
                "number": number,
                "location": f"Section for {number}",
                "evidence": f"Row {number} is reported in full in the manuscript.",
                "human_confirmed": True,
            }
            for _section, number, _topic in compliance.PRISMA_2020
        ]
        path = os.path.join(directory, "compliance.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"schema_version": "1.0", "variant": "prisma_2020", "items": rows}, handle)
        return path

    def test_default_root_is_this_scripts_own_siblings(self):
        self.assertEqual(vr.DEFAULT_PRISMA_SCRIPTS, vr.prisma_scripts_dir(None))

    def test_explicit_root_is_the_parent_of_a_skills_directory(self):
        self.assertEqual(
            pathlib.Path("/somewhere/skills/prisma-flow/scripts").resolve(),
            vr.prisma_scripts_dir("/somewhere"),
        )

    def test_children_resolve_under_a_relocated_skills_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "elsewhere")
            os.makedirs(os.path.join(root, "skills"))
            shutil.copytree("skills/prisma-flow", os.path.join(root, "skills", "prisma-flow"))
            # The sub-gate is copied out on its own: without the option its siblings
            # are genuinely absent, which is the negative control for this test.
            lonely = os.path.join(tmp, "prisma_reporting_checks.py")
            shutil.copy("skills/verify-review/scripts/prisma_reporting_checks.py", lonely)
            record = self._compliance_record(tmp)

            without = subprocess.run(
                [sys.executable, lonely, record, "--json"],
                capture_output=True, text=True,
            )
            self.assertEqual(2, without.returncode, without.stdout)
            self.assertIn("no sibling skills", without.stderr)

            with_root = subprocess.run(
                [sys.executable, lonely, record, "--json", "--skills-root", root],
                capture_output=True, text=True,
            )
            self.assertEqual(0, with_root.returncode, with_root.stderr)
            envelope = json.loads(with_root.stdout)
            self.assertEqual(0, envelope["units"]["U_prisma_compliance"])

    def test_the_runner_passes_its_own_root_to_this_check(self):
        core = load("skills/verify-review/scripts/review_units_core.py")
        self.assertTrue(core.CHECK_TABLE["prisma_reporting_checks"].get("passes_skills_root"))
        runner = core.CheckRunner(records_root=".", skills_root="/a/root")
        self.assertEqual(pathlib.Path("/a/root"), runner.skills_root)
        # Only the sub-gate takes the root, because it is the only check that runs
        # other checks. A leaf check receiving it would be given an option it does
        # not accept, so the argv would fail at the child rather than here.
        self.assertEqual(
            {"prisma_reporting_checks"},
            {name for name, spec in core.CHECK_TABLE.items()
             if spec.get("passes_skills_root")},
        )

    def test_argv_carries_the_root_when_the_script_is_present(self):
        core = load("skills/verify-review/scripts/review_units_core.py")
        runner = core.CheckRunner(records_root=".", skills_root=".")
        argv = runner.argv_for(
            "prisma_reporting_checks",
            {"record": "skills/verify-review/scripts/prisma_reporting_checks.py"},
        )
        self.assertIn("--skills-root", argv)
        self.assertEqual(str(pathlib.Path(".")), argv[argv.index("--skills-root") + 1])


if __name__ == "__main__":
    unittest.main()
