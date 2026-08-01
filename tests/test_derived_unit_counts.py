"""Issue #4 — verify-review derives unit counts by RUNNING the checks.

Before this, `review_units.py` computed a verdict from the counts it was handed. It
never ran a check, never located an artifact, and never confirmed a count came from
a real run, so a hand-written `units.json` of all zeros reached VERIFIED. The
enforcement was real at the point a check ran and an assertion at the point the
verdict was computed.

Two halves are tested here and they fail in opposite directions:

  * The four checks must EMIT their counts machine-readably (`--strict --json`),
    with the exit-code contract unchanged. A count parsed out of prose would be
    fragile, and a count re-derived by the consumer would be a second definition of
    the unit.
  * `review_units.py` must RUN them, prefer what they report over what the record
    asserts, and refuse to verify a scope-declaring record that never ran them.

These tests use real subprocesses against the real scripts. The verdict-arithmetic
modules substitute a runner instead; this is the module that proves the path they
substitute actually exists.

Standard library only.
"""
from __future__ import annotations

import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load, fixture  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"

ru = load("skills/verify-review/scripts/review_units.py")

# check name -> (script, an argv that produces a CLEAN result)
CLEAN_RUNS = {
    "prisma_flow": ("skills/prisma-flow/scripts/prisma_flow.py",
                    [str(fixture("counts.valid.json"))]),
    "prisma_checklist": ("skills/prisma-flow/scripts/prisma_checklist.py",
                         [str(fixture("checklist.valid.json"))]),
    "grade_profile": ("skills/validate-evidence/scripts/grade_profile.py",
                      [str(fixture("grade-profile.valid.json")),
                       "--rob", str(fixture("risk-of-bias.contract-example.json"))]),
    "rob_appraisal": ("skills/appraise-risk-of-bias/scripts/rob_appraisal.py",
                      [str(fixture("risk-of-bias.contract-example.json"))]),
}


