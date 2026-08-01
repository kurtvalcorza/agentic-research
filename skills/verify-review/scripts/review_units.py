#!/usr/bin/env python3
"""
review_units.py — compute the weighted "units remaining" scalar and the loop
verdict for the verify-review skill.

Stdlib only. Mirrors the convention of the other runnable backends in this
suite (screen-literature/kappa.py, prisma-flow/prisma_flow.py).

INPUT (a JSON file, or stdin):
{
  "schema_version": "1.0",             # required; rejects pre-redefinition records
  "review_type": "systematic",          # systematic|scoping|rapid|umbrella|narrative
  "cycle": 3,                            # current cycle number (0 = baseline)
  "units": {                             # auto-reducible unit COUNTS (in-scope only)
    "U_cite_external": 2,
    "U_cite_internal": 0,
    "U_screen": 1,
    "U_extract": 0,
    "U_prisma": 0,
    "U_grade": 0
  },
  "units_in_scope": ["U_screen", "U_prisma"],  # optional: the frozen in-scope set
                                         #   (spec §3.3). Every listed unit must be
                                         #   present+0 before VERIFIED; default is
                                         #   the universal floor alone.
  "consistency": {"score": 71, "critical_breaks": 0},   # optional -> derives U_consistency
  "gates": {"H_rob": 4, "H_screen_adj": 0, "H_cite_manual": 1, "H_numeric": 0},  # human-gate counts
  "history": [14, 11, 9],                # prior WEIGHTED totals, oldest first (optional)
  "denominators": {"citations": 40, "studies": 22, "themes": 8},  # optional, floor-guard
  "exclusions_logged": false,            # optional: a denominator drop is backed by a
                                         #   logged eligibility/exclusion reason (§5)
  "checks": {                            # optional: DERIVE counts by running a check
    "prisma_flow":      {"record": "flow.json"},
    "prisma_checklist": {"record": "checklist.json"},
    "rob_appraisal":    {"record": "appraisal.json"},
    "grade_profile":    {"record": "certainty.json", "rob_record": "appraisal.json"}
  }
}

DERIVED VS REPORTED COUNTS
  Without `checks`, every number above is asserted by whoever wrote this file. With
  it, the named checks are RUN and what they report overrides what the record says
  — `U_prisma`, `U_checklist`, `U_grade`, `U_rob_trace` and the `H_rob` gate. When
  `units_in_scope` is declared, a unit a check could have derived may not be
  self-reported: it is listed under `underived_units` and the verdict is held.

  The check name is a key into a fixed table, never a path, and the command line is
  built here — `--strict --json`, plus `--rob` for the certainty check. Nothing in
  this file reaches the argv, because anyone who can write it would otherwise
  control what runs. Record paths must resolve inside --records-root.

  This makes the counts DERIVED rather than asserted. It does not make them
  unforgeable: a caller can still point `record` at a doctored file. What the loop
  verifies is that the checks were run and what they reported — not that the
  underlying review is true.

Only pass the units that are IN SCOPE for the review type (see SKILL.md §
"Units in scope"). Omitted units are treated as absent, not as zero-to-achieve.
Citation integrity + consistency are the UNIVERSAL FLOOR: a VERIFIED verdict
requires them to be present and zero for *every* review type — an empty or
citation-less units map can never be VERIFIED (the gate fails closed). Declare
`units_in_scope` to also require the review-type-specific units (screening,
PRISMA, extraction, GRADE) be present+0, so an input that silently omits an
in-scope check cannot reach VERIFIED; declaring scope also requires the `gates`
key to be present (even `{}`), so an omitted gates object cannot silently assert
all human gates confirmed.

Fail-closed details:
  - `U_consistency` is derived ONLY from the `consistency` object (needs a numeric
    score); a value placed directly in `units` is ignored.
  - Counts must be finite non-negative numbers; gate/cycle/denominator counts must
    be whole numbers; booleans/NaN/negatives/wrong field types → error verdict,
    non-zero exit (never a traceback or a spurious VERIFIED).
  - With `--manifest`, an UNLOGGED denominator drop (content removed without
    `exclusions_logged`) HOLDS a would-be VERIFIED as BLOCKED_ON_HUMAN for
    adjudication (anti-gaming, §5).
  - A declared check that cannot produce a verdict — exit 2, a crash, a timeout, an
    output this module cannot validate — is an error, never a count of zero. An
    unreadable record is exactly the case where booking zero outstanding work would
    be worst.
  - Each manifest record carries the `schema_version` its counts were computed
    under; records written before that field existed are stamped `"unversioned"`
    rather than assumed current, so a history spanning a unit redefinition cannot
    be read as one continuous series.

OUTPUT: a JSON verdict on stdout. Exit code 0 only when VERIFIED; non-zero
otherwise (so it can gate a pipeline like `prisma_flow.py --strict`).
"""

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

# --- configuration (single source of truth for weights / thresholds) --------
SCHEMA_VERSION = "1.0"
# Stamped on manifest records written before this field existed. It says the
# definitions those counts were computed under are UNKNOWN — which is the whole
# point; adopting them into SCHEMA_VERSION would assert something unverifiable.
LEGACY_SCHEMA = "unversioned"

# Q1: fabricated/unverifiable citations dominate routing and the climb gradient.
DEFAULT_WEIGHTS = {
    "U_cite_external": 3,
    "U_cite_internal": 1,
    "U_screen": 1,
    "U_extract": 1,
    "U_prisma": 1,
    # U_grade: results failing grade_profile.py --strict. Previously this had no
    # operational definition ("themes not yet graded"), so it could not fail for
    # the right reason; it is now DEFINED AS the count that check reports.
    "U_grade": 1,
    # U_rob_trace: studies cited by the certainty record as confirmed-appraisal
    # backing that do not resolve at the named (study, result) target. A matching
    # but unconfirmed appraisal is excluded here and belongs only to H_rob.
    "U_rob_trace": 1,
    # U_checklist: PRISMA rows neither located nor justified (prisma_checklist.py).
    "U_checklist": 1,
    "U_consistency": 1,
}
CONSISTENCY_GATE = 75      # validate-consistency pass threshold
PLATEAU_K = 3              # consecutive flat-or-worse cycles -> PLATEAU
SOFT_ADVISORY_CYCLE = 10   # advisory only; does NOT stop the loop
CEILING = 25               # hard backstop

