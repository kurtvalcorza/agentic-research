"""`--json` on all four checks — the machine-readable counts envelope.

`cli-contract.md` binds every check to the same CLI behaviour, and this adds one
more clause to it: a check must be able to report its counts as data, not only as
prose. A consumer parsing the rendered artifact would be fragile even though the
format is golden-tested, and a consumer RE-DERIVING a count from the diagnostics
would be a second definition of the unit — one result raises four messages, so
counting messages books four units of work for one broken result.

So each check EMITS the number it defines. This module pins that the four agree on
the envelope, that `--json` changes the rendering and nothing else, and that the two
counts which are not simply "how many diagnostics" are computed correctly.

Nothing here consumes the envelope. Deriving `units.json` counts by running these
checks is a separate change (issue #4) on its own branch; this one only makes the
checks capable of being consumed.

Standard library only.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import fixture  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent

# The envelope version, written out rather than imported. The consumer that
# validates it does not exist on this branch, and a test importing the constant
# from the code under test would pass for any value the code happened to hold.
ENVELOPE_VERSION = "1.0"

# check -> (script, argv producing a CLEAN result, units it may report, gates it may report)
CHECKS = {
    "prisma_flow": ("skills/prisma-flow/scripts/prisma_flow.py",
                    [str(fixture("counts.valid.json"))], {"U_prisma"}, set()),
    "prisma_checklist": ("skills/prisma-flow/scripts/prisma_checklist.py",
                         [str(fixture("checklist.valid.json"))], {"U_checklist"}, set()),
    "grade_profile": ("skills/validate-evidence/scripts/grade_profile.py",
                      [str(fixture("grade-profile.valid.json")),
                       "--rob", str(fixture("risk-of-bias.contract-example.json"))],
                      {"U_grade", "U_rob_trace"}, set()),
    "rob_appraisal": ("skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
                      [str(fixture("risk-of-bias.contract-example.json"))],
                      set(), {"H_rob"}),
}


def run_script(rel: str, *args: str):
    """Run a check as a real subprocess and return (exit code, stdout, stderr)."""
    proc = subprocess.run([sys.executable, str(REPO / rel), *args],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout, proc.stderr


class TestEveryCheckSpeaksTheEnvelope(unittest.TestCase):
    """`--json` is binding on all four, like `--strict` before it."""

    def envelope(self, name):
        rel, args, _, _ = CHECKS[name]
        code, out, err = run_script(rel, *args, "--strict", "--json")
        self.assertIn(code, (0, 1), msg=err)
        return json.loads(out)

    def test_every_check_accepts_json_and_emits_the_envelope(self):
        for name in CHECKS:
            with self.subTest(check=name):
                env = self.envelope(name)
                self.assertEqual(env["check"], name)
                self.assertEqual(env["schema_version"], ENVELOPE_VERSION)
                for key in ("issues", "units", "gates", "unattributed"):
                    self.assertIn(key, env)

    def test_a_check_reports_only_the_counts_that_are_its_own(self):
        """A check claiming a unit outside its remit would let one record's counts
        overwrite another's in any consumer that merges them."""
        for name, (_, _, units, gates) in CHECKS.items():
            with self.subTest(check=name):
                env = self.envelope(name)
                self.assertLessEqual(set(env["units"]), units)
                self.assertLessEqual(set(env["gates"]), gates)

    def test_json_replaces_the_artifact_rather_than_joining_it(self):
        """Stdout must be JSON and nothing else — a consumer parses the whole stream."""
        for name in CHECKS:
            with self.subTest(check=name):
                rel, args, _, _ = CHECKS[name]
                _, out, _ = run_script(rel, *args, "--strict", "--json")
                self.assertNotIn("```mermaid", out)
                # The checklist artifact's real table header. "| Item |" was a
                # sentinel no check emits, so the assertion could never fire.
                self.assertNotIn("| Section | # | Topic |", out)
                json.loads(out)          # the whole stream, not a prefix of it

    def test_json_does_not_change_the_exit_code(self):
        """The exit-code contract is `cli-contract.md`'s, and `--json` is an output
        format. A check that exited differently with it would make the flag change
        the verdict rather than the rendering, and no invocation could adopt it
        safely."""
        cases = [("skills/prisma-flow/scripts/prisma_flow.py",
                  [str(fixture("counts.valid.json"))]),
                 ("skills/prisma-flow/scripts/prisma_checklist.py",
                  [str(fixture("checklist.partial.json"))]),
                 ("skills/prisma-flow/scripts/prisma_checklist.py",
                  [str(fixture("checklist.unknown-number.json"))]),
                 ("skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
                  [str(fixture("risk-of-bias.unconfirmed.json"))]),
                 ("skills/validate-evidence/scripts/grade_profile.py",
                  [str(fixture("grade-profile.bad-arithmetic.json"))])]
        for rel, args in cases:
            with self.subTest(script=rel, record=args[0]):
                plain, _, _ = run_script(rel, *args, "--strict")
                as_json, _, _ = run_script(rel, *args, "--strict", "--json")
                self.assertEqual(plain, as_json)

    def test_malformed_input_emits_no_envelope(self):
        """Exit 2 means the record was never evaluated. An envelope of zeros there
        is the shape a consumer trusts, carrying counts nothing produced — the
        single worst output this contract could permit."""
        code, out, err = run_script("skills/prisma-flow/scripts/prisma_checklist.py",
                                    str(fixture("checklist.unknown-number.json")),
                                    "--strict", "--json")
        self.assertEqual(code, 2)
        self.assertEqual(out.strip(), "")
        self.assertTrue(err.strip())