def run_script(rel: str, *args: str):
    """Run a check as a real subprocess and return (exit code, stdout, stderr)."""
    proc = subprocess.run([sys.executable, str(REPO / rel), *args],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout, proc.stderr


def clean_checks(**overrides) -> dict:
    """A `checks` block over the fixtures, every check reporting zero."""
    block = {
        "prisma_flow": {"record": "counts.valid.json"},
        "prisma_checklist": {"record": "checklist.valid.json"},
        "grade_profile": {"record": "grade-profile.valid.json",
                          "rob_record": "risk-of-bias.contract-example.json"},
        "rob_appraisal": {"record": "risk-of-bias.contract-example.json"},
    }
    block.update(overrides)
    return block


SCOPE = ["U_cite_external", "U_cite_internal", "U_consistency", "U_screen",
         "U_extract", "U_prisma", "U_grade", "U_rob_trace", "U_checklist"]


def record(units=None, gates=None, **extra) -> dict:
    """A fully-scoped systematic review whose derivable units come from checks."""
    u = {"U_cite_external": 0, "U_cite_internal": 0, "U_screen": 0, "U_extract": 0}
    if units:
        u.update(units)
    d = {"schema_version": ru.SCHEMA_VERSION, "review_type": "systematic",
         "units_in_scope": SCOPE, "units": u,
         "consistency": {"score": 90, "critical_breaks": 0},
         "gates": dict({"H_rob": 0, "H_screen_adj": 0, "H_cite_manual": 0,
                        "H_numeric": 0}, **(gates or {}))}
    d.update(extra)
    return d


def runner(records_root=FIXTURES, skills_root=REPO, **kw):
    return ru.CheckRunner(records_root=records_root, skills_root=skills_root, **kw)


def verdict(data, **kw):
    return ru.verdict(data, ru.DEFAULT_WEIGHTS, ru.CEILING, runner(**kw))


# ---------------------------------------------------------------------------
# Half one: the checks emit their counts
# ---------------------------------------------------------------------------

class TestEveryCheckSpeaksTheEnvelope(unittest.TestCase):
    """`--json` is binding on all four, like `--strict` before it."""

    def envelope(self, name):
        rel, args = CLEAN_RUNS[name]
        code, out, err = run_script(rel, *args, "--strict", "--json")
        self.assertIn(code, (0, 1), msg=err)
        return json.loads(out)

    def test_every_check_accepts_json_and_emits_the_envelope(self):
        for name in CLEAN_RUNS:
            with self.subTest(check=name):
                env = self.envelope(name)
                self.assertEqual(env["check"], name)
                self.assertEqual(env["schema_version"], ru.CHECKS_ENVELOPE_VERSION)
                for key in ("issues", "units", "gates", "unattributed"):
                    self.assertIn(key, env)

    def test_a_check_reports_only_the_units_the_table_assigns_it(self):
        """The consumer validates this too, from the other side.

        A check claiming a unit outside its remit would let one record's counts
        overwrite another's, and the table in `review_units.py` is the only place
        that mapping is written down.
        """
        for name in CLEAN_RUNS:
            with self.subTest(check=name):
                env = self.envelope(name)
                spec = ru.CHECK_TABLE[name]
                self.assertLessEqual(set(env["units"]), set(spec["units"]))
                self.assertLessEqual(set(env["gates"]), set(spec["gates"]))

    def test_json_replaces_the_artifact_rather_than_joining_it(self):
        """Stdout must be JSON and nothing else — a consumer parses the whole stream."""
        for name in CLEAN_RUNS:
            with self.subTest(check=name):
                rel, args = CLEAN_RUNS[name]
                _, out, _ = run_script(rel, *args, "--strict", "--json")
                self.assertNotIn("```mermaid", out)
                self.assertNotIn("| Item |", out)
                json.loads(out)          # the whole stream, not a prefix of it

    def test_json_does_not_change_the_exit_code(self):
        """The exit-code contract is `cli-contract.md`'s, and `--json` is an output
        format. A check that exited differently with it would make the flag change
        the verdict rather than the rendering."""
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
        """Exit 2 means the record was never evaluated. Printing an envelope of
        zeros there is the single worst thing this feature could do — it is the
        shape a consumer trusts, carrying counts nothing produced."""
        code, out, err = run_script("skills/prisma-flow/scripts/prisma_checklist.py",
                                    str(fixture("checklist.unknown-number.json")),
                                    "--strict", "--json")
        self.assertEqual(code, 2)
        self.assertEqual(out.strip(), "")
        self.assertTrue(err.strip())


class TestTheFlowCheckCountsWhatItCouldNotReach(unittest.TestCase):
    """`U_prisma` is failures PLUS unreached stages, and the second term is the
    whole point.

    Issue #9 stopped the artifact printing ✅ over a flow nothing had examined.
    A `U_prisma` counting only reconciliation failures would put that same
    fail-open straight back — this time in the number the loop reads, where no
    reader would ever see it.
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

    def test_and_that_record_cannot_verify_a_review(self):
        """End to end, which is the claim that matters."""
        d = record(checks=clean_checks(prisma_flow={"record": "counts.two-ends-only.json"}))
        r = verdict(d)
        self.assertEqual(r["units_evaluated"]["U_prisma"], 5)
        self.assertNotEqual(r["state"], "VERIFIED")


class TestTheCertaintyCheckCountsReferences(unittest.TestCase):
    """`U_rob_trace` counts unresolved REFERENCES, not diagnostics naming them.

    Three unresolved studies raise one message listing all three. Counting messages
    would book one unit of work for three broken references and understate the
    weighted total that routes the whole review — the same error `U_grade` was
    defined around when it moved from diagnostics to failing results.
    """

    def profile(self, **changes):
        rec = json.loads(fixture("grade-profile.valid.json").read_text(encoding="utf-8"))
        rec["results"][0].update(changes)
        return rec

    def envelope(self, rec, *args):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "rec.json"
            p.write_text(json.dumps(rec), encoding="utf-8")
            code, out, err = run_script(
                "skills/validate-evidence/scripts/grade_profile.py", str(p),
                "--rob", str(fixture("risk-of-bias.contract-example.json")),
                *args, "--strict", "--json")
        self.assertIn(code, (0, 1), msg=err)
        return json.loads(out)

    def test_a_resolving_record_reports_zero(self):
        self.assertEqual(self.envelope(self.profile())["units"]["U_rob_trace"], 0)

    def test_every_reference_counts_when_the_target_is_unknown(self):
        """A target that names nothing means NONE of the references resolve.

        Reporting 0 here would say the traceability was clean when in truth it
        could not be attempted — the difference between "checked and fine" and
        "never checked" that this whole loop turns on.
        """
        rec = self.profile(appraised_result="a result nobody appraised")
        env = self.envelope(rec)
        n_refs = len(rec["results"][0]["study_ids"])
        self.assertEqual(env["units"]["U_rob_trace"], n_refs)
        self.assertGreater(n_refs, 0)

    def test_an_unknown_study_reference_counts_once(self):
        """One reference REPLACED, not appended: adding one would also break
        design_mix, and a fixture with two defects cannot prove which one produced
        the count."""
        ids = list(self.profile()["results"][0]["study_ids"])
        env = self.envelope(self.profile(study_ids=[*ids[:-1], "S_not_in_the_appraisal"]))
        self.assertEqual(env["units"]["U_rob_trace"], 1)

    def test_the_unit_is_absent_without_an_appraisal_record(self):
        """No `--rob`, no traceability. Emitting 0 would claim every reference
        resolved, and the consumer must see the unit as UNDERIVED instead."""
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "rec.json"
            p.write_text(json.dumps(self.profile()), encoding="utf-8")
            _, out, _ = run_script("skills/validate-evidence/scripts/grade_profile.py",
                                   str(p), "--strict", "--json")
        env = json.loads(out)
        self.assertIn("U_grade", env["units"])
        self.assertNotIn("U_rob_trace", env["units"])


class TestTheAppraisalCheckDoesNotCountASignatureTwice(unittest.TestCase):
    def test_a_pending_confirmation_is_the_gate_and_nothing_else(self):
        """`H_rob` counts it, so `unattributed` must not.

        Counting it in both put every pending signature into a bucket a human
        cannot clear, so a record whose only fault was an unsigned appraisal could
        never reach the hand-off state that fault exists to produce.
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


# ---------------------------------------------------------------------------
# Half two: the loop runs them
# ---------------------------------------------------------------------------

class TestDerivedCountsOverrideReportedOnes(unittest.TestCase):
    def test_a_clean_run_verifies(self):
        self.assertEqual(verdict(record(checks=clean_checks()))["state"], "VERIFIED")

    def test_the_headline_case_a_handwritten_zero_no_longer_verifies(self):
        """Issue #4 in one test: every unit declared 0 by hand, against a record
        that does not reconcile."""
        d = record(units={"U_prisma": 0},
                   checks=clean_checks(prisma_flow={"record": "counts.two-ends-only.json"}))
        r = verdict(d)
        self.assertNotEqual(r["state"], "VERIFIED")
        self.assertEqual(r["units_evaluated"]["U_prisma"], 5)

    def test_a_disagreement_is_reported_not_silently_resolved(self):
        """The derived count wins — and the record said something else, which the
        caller is entitled to see. A contradiction the check resolves quietly is
        still a contradiction."""
        d = record(units={"U_checklist": 0},
                   checks=clean_checks(prisma_checklist={"record": "checklist.partial.json"}))
        r = verdict(d)
        self.assertTrue(any("U_checklist" in m for m in r["ignored_inputs"]), r["ignored_inputs"])
        self.assertGreater(r["units_evaluated"]["U_checklist"], 0)

    def test_an_agreeing_value_is_not_reported_as_ignored(self):
        """`ignored_inputs` names input that was DROPPED. A record carrying the same
        number the check found lost nothing, and flagging it would make the field
        noise in the ordinary case."""
        self.assertEqual(verdict(record(units={"U_prisma": 0},
                                        checks=clean_checks()))["ignored_inputs"], [])

    def test_a_derived_gate_overrides_a_reported_one(self):
        """The count a loop has the most incentive to understate."""
        d = record(gates={"H_rob": 0},
                   checks=clean_checks(rob_appraisal={"record": "risk-of-bias.unconfirmed.json"},
                                       grade_profile={"record": "grade-profile.valid.json",
                                                      "rob_record": "risk-of-bias.unconfirmed.json"}))
        r = verdict(d)
        self.assertEqual(r["gates_remaining"], 1)
        self.assertEqual(r["state"], "BLOCKED_ON_HUMAN")
        self.assertTrue(any("H_rob" in m for m in r["ignored_inputs"]), r["ignored_inputs"])

    def test_a_derived_unit_need_not_be_reported_at_all(self):
        """Declaring the check IS reporting the unit. Requiring the key as well
        would make the record restate what it just asked to have derived."""
        d = record(checks=clean_checks())
        self.assertNotIn("U_prisma", d["units"])
        r = verdict(d)
        self.assertEqual(r["missing_units"], [])
        self.assertEqual(r["state"], "VERIFIED")


class TestScopeDeclaredMeansChecksRequired(unittest.TestCase):
    def test_a_scoped_record_without_checks_cannot_verify(self):
        """Requirement 4. Without it the block is optional, and anyone wanting the
        old behaviour simply omits it."""
        d = record(units={"U_prisma": 0, "U_grade": 0, "U_rob_trace": 0,
                          "U_checklist": 0})
        r = verdict(d)
        self.assertEqual(r["state"], "CONTINUE")
        self.assertEqual(r["underived_units"],
                         ["U_checklist", "U_grade", "U_prisma", "U_rob_trace"])

    def test_a_partial_checks_block_names_exactly_what_is_left(self):
        d = record(units={"U_grade": 0, "U_rob_trace": 0, "U_checklist": 0},
                   checks={"prisma_flow": {"record": "counts.valid.json"}})
        self.assertEqual(verdict(d)["underived_units"],
                         ["U_checklist", "U_grade", "U_rob_trace"])

    def test_certainty_without_an_appraisal_record_leaves_the_trace_underived(self):
        """The conditional unit, end to end: `grade_profile` is declared, so
        `U_grade` is derived — but nothing traced anything, so `U_rob_trace` is
        not, and it must not read as a clean zero."""
        d = record(checks=clean_checks(
            grade_profile={"record": "grade-profile.valid.json"}))
        r = verdict(d)
        self.assertEqual(r["underived_units"], ["U_rob_trace"])
        self.assertNotEqual(r["state"], "VERIFIED")

    def test_the_human_gate_must_be_derived_too(self):
        """Gate 0 finding, and the worst one this change could have shipped.

        The requirement covered every unit and no gate. `H_rob` cannot appear in
        `units_in_scope` — that list is validated against the unit weights — so a
        record could declare systematic scope, omit the `rob_appraisal` entry, and
        reach VERIFIED with a signature still pending: issue #4's own failure mode
        surviving for the one count the constitution says a loop may never
        auto-zero.
        """
        d = record(gates={"H_rob": 0}, checks=clean_checks())
        del d["checks"]["rob_appraisal"]
        d["checks"]["grade_profile"]["rob_record"] = "risk-of-bias.unconfirmed.json"
        r = verdict(d)
        self.assertEqual(r["underived_gates"], ["H_rob"])
        self.assertNotEqual(r["state"], "VERIFIED")

    def test_and_declaring_it_surfaces_the_pending_signature(self):
        """The other half: with the entry, the gate the record understated is the
        one the verdict reports."""
        d = record(gates={"H_rob": 0}, checks=clean_checks(
            rob_appraisal={"record": "risk-of-bias.unconfirmed.json"},
            grade_profile={"record": "grade-profile.valid.json",
                           "rob_record": "risk-of-bias.unconfirmed.json"}))
        r = verdict(d)
        self.assertEqual(r["underived_gates"], [])
        self.assertEqual(r["gates_remaining"], 1)
        self.assertEqual(r["state"], "BLOCKED_ON_HUMAN")

    def test_a_gate_out_of_scope_is_not_required(self):
        """`H_rob` reads its scope from `U_rob_trace`, so dropping that unit from
        scope must drop the requirement with it.

        A rapid review is the real case: it permits the heuristic risk-of-bias
        basis, so both are out of scope, and a requirement that reached it anyway
        would demand an appraisal the review type says it need not have.
        """
        d = record(checks=clean_checks())
        del d["checks"]["rob_appraisal"]
        d["units_in_scope"] = [u for u in SCOPE if u != "U_rob_trace"]
        r = verdict(d)
        self.assertEqual(r["underived_gates"], [])
        self.assertEqual(r["state"], "VERIFIED")

    def test_the_gate_proxy_is_wired_to_a_real_unit_and_a_real_check(self):
        """The proxy is hand-written and could drift out of the property it needs:
        a gate whose proxy unit no check derives would silently never be required."""
        for gate, proxy in ru.GATE_SCOPE_PROXY.items():
            with self.subTest(gate=gate):
                self.assertIn(gate, ru.GATE_KEYS)
                self.assertIn(gate, ru.DERIVED_BY_GATE)
                self.assertIn(proxy, ru.DERIVED_BY)
        # Every gate any check produces needs a proxy, or it is unrequirable.
        self.assertEqual(set(ru.DERIVED_BY_GATE), set(ru.GATE_SCOPE_PROXY))

    def test_units_with_no_runnable_check_are_still_self_reported(self):
        """Stated rather than implied. Four units have no check in the table, so
        the requirement cannot reach them, and a reader must not infer from a
        clean verdict that every count was derived."""
        for unit in ("U_cite_external", "U_cite_internal", "U_screen", "U_extract"):
            with self.subTest(unit=unit):
                self.assertNotIn(unit, ru.DERIVED_BY)
        self.assertEqual(verdict(record(checks=clean_checks()))["state"], "VERIFIED")

    def test_an_undeclared_scope_stays_lenient(self):
        """No scope declared is the light path, and it keeps its existing default —
        the same choice `gates` already makes."""
        d = {"schema_version": ru.SCHEMA_VERSION,
             "units": {"U_cite_external": 0, "U_cite_internal": 0, "U_prisma": 0},
             "consistency": {"score": 90, "critical_breaks": 0}}
        r = verdict(d)
        self.assertEqual(r["underived_units"], [])
        self.assertEqual(r["state"], "VERIFIED")

    def test_no_routing_while_a_unit_is_underived(self):
        """Sending the agent to repair the dominant unit would be repairing a number
        nothing established."""
        d = record(units={"U_cite_external": 4, "U_prisma": 0, "U_grade": 0,
                          "U_rob_trace": 0, "U_checklist": 0})
        self.assertIsNone(verdict(d)["dominant_unit"])


class TestWorkNoUnitCounts(unittest.TestCase):
    def test_an_invalid_appraisal_record_holds_the_verdict(self):
        """`rob_appraisal` reports method violations that no unit and no gate
        counts. Ignoring them would let an appraisal record its own instrument
        rejects pass through as nothing outstanding."""
        d = record(checks=clean_checks(
            rob_appraisal={"record": "risk-of-bias.wrong-instrument.json"}))
        r = verdict(d)
        self.assertTrue(r["unattributed_issues"])
        self.assertNotEqual(r["state"], "VERIFIED")

    def test_it_is_not_parked_on_a_human(self):
        """BLOCKED_ON_HUMAN says a person must act. A record the appraisal check
        rejects is the agent's to fix, and mislabelling it would stall the loop
        waiting for a signature nobody was asked for."""
        d = record(gates={"H_rob": 0}, checks=clean_checks(
            rob_appraisal={"record": "risk-of-bias.wrong-instrument.json"}))
        self.assertEqual(verdict(d)["state"], "CONTINUE")


class TestAFailedCheckIsNeverZero(unittest.TestCase):
    """Step 3 of the issue: exit 2 must fail closed.

    This is the case where a fail-open costs the most. A malformed record is a
    record nothing evaluated, and booking it as zero outstanding work would make
    the most broken input in the system indistinguishable from the cleanest.
    """

    def test_exit_two_from_a_check_is_an_error(self):
        d = record(checks=clean_checks(
            prisma_checklist={"record": "checklist.unknown-number.json"}))
        with self.assertRaisesRegex(ru.InputError, "prisma_checklist"):
            verdict(d)

    def test_the_error_says_it_is_not_a_count_of_zero(self):
        d = record(checks=clean_checks(
            prisma_checklist={"record": "checklist.unknown-number.json"}))
        with self.assertRaisesRegex(ru.InputError, "not a count of zero"):
            verdict(d)

    def test_a_check_that_cannot_be_found_is_an_error(self):
        """A skill copied out on its own has no sibling skills. That is an
        unavailable check, not a clean one."""
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ru.InputError, "not available"):
                verdict(record(checks={"prisma_flow": {"record": "counts.valid.json"}}),
                        skills_root=pathlib.Path(d))

    def test_a_timeout_is_an_error(self):
        with self.assertRaisesRegex(ru.InputError, "unrun"):
            verdict(record(checks=clean_checks()), timeout=0.0001)

    def envelope_of(self, **over):
        """A COMPLETE envelope with one field changed.

        Same reasoning as tests/fixtures/README.md's one-defect-per-fixture rule:
        hand-writing a partial envelope per test made two of them fail for the
        missing `issues` field rather than for the thing they name, which a
        `assertRaises` alone could not have told apart.
        """
        env = {"check": "prisma_flow", "schema_version": ru.CHECKS_ENVELOPE_VERSION,
               "issues": 0, "units": {"U_prisma": 0}, "gates": {}, "unattributed": 0}
        env.update(over)
        return json.dumps(env)

    def test_unparseable_output_is_an_error(self):
        with self.assertRaisesRegex(ru.InputError, "not valid JSON"):
            ru._validated_envelope("prisma_flow", "not json at all", {"U_prisma"})

    def test_an_unknown_envelope_version_is_an_error(self):
        """A shape this module does not know is not read on the assumption it means
        what it used to."""
        with self.assertRaisesRegex(ru.InputError, "schema_version"):
            ru._validated_envelope("prisma_flow", self.envelope_of(schema_version="9.9"),
                                   {"U_prisma"})

    def test_a_script_identifying_as_another_check_is_an_error(self):
        with self.assertRaisesRegex(ru.InputError, "identifies itself"):
            ru._validated_envelope("prisma_flow", self.envelope_of(check="grade_profile"),
                                   {"U_prisma"})

    def test_a_check_reporting_fewer_units_than_planned_is_an_error(self):
        """The preview and the run agree because BOTH read `_would_derive`. A check
        quietly dropping a unit would break that agreement without either side
        noticing, so the mismatch is an error rather than a smaller result."""
        out = self.envelope_of(check="grade_profile", units={"U_grade": 0})
        with self.assertRaisesRegex(ru.InputError, "expected"):
            ru._validated_envelope("grade_profile", out, {"U_grade", "U_rob_trace"})

    def test_a_check_claiming_a_unit_outside_its_remit_is_an_error(self):
        out = self.envelope_of(units={"U_prisma": 0, "U_grade": 0})
        with self.assertRaisesRegex(ru.InputError, "expected"):
            ru._validated_envelope("prisma_flow", out, {"U_prisma"})

    def test_a_missing_gate_is_an_error_just_as_a_missing_unit_is(self):
        """Gates were checked in one direction only — extra rejected, absent
        accepted. An envelope omitting `gates` therefore left the record's own
        self-reported H_rob standing, which is the count that must never be taken
        on trust."""
        out = self.envelope_of(check="rob_appraisal", units={}, gates={})
        with self.assertRaisesRegex(ru.InputError, "expected"):
            ru._validated_envelope("rob_appraisal", out, set())

    def test_a_required_field_may_not_be_absent(self):
        """Absent is not zero. `unattributed` defaulting to 0 meant a check that
        never mentioned it read as one reporting none."""
        for field in ("issues", "units", "gates", "unattributed", "check",
                      "schema_version"):
            with self.subTest(missing=field):
                env = json.loads(self.envelope_of())
                del env[field]
                with self.assertRaises(ru.InputError):
                    ru._validated_envelope("prisma_flow", json.dumps(env), {"U_prisma"})

    def test_an_unknown_envelope_field_is_rejected(self):
        """The envelope is input like any other. Every other surface in the module
        rejects unknown keys; this one silently accepted them."""
        with self.assertRaisesRegex(ru.InputError, "bogus"):
            ru._validated_envelope("prisma_flow", self.envelope_of(bogus=1), {"U_prisma"})

    def test_a_malformed_record_is_rejected_before_anything_runs(self):
        """Validation ordering. Spawning four subprocesses and then rejecting the
        record for a misspelled unit key would do work on input already known to be
        malformed — the difference between validating a record and acting on it."""
        d = record(checks=clean_checks())
        d["units"]["U_vibes"] = 0
        with mock.patch.object(subprocess, "run",
                               side_effect=AssertionError("a check was executed")):
            with self.assertRaisesRegex(ru.InputError, "U_vibes"):
                verdict(d)

    def test_a_negative_derived_count_is_an_error(self):
        with self.assertRaises(ru.InputError):
            ru._validated_envelope("prisma_flow", self.envelope_of(units={"U_prisma": -1}),
                                   {"U_prisma"})