# H_rob is DEFINED AS the count rob_appraisal.py reports: APPRAISALS lacking
# confirmed_by/confirmed_at, not studies. Identity is (study, result), so one study
# appraised for two results and confirmed for neither contributes 2 — a human signs
# off on a judgment about one result, not on a study wholesale, and the gate counts
# the sign-offs still owed. Describing it as studies would invite an assembler to
# deduplicate the producer's count and understate the human workload.
#
# NOTE what this module cannot do. It now RUNS the four checks named in a `checks`
# block and takes their counts over the record's own, so a hand-written units.json
# of all zeros no longer reaches VERIFIED on the scope-declaring path — that was
# issue #4. Two limits survive the fix and are not shrinking:
#
#   * A caller can still point `record` at a doctored file. Running the check
#     proves what the check said about the record it was given, not that the record
#     describes the review that happened.
#   * Four units have no runnable check here at all — U_cite_external,
#     U_cite_internal, U_screen, U_extract — and stay self-reported. `U_consistency`
#     is derived, but from an object in this same file rather than from a run.
#
# Human gates are never auto-zeroed by any number of cycles.
GATE_KEYS = ("H_rob", "H_screen_adj", "H_cite_manual", "H_numeric")

# Citation integrity + consistency are universal for EVERY review type (spec
# §3.3): the floor the loop guarantees for any review. A VERIFIED verdict must
# have these present and zero, so an empty/partial units map fails closed.
UNIVERSAL_FLOOR = ("U_cite_external", "U_cite_internal", "U_consistency")
RECORD_KEYS = {
    "schema_version", "review_type", "cycle", "units", "units_in_scope",
    "consistency", "gates", "history", "denominators", "exclusions_logged",
    "outcome", "checks",
}
CONSISTENCY_KEYS = {"score", "critical_breaks"}

# --- derived counts ---------------------------------------------------------
#
# The four checks this module may RUN, so a count can be derived from a check
# rather than asserted by whoever wrote units.json. Everything above computes a
# verdict from numbers it is given; this table is what lets some of those numbers
# come from somewhere.
#
# THE TABLE IS THE SECURITY BOUNDARY. `units.json` is untrusted — anyone able to
# write it can point this module at a record — so nothing in it reaches the
# command line. A `checks` entry names WHICH check (a key here, never a path, never
# a basename to be matched) and WHAT RECORD to read. The argv is built here:
# `--strict --json` are fixed, and the only caller-supplied values are record
# paths, which the check opens for reading and never executes. Two more expressive
# designs — a per-script flag allowlist, and free-form args behind a basename
# allowlist — were considered and rejected on issue #4, because both hand argv
# control back to whoever writes the record.
#
# The OPERATOR's argv is a different matter and is trusted: --skills-root and
# --records-root exist for that reason. Someone who can pass flags to this script
# can already run anything on the machine, so constraining them would buy nothing.
#
# `conditional_units` names a unit the check derives only when the entry supplies
# a particular record: without `--rob` the certainty check traces nothing, and a
# reported 0 would claim every reference resolved.
CHECK_TABLE = {
    "prisma_flow": {
        "script": ("skills", "prisma-flow", "scripts", "prisma_flow.py"),
        "units": ("U_prisma",),
        "gates": (),
        "optional_records": (),
        "conditional_units": {},
    },
    "prisma_checklist": {
        "script": ("skills", "prisma-flow", "scripts", "prisma_checklist.py"),
        "units": ("U_checklist",),
        "gates": (),
        "optional_records": (),
        "conditional_units": {},
    },
    "grade_profile": {
        "script": ("skills", "validate-evidence", "scripts", "grade_profile.py"),
        "units": ("U_grade", "U_rob_trace"),
        "gates": (),
        "optional_records": (("rob_record", "--rob"),),
        "conditional_units": {"U_rob_trace": "rob_record"},
    },
    "rob_appraisal": {
        "script": ("skills", "appraise-risk-of-bias", "scripts", "rob_appraisal.py"),
        "units": (),
        # A human gate, never an auto-reducible unit: no number of cycles clears it.
        "gates": ("H_rob",),
        "optional_records": (),
        "conditional_units": {},
    },
}

# unit -> the check that produces it. A unit in scope with no entry for its check
# is UNDERIVED: present in the record, but self-reported, which is the gap this
# whole block exists to close.
DERIVED_BY = {u: name for name, spec in CHECK_TABLE.items() for u in spec["units"]}

# gate -> the in-scope UNIT it moves with. A gate cannot appear in
# `units_in_scope` (that list is validated against DEFAULT_WEIGHTS), so there is
# nothing to read a gate's scope off directly — and without this the requirement
# below covered every unit and no gate at all. A record could declare systematic
# scope, omit the `rob_appraisal` entry, and reach VERIFIED with a signature still
# pending: issue #4's own failure mode surviving for the one count the
# constitution says a loop may never auto-zero, and the count a loop has the most
# incentive to understate.
#
# `H_rob` pairs with `U_rob_trace` because they are in scope for exactly the same
# review types in every row of the contract's table — both come from the appraisal
# record, and a review that must trace appraisals must also have them signed.
GATE_SCOPE_PROXY = {"H_rob": "U_rob_trace"}

# gate -> the check that produces it, the DERIVED_BY of the gate side.
DERIVED_BY_GATE = {g: name for name, spec in CHECK_TABLE.items() for g in spec["gates"]}

# Version of the checks' --json ENVELOPE, not of any record. Validated before a
# single count is read, so a script whose output shape changes is rejected rather
# than mis-read as the shape expected here.
CHECKS_ENVELOPE_VERSION = "1.0"

# The envelope's closed schema. `detail` is the only optional field — it is
# advisory and nothing here reads it. Everything else must be PRESENT: absent is
# not zero, and a check that did not say is not a check that reported none.
ENVELOPE_KEYS = {"check", "schema_version", "issues", "units", "gates",
                 "unattributed", "detail"}
ENVELOPE_REQUIRED = ENVELOPE_KEYS - {"detail"}

# A check reads one JSON record and prints counts; anything approaching this is
# hung, not slow. A hang would otherwise stall the loop indefinitely with no
# verdict at all.
CHECK_TIMEOUT = 120.0


class InputError(ValueError):
    """Malformed units.json — the gate fails closed (error verdict, non-zero exit)."""