class TestTheFlowCheckCountsWhatItCouldNotReach(unittest.TestCase):
    """`U_prisma` is failures PLUS unreached stages, and the second term is the
    whole point.

    Issue #9 stopped the artifact printing ✅ over a flow nothing had examined. A
    `U_prisma` counting only reconciliation failures would put that same fail-open
    back — this time in the number a consumer reads, where no reader would see it.
    """

    def envelope(self, name):
        code, out, err = run_script("skills/prisma-flow/scripts/prisma_flow.py",
                                    str(fixture(name)), "--strict", "--json")
        self.assertIn(code, (0, 1), msg=err)
        return json.loads(out)

    def test_a_reconciling_record_reports_zero(self):
        env = self.envelope("counts.valid.json")
        self.assertEqual(env["units"]["U_prisma"], 0)
        self.assertEqual(env["detail"]["unreached_stages"], [])

    def test_a_record_naming_only_two_ends_is_not_zero(self):
        env = self.envelope("counts.two-ends-only.json")
        self.assertEqual(env["issues"], 0)             # nothing FAILED …
        self.assertEqual(env["units"]["U_prisma"], 5)  # … because nothing was checked
        self.assertEqual(env["detail"]["checked_stages"], [])

    def test_the_artifact_and_the_envelope_agree(self):
        """Both are derived from one reconciliation, so a record the artifact
        reports as fully checked cannot be one the envelope books work for."""
        _, artifact, _ = run_script("skills/prisma-flow/scripts/prisma_flow.py",
                                    str(fixture("counts.valid.json")), "--strict")
        self.assertIn("5 of 5 stages checked", artifact)
        self.assertEqual(self.envelope("counts.valid.json")["units"]["U_prisma"], 0)


class TestTheCertaintyCheckCountsReferences(unittest.TestCase):
    """`U_rob_trace` counts unresolved REFERENCES, not diagnostics naming them.

    Three unresolved studies raise one message listing all three. Counting messages
    would book one unit of work for three broken references — the same error
    `U_grade` was defined around when it moved from diagnostics to failing results.
    """

    def profile(self, **changes):
        rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
        rec["results"][0].update(changes)
        return rec

    def envelope(self, rec, with_rob=True):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "rec.json"
            p.write_text(json.dumps(rec), encoding="utf-8")
            rob = ["--rob", str(fixture("risk-of-bias.contract-example.json"))] if with_rob else []
            code, out, err = run_script(
                "skills/validate-evidence/scripts/grade_profile.py", str(p),
                *rob, "--strict", "--json")
        self.assertIn(code, (0, 1), msg=err)
        return json.loads(out)

    def test_a_resolving_record_reports_zero(self):
        self.assertEqual(self.envelope(self.profile())["units"]["U_rob_trace"], 0)

    def test_every_reference_counts_when_the_target_is_unknown(self):
        """A target that names nothing means NONE of the references resolve.

        Reporting 0 here would say the traceability was clean when in truth it
        could not be attempted — the difference between "checked and fine" and
        "never checked" this whole suite turns on.
        """
        rec = self.profile(appraised_result="a result nobody appraised")
        env = self.envelope(rec)
        n_refs = len(rec["results"][0]["study_ids"])
        self.assertGreater(n_refs, 0)
        self.assertEqual(env["units"]["U_rob_trace"], n_refs)

    def test_an_unknown_study_reference_counts_once(self):
        """One reference REPLACED, not appended: adding one would also break
        design_mix, and a fixture with two defects cannot prove which one produced
        the count."""
        ids = list(self.profile()["results"][0]["study_ids"])
        env = self.envelope(self.profile(study_ids=[*ids[:-1], "S_not_in_the_appraisal"]))
        self.assertEqual(env["units"]["U_rob_trace"], 1)

    def test_the_unit_is_absent_without_an_appraisal_record(self):
        """No `--rob`, no traceability. Emitting 0 would claim every reference
        resolved; the unit must simply not be reported."""
        env = self.envelope(self.profile(), with_rob=False)
        self.assertIn("U_grade", env["units"])
        self.assertNotIn("U_rob_trace", env["units"])


class TestTheAppraisalCheckDoesNotCountASignatureTwice(unittest.TestCase):
    def test_a_pending_confirmation_is_the_gate_and_nothing_else(self):
        """`H_rob` counts it, so `unattributed` must not.

        Counting it in both would put every pending signature into a bucket no
        human can clear, so a record whose only fault was an unsigned appraisal
        could never reach the hand-off state that fault exists to produce.
        """
        code, out, err = run_script(
            "skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
            str(fixture("risk-of-bias.unconfirmed.json")), "--strict", "--json")
        self.assertEqual(code, 1, msg=err)
        env = json.loads(out)
        self.assertEqual(env["gates"]["H_rob"], 1)
        self.assertEqual(env["issues"], 1)
        self.assertEqual(env["unattributed"], 0)

    def test_a_method_violation_is_unattributed(self):
        """No unit counts an appraisal its own instrument rejects, so it would
        vanish entirely if `unattributed` did not report it."""
        code, out, err = run_script(
            "skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
            str(fixture("risk-of-bias.wrong-instrument.json")), "--strict", "--json")
        self.assertEqual(code, 1, msg=err)
        env = json.loads(out)
        self.assertEqual(env["units"], {})
        self.assertGreater(env["unattributed"], 0)

    def test_this_check_produces_no_auto_reducible_unit(self):
        """A human gate is not work a loop can clear, so `units` is empty by
        design rather than by omission."""
        code, out, _ = run_script(
            "skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
            str(fixture("risk-of-bias.contract-example.json")), "--strict", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["units"], {})


if __name__ == "__main__":
    unittest.main()