class TestTheBlockCannotChooseWhatRuns(unittest.TestCase):
    """The security boundary. `units.json` is untrusted input: anyone who can write
    it can point this module at a record, so nothing in it may reach the argv.
    """

    def test_the_argv_is_built_from_the_table_not_the_record(self):
        argv = runner().argv_for("grade_profile",
                                 {"record": "grade-profile.valid.json",
                                  "rob_record": "risk-of-bias.contract-example.json"})
        self.assertEqual(argv[0], sys.executable)
        self.assertTrue(argv[1].endswith("grade_profile.py"))
        self.assertIn("--strict", argv)
        self.assertIn("--json", argv)
        self.assertIn("--rob", argv)
        # Everything that is not a flag is a resolved path under the records root.
        for token in argv[2:]:
            if not token.startswith("--"):
                self.assertTrue(pathlib.Path(token).is_file(), token)

    def test_an_unknown_check_name_is_rejected(self):
        with self.assertRaisesRegex(ru.InputError, "unknown check"):
            verdict(record(checks={"rm": {"record": "counts.valid.json"}}))

    def test_a_check_name_is_not_a_path(self):
        """A name is a key into a fixed table. Accepting a path would be the
        code-execution surface this design exists to remove."""
        for name in ("../../evil.py", "skills/prisma-flow/scripts/prisma_flow.py",
                     "prisma_flow.py"):
            with self.subTest(name=name):
                with self.assertRaises(ru.InputError):
                    verdict(record(checks={name: {"record": "counts.valid.json"}}))

    def test_extra_entry_keys_are_rejected(self):
        """No `args`, no `flags`, no `python`. The rejected designs on issue #4 all
        reduce to letting the record add one of these."""
        for key in ("args", "flags", "script", "python", "env"):
            with self.subTest(key=key):
                with self.assertRaises(ru.InputError):
                    verdict(record(checks={"prisma_flow": {
                        "record": "counts.valid.json", key: ["--anything"]}}))

    def test_rob_record_is_rejected_where_it_does_not_belong(self):
        """`--rob` is the certainty check's flag. Accepting the key elsewhere would
        pass it to a script that does not take it."""
        with self.assertRaises(ru.InputError):
            verdict(record(checks={"prisma_flow": {
                "record": "counts.valid.json",
                "rob_record": "risk-of-bias.contract-example.json"}}))

    def test_a_missing_record_key_is_rejected(self):
        with self.assertRaisesRegex(ru.InputError, "record"):
            verdict(record(checks={"prisma_flow": {}}))

    def test_a_record_outside_the_root_is_rejected(self):
        with self.assertRaisesRegex(ru.InputError, "outside the records root"):
            verdict(record(checks={"prisma_flow": {"record": "../../README.md"}}))

    def test_an_absolute_path_outside_the_root_is_rejected(self):
        with self.assertRaisesRegex(ru.InputError, "outside the records root"):
            verdict(record(checks={"prisma_flow": {"record": str(REPO / "README.md")}}))

    def test_a_symlink_out_of_the_root_is_rejected(self):
        """Resolved BEFORE the containment test, or the test means nothing: a link
        inside the root pointing anywhere passes a purely textual check."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            try:
                (root / "escape.json").symlink_to(REPO / "README.md")
            except (OSError, NotImplementedError) as e:      # unprivileged Windows
                self.skipTest(f"symlinks unavailable: {e}")
            with self.assertRaisesRegex(ru.InputError, "outside the records root"):
                verdict(record(checks={"prisma_flow": {"record": "escape.json"}}),
                        records_root=root)

    def test_a_record_that_is_not_there_is_rejected(self):
        with self.assertRaisesRegex(ru.InputError, "no file at"):
            verdict(record(checks={"prisma_flow": {"record": "nowhere.json"}}))

    def test_a_non_string_record_is_rejected(self):
        for value in (3, None, ["counts.valid.json"], {"path": "counts.valid.json"}):
            with self.subTest(value=value):
                with self.assertRaises(ru.InputError):
                    verdict(record(checks={"prisma_flow": {"record": value}}))

    def test_the_block_itself_must_be_an_object(self):
        for value in ([{"prisma_flow": {}}], "prisma_flow", 3):
            with self.subTest(value=value):
                with self.assertRaises(ru.InputError):
                    verdict(record(checks=value))

    def test_an_entry_must_be_an_object(self):
        with self.assertRaises(ru.InputError):
            verdict(record(checks={"prisma_flow": "counts.valid.json"}))


class TestThePreviewDescribesTheRunItPreviews(unittest.TestCase):
    """`--dry-run` promises to run no checks. It must still validate the block, or
    it reports a plan that the run will reject — which is how `units_in_scope` and
    its preview drifted apart once already (`_validated_scope`).
    """

    def preview(self, data, **kw):
        return ru.dry_run_preview(data, ru.CEILING, runner(**kw))

    def test_the_preview_names_the_checks_and_the_units_they_will_derive(self):
        p = self.preview(record(checks=clean_checks()))
        self.assertEqual(p["checks_declared"], sorted(ru.CHECK_TABLE))
        self.assertEqual(p["units_that_will_be_derived"],
                         ["U_checklist", "U_grade", "U_prisma", "U_rob_trace"])
        self.assertEqual(p["underived_units"], [])

    def test_the_preview_names_what_will_be_underived(self):
        p = self.preview(record(checks={"prisma_flow": {"record": "counts.valid.json"}}))
        self.assertEqual(p["underived_units"],
                         ["U_checklist", "U_grade", "U_rob_trace"])

    def test_the_preview_agrees_with_the_run_on_the_conditional_unit(self):
        entry = {"grade_profile": {"record": "grade-profile.valid.json"}}
        p = self.preview(record(checks=entry))
        self.assertEqual(p["units_that_will_be_derived"], ["U_grade"])
        r = verdict(record(checks=entry))
        self.assertIn("U_grade", r["units_evaluated"])
        self.assertIn("U_rob_trace", r["underived_units"])

    def test_the_preview_rejects_what_the_run_would_reject(self):
        for block in ({"nope": {"record": "counts.valid.json"}},
                      {"prisma_flow": {"record": "../../README.md"}},
                      {"prisma_flow": {"record": "counts.valid.json", "args": []}}):
            with self.subTest(block=block):
                with self.assertRaises(ru.InputError):
                    self.preview(record(checks=block))

    def test_the_preview_still_runs_nothing(self):
        with mock.patch.object(subprocess, "run",
                               side_effect=AssertionError("a check was executed")):
            self.preview(record(checks=clean_checks()))


class TestTheCommandLine(unittest.TestCase):
    """`--records-root` and `--skills-root` come from the ARGV, which is the
    operator's, not from the record, which is not. Someone who can pass flags to
    this script can already run anything on the machine."""

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["review_units.py", *argv]), \
                redirect_stdout(out), redirect_stderr(err):
            code = ru.main()
        return code, out.getvalue(), err.getvalue()

    def test_records_resolve_beside_the_input_by_default(self):
        """A review's artifacts sit next to its units.json, so that is the default
        root and no flag is needed for the ordinary case."""
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "units.json"
            p.write_text(json.dumps(record(checks={
                "prisma_flow": {"record": "counts.valid.json"}})), encoding="utf-8")
            (pathlib.Path(d) / "counts.valid.json").write_text(
                fixture("counts.valid.json").read_text(encoding="utf-8"), encoding="utf-8")
            code, out, err = self.run_main(str(p))
        self.assertEqual(code, 1, msg=err)               # units still outstanding
        self.assertEqual(json.loads(out)["units_evaluated"]["U_prisma"], 0)

    def test_records_root_overrides_it(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "units.json"
            p.write_text(json.dumps(record(checks=clean_checks())), encoding="utf-8")
            code, out, err = self.run_main(str(p), "--records-root", str(FIXTURES))
        self.assertEqual(code, 0, msg=err)
        self.assertEqual(json.loads(out)["state"], "VERIFIED")

    def test_a_failed_check_exits_two_with_a_message_not_a_traceback(self):
        """The gate fails closed the same way every other malformed input does."""
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "units.json"
            p.write_text(json.dumps(record(checks={"prisma_flow": {
                "record": "nowhere.json"}})), encoding="utf-8")
            code, out, err = self.run_main(str(p))
        self.assertEqual(code, 2)
        self.assertEqual(out.strip(), "")
        self.assertIn("prisma_flow", json.loads(err)["error"])


class TestTheTableIsConsistent(unittest.TestCase):
    """Invariants over CHECK_TABLE, so a fifth check cannot be added half-wired.

    The last review round on this repository closed a class of bug by proving a
    property of two hand-written key tuples rather than by fixing one more
    instance. Same reasoning here: these tables are hand-written and can drift out
    of the property they are supposed to have without any test failing.
    """

    def test_every_unit_in_the_table_has_a_weight(self):
        for name, spec in ru.CHECK_TABLE.items():
            for unit in spec["units"]:
                with self.subTest(check=name, unit=unit):
                    self.assertIn(unit, ru.DEFAULT_WEIGHTS)

    def test_every_gate_in_the_table_is_a_gate_key(self):
        for name, spec in ru.CHECK_TABLE.items():
            for gate in spec["gates"]:
                with self.subTest(check=name, gate=gate):
                    self.assertIn(gate, ru.GATE_KEYS)

    def test_no_unit_is_produced_by_two_checks(self):
        """`DERIVED_BY` is a dict, so a duplicate would silently keep the last
        entry and the loop would run the wrong check for that unit."""
        produced = [u for spec in ru.CHECK_TABLE.values() for u in spec["units"]]
        self.assertEqual(len(produced), len(set(produced)))
        self.assertEqual(len(produced), len(ru.DERIVED_BY))

    def test_a_conditional_unit_belongs_to_its_own_check(self):
        for name, spec in ru.CHECK_TABLE.items():
            optional = {k for k, _ in spec["optional_records"]}
            for unit, key in spec["conditional_units"].items():
                with self.subTest(check=name, unit=unit):
                    self.assertIn(unit, spec["units"])
                    self.assertIn(key, optional)

    def test_no_universal_floor_unit_is_derivable(self):
        """The floor is what every review type must satisfy however light, and
        three of its members have no check at all. A floor unit that became
        derivable would make the requirement unmeetable for a narrative review."""
        self.assertEqual(set(ru.UNIVERSAL_FLOOR) & set(ru.DERIVED_BY), set())

    def test_every_script_in_the_table_exists_and_takes_the_flags(self):
        for name, spec in ru.CHECK_TABLE.items():
            with self.subTest(check=name):
                script = REPO.joinpath(*spec["script"])
                self.assertTrue(script.is_file(), script)
                code, out, _ = run_script("/".join(spec["script"]), "--help")
                self.assertEqual(code, 0)
                self.assertIn("--json", out)
                self.assertIn("--strict", out)


if __name__ == "__main__":
    unittest.main()