def _as_count(x, ctx):
    """Coerce a JSON value to a numeric count, or fail closed.

    Rejects booleans (JSON true/false would otherwise silently coerce to 1.0/0.0
    via float() and a `false` could satisfy the all-zero predicate), null, and
    non-numeric values. A malformed count raises InputError, which main() reports
    as an error verdict with a non-zero exit — rather than crashing with a
    traceback or letting a bad value slip through the gate.
    """
    # bool is an int subclass, so it must be rejected explicitly. Numeric strings
    # ("0") are also rejected: the contract requires JSON numbers, so a wrong type
    # fails closed rather than being silently coerced.
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise InputError(f"{ctx}: expected a JSON number ({x!r})")
    v = float(x)
    if not math.isfinite(v):   # reject NaN / Infinity (would blind plateau + emit invalid JSON)
        raise InputError(f"{ctx}: not a finite number ({x!r})")
    return v


def _as_nonneg_count(x, ctx):
    """Coerce to a non-negative count; a negative count is malformed input."""
    v = _as_count(x, ctx)
    if v < 0:
        raise InputError(f"{ctx}: negative count ({x!r})")
    return v


def _as_int_count(x, ctx):
    """Coerce to a non-negative INTEGER count (gates, cycle).

    Rejects negatives (which could cancel a positive gate to a false zero) and
    fractional values (which int() would truncate — 0.9 → 0 silently drops a
    pending human gate). Counts are whole numbers, so anything else is malformed.
    """
    v = _as_nonneg_count(x, ctx)
    if v != int(v):
        raise InputError(f"{ctx}: expected a whole number ({x!r})")
    return int(v)


def derive_consistency_unit(consistency):
    """Q2: graded gradient = critical_breaks + max(0, 75 - score).

    Returns None (unit absent) when there is no numeric score — a consistency
    object without a real score means the check was not measured, so the floor
    unit must stay absent (fail closed) rather than fabricate a present-and-zero
    U_consistency that could satisfy the gate without a genuine >=75 result.
    critical_breaks and score are validated non-negative/finite so a negative
    break count cannot cancel the sub-gate gap to a spurious 0.
    """
    if consistency is None:
        return None
    if not isinstance(consistency, dict):
        raise InputError("consistency: expected an object")
    _reject_unknown_keys(consistency, CONSISTENCY_KEYS, "consistency")
    score = consistency.get("score")
    if score is None:
        return None       # measured requires a score; absent → fails closed
    breaks = _as_nonneg_count(consistency.get("critical_breaks", 0), "consistency.critical_breaks")
    return breaks + max(0, CONSISTENCY_GATE - _as_nonneg_count(score, "consistency.score"))


def _as_object(x, ctx):
    """Absent/null → {}; any other non-object (incl. empty [] / '') is malformed."""
    if x is None:
        return {}
    if not isinstance(x, dict):
        raise InputError(f"{ctx}: expected an object")
    return x


def _validate_schema_version(data):
    """Reject legacy records before interpreting redefined unit semantics."""
    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise InputError(
            f"schema_version: expected {SCHEMA_VERSION!r}, got {version!r}; "
            "unversioned or older records predate the current U_grade/U_rob_trace definitions")


def _reject_unknown_keys(value, allowed, ctx):
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise InputError(
            f"{ctx}: unknown field(s) {', '.join(repr(k) for k in unknown)}; "
            f"expected only {sorted(allowed)}")


def _validated_scope(data):
    """Return (declared, declared_present) with every entry checked.

    Shared by compute() and dry_run_preview() because they MUST agree. They did
    not: this validation lived inside compute(), and --dry-run reached the scope
    set through its own `isinstance(declared, list) else []` coercion, which
    validated nothing. Five shapes diverged — `[{}]` and `["U_bogus", 1]` raised
    an uncaught TypeError (traceback, exit 1) while `[1]`, `["U_bogus"]` and a
    bare string all exited 0, the last of them silently DISCARDING the declared
    scope and previewing an empty one. A preview that reports a different scope
    from the run it previews is worse than no preview, and a silent drop is the
    exact overclaim this whole check exists to refuse.

    Callers that only need the names can ignore the second element.
    """
    raw_scope = data.get("units_in_scope")
    if raw_scope is None:
        return [], False
    if not isinstance(raw_scope, list):
        raise InputError("units_in_scope: expected an array of unit names")
    for u in raw_scope:
        # isinstance before membership: an unhashable entry (a dict, a list)
        # raises TypeError on `in` and on set(), which would surface as a
        # traceback and exit 1 instead of the documented exit 2.
        if not isinstance(u, str):
            raise InputError(f"units_in_scope: entries must be unit-name strings (got {u!r})")
        if u not in DEFAULT_WEIGHTS:
            raise InputError(f"units_in_scope: unknown unit {u!r}; expected one of {sorted(DEFAULT_WEIGHTS)}")
    return raw_scope, True


def _would_derive(name, entry):
    """The units this entry will cause its check to report.

    Computed from the entry alone, before anything runs, so `--dry-run` can name
    them without executing a check. The same function then validates what the check
    actually returned, which is what stops the preview and the run from drifting
    apart: a check reporting fewer units than predicted is an error, not a quietly
    smaller result. `_validated_scope` above exists because that exact drift
    happened once already.
    """
    spec = CHECK_TABLE[name]
    conditional = spec["conditional_units"]
    derived = {u for u in spec["units"] if u not in conditional}
    derived |= {u for u, key in conditional.items() if key in entry}
    return derived


class CheckRunner:
    """Runs the four checks and reports what they SAID, not what units.json claims.

    Built by main() from the argv. Its two roots are the trust boundary:

      records_root  where a `record` path may point. Resolved with realpath, so a
                    symlink or `..` cannot walk out of it. Defaults to the
                    directory holding units.json — a review's artifacts sit beside
                    it — and the record is opened for READING by the check.
      skills_root   where the check scripts are found. Never influenced by
                    units.json; the path within it comes from CHECK_TABLE.

    A skill directory copied out on its own (constitution Principle III) has no
    sibling skills, so a check will simply not be there. That is reported as an
    unavailable check, not treated as a clean one.
    """

    def __init__(self, records_root, skills_root, timeout=CHECK_TIMEOUT):
        self.records_root = Path(records_root)
        self.skills_root = Path(skills_root)
        self.timeout = timeout

    def _contained_record(self, value, ctx):
        if not isinstance(value, str) or not value.strip():
            raise InputError(f"{ctx}: expected a non-empty path string")
        root = Path(os.path.realpath(self.records_root))
        resolved = Path(os.path.realpath(root / value))
        try:
            # realpath first, relative_to second: resolving the symlinks BEFORE the
            # containment test is what makes the test mean anything. A link inside
            # the root pointing anywhere on the filesystem passes a purely textual
            # check. On Windows a path on another drive raises here too, which is
            # the same rejection for the same reason.
            resolved.relative_to(root)
        except ValueError:
            raise InputError(
                f"{ctx}: {value!r} resolves to {str(resolved)!r}, outside the records "
                f"root {str(root)!r}. Records are caller-supplied paths in an "
                f"untrusted file, so they may not reach outside it; pass "
                f"--records-root if the review's artifacts live elsewhere") from None
        if not resolved.is_file():
            raise InputError(f"{ctx}: no file at {value!r} (resolved to {str(resolved)!r})")
        return str(resolved)

    def argv_for(self, name, entry):
        """Build the full command line. Nothing here comes from `entry` but paths."""
        spec = CHECK_TABLE[name]
        script = self.skills_root.joinpath(*spec["script"])
        if not script.is_file():
            raise InputError(
                f"checks.{name}: the check is not available — no script at "
                f"{str(script)!r}. A skill directory copied out on its own has no "
                f"sibling skills; pass --skills-root pointing at the PARENT of a "
                f"'skills' directory. Dropping the entry does not help while "
                f"units_in_scope is declared — the unit then lands in "
                f"underived_units and the verdict is held, so a standalone copy "
                f"needs either the sibling skills or an undeclared scope")
        argv = [sys.executable, str(script),
                self._contained_record(entry["record"], f"checks.{name}.record"),
                "--strict", "--json"]
        for key, flag in spec["optional_records"]:
            if key in entry:
                argv += [flag, self._contained_record(entry[key], f"checks.{name}.{key}")]
        return argv

    def run(self, name, argv, expected_units):
        """Execute one check and return (units, gates, unattributed count)."""
        try:
            proc = subprocess.run(argv, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace",
                                  timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise InputError(
                f"checks.{name}: no result after {self.timeout:g}s — the check is "
                f"treated as unrun, not as zero outstanding") from None
        except OSError as e:
            raise InputError(f"checks.{name}: cannot run the check ({e})") from None

        # 0 and 1 are the check's two REVIEW outcomes: clean, and violations under
        # --strict. Everything else means the check did not evaluate the record —
        # exit 2 is malformed input, and anything higher is a crash. Both must fail
        # closed here, because the alternative is booking an unreadable record as
        # zero outstanding work, which is the whole failure mode being closed.
        if proc.returncode not in (0, 1):
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            raise InputError(
                f"checks.{name}: exited {proc.returncode} without a verdict"
                f"{' — ' + detail[0] if detail else ''}. Exit 2 is an unreadable "
                f"record and needs a human; it is not a count of zero")
        return _validated_envelope(name, proc.stdout, expected_units)


def _validated_envelope(name, stdout, expected_units):
    """Parse and check one check's --json output before any count is believed."""
    spec = CHECK_TABLE[name]
    try:
        env = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise InputError(f"checks.{name}: output is not valid JSON ({e})") from None
    if not isinstance(env, dict):
        raise InputError(f"checks.{name}: output is not a JSON object")
    if env.get("check") != name:
        raise InputError(
            f"checks.{name}: the script identifies itself as {env.get('check')!r}")
    if env.get("schema_version") != CHECKS_ENVELOPE_VERSION:
        raise InputError(
            f"checks.{name}: envelope schema_version {env.get('schema_version')!r}, "
            f"expected {CHECKS_ENVELOPE_VERSION!r} — an output shape this module does "
            f"not know is not read on the assumption it means what it used to")

    # The envelope is input like any other, so it gets the closed-schema treatment
    # every other input surface in this module gets. It did not: an unknown field
    # sailed through while a misspelled one in units.json is rejected outright.
    _reject_unknown_keys(env, ENVELOPE_KEYS, f"checks.{name}")
    for key in ENVELOPE_REQUIRED:
        if key not in env:
            raise InputError(
                f"checks.{name}: envelope is missing {key!r}. Absent is not zero — "
                f"a check that did not say is not a check that reported none")

    units = _as_object(env.get("units"), f"checks.{name}.units")
    gates = _as_object(env.get("gates"), f"checks.{name}.gates")
    # BOTH directions, for units and gates alike. An EXTRA entry means the script is
    # claiming a count outside its remit; a MISSING one means it reported less than
    # this entry asked for, and accepting that silently would let a check quietly
    # stop deriving a count while the loop went on treating it as derived. That
    # applied to gates too, and checking them one way round was how an envelope
    # omitting `gates` entirely left a self-reported H_rob standing.
    if set(units) != set(expected_units):
        raise InputError(
            f"checks.{name}: reported units {sorted(units)}, expected "
            f"{sorted(expected_units)}")
    if set(gates) != set(spec["gates"]):
        raise InputError(
            f"checks.{name}: reported gates {sorted(gates)}, expected "
            f"{sorted(spec['gates'])}")

    return ({u: _as_int_count(v, f"checks.{name}.units.{u}") for u, v in units.items()},
            {g: _as_int_count(v, f"checks.{name}.gates.{g}") for g, v in gates.items()},
            _as_int_count(env["unattributed"], f"checks.{name}.unattributed"))


def _validated_checks(data, runner):
    """Return {check name: (argv, units it will derive)}, fully validated.

    Shared by compute() and dry_run_preview() for the reason `_validated_scope`
    is: a preview that validates the block differently from the run it previews is
    worse than no preview. Nothing is executed here, so --dry-run can call it and
    keep its promise to run no checks.
    """
    raw = data.get("checks")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise InputError("checks: expected an object mapping a check name to "
                         "{\"record\": path}")
    if runner is None:
        raise InputError(
            "checks: a `checks` block was supplied but no runner is configured — "
            "the counts would be read from the record instead of derived, which is "
            "the opposite of what the block asks for")
    out = {}
    for name in sorted(raw):
        if name not in CHECK_TABLE:
            raise InputError(
                f"checks: unknown check {name!r}; expected one of {sorted(CHECK_TABLE)}. "
                f"The name is a key into a fixed table, not a path")
        entry = raw[name]
        if not isinstance(entry, dict):
            raise InputError(f"checks.{name}: expected an object")
        spec = CHECK_TABLE[name]
        _reject_unknown_keys(entry, {"record"} | {k for k, _ in spec["optional_records"]},
                             f"checks.{name}")
        if "record" not in entry:
            raise InputError(
                f"checks.{name}: 'record' is required — it names the record the check "
                f"runs against")
        out[name] = (runner.argv_for(name, entry), _would_derive(name, entry))
    return out


def _validate_record_schema(data):
    """Apply the closed input schema before interpreting any optional defaults."""
    if not isinstance(data, dict):
        raise InputError("record: expected an object")
    _reject_unknown_keys(data, RECORD_KEYS, "record")
    _validate_schema_version(data)
    consistency = data.get("consistency")
    if consistency is not None:
        if not isinstance(consistency, dict):
            raise InputError("consistency: expected an object")
        _reject_unknown_keys(consistency, CONSISTENCY_KEYS, "consistency")


def compute(data, weights, runner=None):
    _validate_record_schema(data)
    ignored_inputs: list[str] = []

    # Validate the `checks` block before anything is executed — unknown names,
    # stray keys, records that will not resolve. Nothing here runs a check.
    planned_checks = _validated_checks(data, runner)

    raw_units = _as_object(data.get("units"), "units")
    for key in raw_units:
        if key not in DEFAULT_WEIGHTS:
            raise InputError(f"units: unknown unit {key!r}; expected one of {sorted(DEFAULT_WEIGHTS)}")
    # U_consistency is derived ONLY from the `consistency` object — a value
    # supplied directly in `units` is ignored, so a caller cannot fabricate a
    # present-and-zero U_consistency and satisfy the floor without a real score.
    units = {key: _as_nonneg_count(count, f"units.{key}")
             for key, count in raw_units.items() if key != "U_consistency"}

    cu = derive_consistency_unit(data.get("consistency"))
    if cu is not None:
        units["U_consistency"] = cu
    # Report the drop whenever the key was supplied — NOT only when derivation
    # failed. Hanging this off `elif` meant the worst case stayed silent: supply a
    # `consistency` object AND "U_consistency": 999 and the record reached VERIFIED
    # with ignored_inputs empty, hiding a direct contradiction. Derivation winning
    # is correct; concealing that it won is not.
    if "U_consistency" in raw_units:
        # The caller DID supply it, under a key that is deliberately ignored. Saying
        # only "missing" reads as "you forgot it" and sends them to add the very key
        # that is being dropped. Name the ignore and the remedy instead: a silent
        # drop is not fail-closed just because the verdict happens to be correct.
        supplied = raw_units["U_consistency"]
        if cu is None:
            ignored_inputs.append(
                f"units.U_consistency={supplied!r} was supplied but is ignored, and no "
                f"usable `consistency` object was given — this unit is derived only "
                f"from a `consistency` object with a numeric score, so that a "
                f"hand-written zero cannot satisfy the universal floor without one. "
                f"Supply {{\"consistency\": {{\"score\": N, \"critical_breaks\": N}}}} "
                f"instead.")
        else:
            # Both supplied. Derivation wins, which is correct — but the two disagree
            # and the caller is entitled to know which one the verdict rests on.
            ignored_inputs.append(
                f"units.U_consistency={supplied!r} was supplied and is ignored: the "
                f"value derived from the `consistency` object ({cu}) is authoritative. "
                f"Remove the direct key so the record cannot state two different "
                f"things.")

    # Only now are the checks RUN — after every cheap validation the record can
    # fail. Spawning four subprocesses and then rejecting the record for a
    # misspelled unit key would do work on input already known to be malformed, and
    # the ordering is the difference between validating a record and acting on it.
    derived_units: dict = {}
    derived_gates: dict = {}
    unattributed_issues: list[str] = []
    for name, (argv, expected) in planned_checks.items():
        got_units, got_gates, unattributed = runner.run(name, argv, expected)
        derived_units.update(got_units)
        derived_gates.update(got_gates)
        if unattributed:
            unattributed_issues.append(
                f"{name}: {unattributed} issue(s) belonging to no unit and no gate. "
                f"They are real outstanding work that nothing in the unit model "
                f"counts, so the verdict is held rather than reported clean")

    # A derived count wins over a reported one, and says so when they disagree.
    # Reporting an AGREEING value would be noise: nothing was dropped and no reader
    # is misled by a record that happens to carry last cycle's number. A
    # disagreement is the case that matters — the record asserts one thing, the
    # check found another, and the verdict rests on the check.
    for key in sorted(derived_units):
        value = float(derived_units[key])
        if key in units and units[key] != value:
            ignored_inputs.append(
                f"units.{key}={raw_units[key]!r} was supplied and is ignored: "
                f"{DERIVED_BY[key]} reported {value:g} for it. A count a check "
                f"produced is authoritative over one the record asserts — that is "
                f"the point of declaring the check. Remove the direct key so the "
                f"record cannot state two different things.")
        units[key] = value

    # weighted total (the routing/progress scalar)
    weighted_total = 0.0
    contributions = {}
    for key, count in units.items():
        w = weights.get(key, 1)
        contrib = w * count
        contributions[key] = contrib
        weighted_total += contrib

    # Required-present set: the units the caller declared in scope (frozen at
    # classification, spec §3.3) UNION the always-required universal floor;
    # default to the floor alone when no scope is declared. Fail closed — a
    # required unit that is absent is "not yet checked", not zero, so an input
    # that omits an in-scope check (e.g. a systematic review with no U_prisma)
    # cannot reach a done verdict.
    declared, declared_present = _validated_scope(data)
    required = list(UNIVERSAL_FLOOR) + [u for u in declared if u not in UNIVERSAL_FLOOR]
    missing_units = [u for u in required if u not in units]

    # Declaring scope is the rigorous path, and on it a unit a check CAN derive may
    # not be self-reported. Without this a systematic review omits the `checks`
    # block, hand-writes "U_prisma": 0, and reaches VERIFIED having run nothing —
    # the gap issue #4 was opened for. It bites only where a check exists: the
    # citation, screening, extraction and consistency units have no runnable check
    # in this table and stay reported, which the skill documentation states plainly
    # rather than leaving the reader to infer from a shorter list.
    underived_units = []
    underived_gates = []
    if declared_present:
        underived_units = sorted({u for u in declared
                                  if u in DERIVED_BY and u not in derived_units})
        # Gates get the same treatment through their scope proxy. Covering the
        # units alone left `H_rob` self-reported on the rigorous path, which is
        # the one place a self-reported zero costs the most.
        underived_gates = sorted(g for g, proxy in GATE_SCOPE_PROXY.items()
                                 if proxy in declared and g not in derived_gates)

    # predicate uses RAW counts: every required unit present AND all == 0
    auto_units_zero = not missing_units and all(c == 0 for c in units.values())

    # Human gates: when the caller declares scope (the rigorous/orchestrated path),
    # `gates` must be present AND an object — an omitted or null gates value cannot
    # silently assert "all human gates confirmed". Lenient (no scope declared) keeps
    # the simple default of "no gates reported = none pending".
    if declared_present and not isinstance(data.get("gates"), dict):
        raise InputError("gates: required as an object (even {}) when units_in_scope is declared")
    raw_gates = _as_object(data.get("gates"), "gates")
    unknown = [k for k in raw_gates if k not in GATE_KEYS]
    if unknown:
        raise InputError(f"gates: unknown gate key(s) {unknown}; expected {list(GATE_KEYS)}")
    gate_counts = {k: _as_int_count(raw_gates.get(k, 0), f"gates.{k}") for k in GATE_KEYS}
    # Same precedence as the units above, for the same reason: the appraisal check
    # counts the confirmations still owed, and a record asserting a different number
    # does not get to overrule it. A human gate is the one count a loop has the most
    # incentive to understate.
    for key in sorted(derived_gates):
        value = derived_gates[key]
        if key in raw_gates and gate_counts[key] != value:
            ignored_inputs.append(
                f"gates.{key}={raw_gates[key]!r} was supplied and is ignored: "
                f"rob_appraisal reported {value}. Remove the direct key so the "
                f"record cannot state two different things.")
        gate_counts[key] = value
    gates_remaining = sum(gate_counts.values())

    # dominant in-scope unit (for routing), highest weighted contribution
    dominant = None
    if contributions:
        dominant = max(
            contributions.items(),
            key=lambda kv: (kv[1], weights.get(kv[0], 1), kv[0]),
        )[0]
        if contributions[dominant] == 0:
            dominant = None

    return (weighted_total, auto_units_zero, gates_remaining, dominant,
            units, contributions, missing_units, ignored_inputs,
            underived_units, underived_gates, unattributed_issues)


def detect_plateau(history, current_total):
    """PLATEAU = PLATEAU_K consecutive flat-or-worse cycles (no decrease).

    Counts backward from the current cycle while each total is >= the one before
    it, and trips once that run reaches PLATEAU_K. A single real improvement
    (a strict decrease) breaks the run, so an actively-descending loop is never
    flagged — even right after a mid-run rise in the scalar (e.g. new in-scope
    work discovered). Needs PLATEAU_K + 1 samples so there are K transitions.
    """
    series = list(history) + [current_total]
    if len(series) < PLATEAU_K + 1:
        return False
    non_improving = 0
    for i in range(len(series) - 1, 0, -1):
        if series[i] >= series[i - 1]:   # flat or worse
            non_improving += 1
        else:
            break
    return non_improving >= PLATEAU_K


def verdict(data, weights, ceiling, runner=None):
    (weighted_total, auto_zero, gates_remaining, dominant, units,
     contributions, missing_units, ignored_inputs,
     underived_units, underived_gates, unattributed_issues) = compute(data, weights, runner)
    cycle = _as_int_count(data.get("cycle", 0), "cycle")

    raw_history = data.get("history")
    if raw_history is None:
        raw_history = []
    elif not isinstance(raw_history, list):
        raise InputError("history: expected an array of weighted totals")
    history = [_as_count(h, f"history[{i}]") for i, h in enumerate(raw_history)]

    advisory = cycle >= SOFT_ADVISORY_CYCLE

    # Tested BEFORE the two done-states, and ahead of the human gate on purpose. A
    # unit that could have been derived and was not, or a check reporting work no
    # unit tracks, both mean the numbers this verdict rests on are not established.
    # Neither is a repair stall and neither is a human's to clear: the agent adds
    # the `checks` entry, or fixes the record the check rejected. Reaching
    # BLOCKED_ON_HUMAN here would park an unestablished verdict on a person.
    unestablished = bool(underived_units or underived_gates or unattributed_issues)

    if unestablished:
        state = "CEILING" if cycle >= ceiling else "CONTINUE"
    elif auto_zero and gates_remaining == 0:
        state = "VERIFIED"
    elif auto_zero and gates_remaining > 0:
        state = "BLOCKED_ON_HUMAN"
    elif missing_units:
        # Incomplete input (a required in-scope unit was not reported) is not a
        # repair stall: never mislabel it PLATEAU. Keep going so the agent can
        # supply the missing check; the ceiling still bounds a misconfigured run.
        state = "CEILING" if cycle >= ceiling else "CONTINUE"
    elif detect_plateau(history, weighted_total):
        state = "PLATEAU"
    elif cycle >= ceiling:
        state = "CEILING"
    else:
        state = "CONTINUE"

    return {
        "state": state,
        "weighted_total": round(weighted_total, 3),
        "auto_units_zero": auto_zero,
        "gates_remaining": gates_remaining,
        "missing_units": missing_units,
        # In scope, and derivable by a check this record did not declare. The count
        # is present but self-reported, which on the scope-declaring path is not
        # enough — add a `checks` entry naming the record for each.
        "underived_units": underived_units,
        # The same, for a human gate. Its scope is read from the unit it moves
        # with, since a gate cannot be named in `units_in_scope`.
        "underived_gates": underived_gates,
        # Work a check reported that no unit and no gate counts, so it cannot appear
        # anywhere else in this verdict. Named rather than dropped.
        "unattributed_issues": unattributed_issues,
        # Input the check received and deliberately did not use. Empty in the normal
        # case; non-empty means a caller's value was dropped, and they are entitled
        # to know that rather than inferring it from a confusing `missing_units`.
        "ignored_inputs": ignored_inputs,
        # No dominant-unit routing while a required check is missing: the client
        # must clear `missing_units` first, not keep repairing a reported unit.
        "dominant_unit": dominant if (state == "CONTINUE" and not missing_units
                                      and not unestablished) else None,
        "cycle": cycle,
        "ceiling": ceiling,
        "soft_advisory": advisory,
        "units_evaluated": {k: round(float(v), 3) for k, v in units.items()},
        # weighted per-unit contribution — the manifest "by_unit" record
        "by_unit": {k: round(float(v), 3) for k, v in contributions.items()},
    }


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def floor_guard_status(prev_denoms, curr_denoms, exclusions_logged):
    """Anti-gaming (§5): flag a denominator that FELL between cycles.

    A dropped denominator (fewer citations/studies/themes than last cycle) is
    how a loop games a unit to zero by *removing* content. It is legitimate only
    when backed by a logged exclusion reason. Advisory: the script records and
    flags the drop; a human/agent judges legitimacy — it never silently credits
    a removal.
    """
    if not prev_denoms:
        return "ok"          # no prior baseline to compare against
    # NB: an empty curr_denoms is NOT an early "ok" — wiping every denominator
    # after a prior cycle reported them is the largest possible content removal
    # and must be flagged, so fall through to the union-of-keys loop below.
    drops = []
    # Union of keys: a denominator that *vanished* (key removed) is the biggest
    # possible content removal, so it must be flagged too — not just a lower value.
    for key in sorted(set(prev_denoms) | set(curr_denoms)):
        p = _num(prev_denoms.get(key))
        if p is None:
            continue                       # no prior baseline for this key
        c = _num(curr_denoms.get(key))
        if c is None:                      # key removed this cycle (or non-numeric)
            drops.append(f"{key} {prev_denoms.get(key)}->(removed)")
        elif c < p:
            drops.append(f"{key} {prev_denoms.get(key)}->{curr_denoms.get(key)}")
    if not drops:
        return "ok"
    tag = "logged-exclusion" if exclusions_logged else "UNLOGGED (no-op per §5)"
    return f"{tag}: " + ", ".join(drops)


def append_to_manifest(path, data, result):
    """Append this cycle's record to manifest.json's verification_units array.

    Makes the audit trail a *written artifact*, not a hand-maintained
    convention — same spirit as kappa.py / prisma_flow.py emitting real files.
    Creates the manifest (and the array) if absent; preserves any other keys.
    Records per-cycle denominators and a floor-guard status so an anti-gaming
    content-removal is detectable across cycles, not just by convention.

    Every appended record carries the `schema_version` its numbers were computed
    under. Validating only the transient input left the written history unlabelled,
    so a manifest spanning the U_grade/U_rob_trace redefinition held old and new
    `by_unit` values that look identical and mean different things.

    WHAT THE FIELD DOES AND DOES NOT DO. It labels the record for a reader of the
    audit trail — a human, or an agent resuming a run. Nothing in this module
    consumes it, and that is deliberate rather than unfinished: the only
    cross-cycle comparison made here is the floor guard's, which reads
    `denominators`, and the redefinition did not touch those. A legacy record
    stays a valid floor-guard baseline on purpose — skipping it would let a
    denominator drop across the version boundary go unflagged and weaken the
    anti-gaming guard to gain nothing. The plateau series is `history` from the
    caller's units.json, which this module cannot version or verify at all.

    Records already present without a version are stamped LEGACY_SCHEMA rather than
    assumed current: an explicit "we do not know which definitions this predates"
    is the honest migration, and silently adopting them into the current version
    would be the overclaim this field exists to prevent.
    """
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
        if not isinstance(manifest, dict):
            raise ValueError("manifest root is not a JSON object")
    except FileNotFoundError:
        manifest = {}

    history = manifest.setdefault("verification_units", [])
    if not isinstance(history, list):
        raise ValueError("manifest.verification_units exists but is not an array")

    # Migrate before appending, so the file never holds a versioned record beside an
    # ambiguous one that merely looks contemporary.
    for rec in history:
        if isinstance(rec, dict) and "schema_version" not in rec:
            rec["schema_version"] = LEGACY_SCHEMA

    # denominator values are validated numeric so a crafted non-numeric value
    # cannot silently blind the cross-cycle floor-guard comparison.
    raw_denoms = _as_object(data.get("denominators"), "denominators")
    denominators = {k: _as_int_count(v, f"denominators.{k}") for k, v in raw_denoms.items()}
    excl = data.get("exclusions_logged")
    if excl is not None and not isinstance(excl, bool):
        raise InputError("exclusions_logged: expected a boolean")
    # Baseline = denominators of the most recent ACCEPTED cycle (floor_guard not
    # UNLOGGED). An unlogged drop does NOT become the new baseline, so a later cycle
    # that keeps the same reduced denominators stays flagged (sticky) until the count
    # is restored or a logged exclusion is recorded — a drop can't be "normalised"
    # away by simply repeating it.
    prev_denoms = {}
    for rec in reversed(history):
        if not isinstance(rec, dict) or str(rec.get("floor_guard", "")).startswith("UNLOGGED"):
            continue
        d = rec.get("denominators")
        if isinstance(d, dict) and d:   # keep scanning past accepted records that carry no
            prev_denoms = d             # denominators, so an intermediate opt-out (or a pre-
            break                       # denominators record) can't reset the baseline to {}
    guard = floor_guard_status(prev_denoms, denominators, excl is True)

    # Anti-gaming (§5): an unlogged denominator drop means the units may have been
    # zeroed by REMOVING content, not resolving it — so it must not read as done.
    # Hold a would-be VERIFIED for human adjudication, and record the held state.
    if guard.startswith("UNLOGGED") and result["state"] == "VERIFIED":
        result["state"] = "BLOCKED_ON_HUMAN"
        result["hold_reason"] = "floor_guard: " + guard
        result["dominant_unit"] = None

    gates_in = _as_object(data.get("gates"), "gates")
    record = {
        # The version the counts in this record were computed under. Without it, a
        # by_unit value from before the U_grade/U_rob_trace redefinition is
        # indistinguishable from one after it.
        "schema_version": SCHEMA_VERSION,
        "cycle": result["cycle"],
        "state": result["state"],
        "weighted_total": result["weighted_total"],
        "by_unit": result["by_unit"],
        "gates": {k: _as_int_count(gates_in.get(k, 0), f"gates.{k}") for k in GATE_KEYS},
        "denominators": denominators,
        "floor_guard": guard,
        # agent-supplied annotation (progressed/no-op/failed/blocked/baseline)
        "outcome": data.get("outcome", "baseline" if result["cycle"] == 0 else ""),
    }

    history.append(record)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return record


def dry_run_preview(data, ceiling, runner=None):
    """Preview what the loop will do without running or writing anything."""
    _validate_record_schema(data)
    review_type = data.get("review_type", "unspecified")
    gates = _as_object(data.get("gates"), "gates")
    gates_will_fire = [k for k in GATE_KEYS if _as_int_count(gates.get(k, 0), f"gates.{k}") > 0]
    declared, declared_present = _validated_scope(data)
    in_scope = sorted((set(_as_object(data.get("units"), "units")) - {"U_consistency"})
                      | set(declared) | ({"U_consistency"} if data.get("consistency") else set()))
    # The full block validation — unknown check names, unknown entry keys, records
    # that do not resolve inside the root, scripts that are not there. It just does
    # not EXECUTE anything, so the promise below still holds while the preview
    # catches everything the run would.
    planned = _validated_checks(data, runner)
    will_derive = sorted({u for _, expected in planned.values() for u in expected})
    return {
        "dry_run": True,
        "review_type": review_type,
        "predicate": ("every in-scope auto-unit == 0 AND every human gate "
                      "CONFIRMED AND ai-disclosure.md current"),
        "universal_floor": list(UNIVERSAL_FLOOR),
        "units_in_scope": in_scope,
        "human_gates_that_will_fire": gates_will_fire,
        "checks_declared": sorted(planned),
        "units_that_will_be_derived": will_derive,
        # What the run will hold the verdict on. Derived from the same validated
        # block, so the preview cannot promise a check the run does not make.
        "underived_units": (sorted({u for u in declared
                                    if u in DERIVED_BY and u not in will_derive})
                            if declared_present else []),
        "underived_gates": (sorted(g for g, proxy in GATE_SCOPE_PROXY.items()
                                   if proxy in declared
                                   and DERIVED_BY_GATE[g] not in planned)
                            if declared_present else []),
        "ceiling": ceiling,
        "note": "preview only — no checks run, no state written",
    }


def main():
    ap = argparse.ArgumentParser(description="Compute verify-review units + verdict.")
    ap.add_argument("input", nargs="?", help="JSON file (default: stdin)")
    # --max-cycles is the documented name (spec §4); --ceiling kept as an alias.
    ap.add_argument("--max-cycles", "--ceiling", type=int, default=CEILING,
                    dest="ceiling", help="hard cycle ceiling (override, default 25)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print review type, predicate, units-in-scope, gates that "
                         "will fire, and ceiling; run no checks and write no state")
    ap.add_argument("--manifest", metavar="PATH",
                    help="append this cycle's record to PATH's verification_units array "
                         "(creates the file/array if absent)")
    ap.add_argument("--records-root", metavar="PATH",
                    help="directory a `checks` record path may point inside "
                         "(default: the directory holding the input, or the working "
                         "directory when reading stdin)")
    ap.add_argument("--skills-root", metavar="PATH",
                    help="directory holding the skills/ tree the checks live in "
                         "(default: this script's own repository)")
    args = ap.parse_args()
    if args.ceiling < 1:
        print(json.dumps({"error": "--max-cycles/--ceiling must be >= 1"}), file=sys.stderr)
        return 2

    # Read + parse + evaluate all fail closed: a missing/unreadable file,
    # non-JSON, or malformed field types produce an {"error": ...} verdict with a
    # non-zero exit, never a traceback or a spurious VERIFIED.
    # The read gets its own handler, wrapping ONLY the read. Catching
    # UnicodeDecodeError across the whole block relabelled an undecodable MANIFEST
    # as "cannot decode input" — the same mislabel, pointed at the other file.
    try:
        if args.input:
            with open(args.input, encoding="utf-8") as f:
                raw = f.read()
        else:
            raw = sys.stdin.read()
    except (OSError, UnicodeDecodeError) as e:
        print(json.dumps({"error": f"cannot read {args.input or 'stdin'}: {e}"}),
              file=sys.stderr)
        return 2

    # Parsing the input is the INPUT's business, so it gets its own handler too.
    # Leaving json.loads inside the block below meant a truncated units.json was
    # reported as "manifest error" — naming a file the caller may never have passed.
    # That is the mislabel this was twice supposed to remove, surviving each time in
    # whatever the narrowing left behind.
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"{args.input or 'stdin'} is not valid JSON: {e}"}),
              file=sys.stderr)
        return 2

    # Both roots come from the ARGV, never from the record: the operator running
    # this script is trusted, the file it reads is not. The default records root is
    # the directory holding units.json, because a review's artifacts sit beside it;
    # the default skills root is this script's own repository, three levels up from
    # skills/verify-review/scripts/.
    # `parents[3]` is skills/<name>/scripts/ walked back to the repository — but it
    # is evaluated OUTSIDE the try below that turns an InputError into a structured
    # verdict, so on a copy placed fewer than four levels deep it would raise
    # IndexError: a traceback and exit 1, where the contract says exit 2. Fall back
    # to the nearest ancestor instead and let the "check is not available" error
    # report it in the documented shape.
    here = Path(__file__).resolve()
    default_skills_root = here.parents[3] if len(here.parents) > 3 else here.parent
    runner = CheckRunner(
        records_root=Path(args.records_root) if args.records_root
        else (Path(args.input).resolve().parent if args.input else Path.cwd()),
        skills_root=Path(args.skills_root) if args.skills_root else default_skills_root)

    try:
        if not isinstance(data, dict):
            raise InputError("input must be a JSON object")

        if args.dry_run:
            print(json.dumps(dry_run_preview(data, args.ceiling, runner), indent=2))
            return 0

        result = verdict(data, DEFAULT_WEIGHTS, args.ceiling, runner)

        if args.manifest:
            record = append_to_manifest(args.manifest, data, result)
            result["manifest_record"] = record
            result["floor_guard"] = record["floor_guard"]
    except InputError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2
    except (ValueError, OSError) as e:
        # The input's read and its JSON parse both have their own handlers above, so
        # what remains here is the manifest's own read, parse and write. An
        # undecodable or malformed manifest is a ValueError and lands here, labelled
        # as what it is.
        print(json.dumps({"error": f"manifest error: {e}"}), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))

    return 0 if result["state"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
