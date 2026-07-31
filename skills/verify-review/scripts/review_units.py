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
  "exclusions_logged": false             # optional: a denominator drop is backed by a
                                         #   logged eligibility/exclusion reason (§5)
}

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
import sys

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
# NOTE what this module cannot do: it computes a verdict from the counts it is
# GIVEN. It does not run the checks or verify that a count came from a real run, so
# a hand-written units.json of all zeros reaches VERIFIED. That is true of every
# unit — this is a verdict calculator, not an orchestrator. Closing the gap means
# running the checks here and deriving the counts; tracked as its own change.
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
    "outcome",
}
CONSISTENCY_KEYS = {"score", "critical_breaks"}


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


def compute(data, weights):
    _validate_record_schema(data)
    ignored_inputs: list[str] = []
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
    raw_scope = data.get("units_in_scope")
    if raw_scope is None:
        declared, declared_present = [], False
    elif isinstance(raw_scope, list):
        declared, declared_present = raw_scope, True
    else:
        raise InputError("units_in_scope: expected an array of unit names")
    for u in declared:
        if not isinstance(u, str):
            raise InputError(f"units_in_scope: entries must be unit-name strings (got {u!r})")
        if u not in DEFAULT_WEIGHTS:
            raise InputError(f"units_in_scope: unknown unit {u!r}; expected one of {sorted(DEFAULT_WEIGHTS)}")
    required = list(UNIVERSAL_FLOOR) + [u for u in declared if u not in UNIVERSAL_FLOOR]
    missing_units = [u for u in required if u not in units]

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
    gates_remaining = sum(_as_int_count(raw_gates.get(k, 0), f"gates.{k}") for k in GATE_KEYS)

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
            units, contributions, missing_units, ignored_inputs)


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


def verdict(data, weights, ceiling):
    (weighted_total, auto_zero, gates_remaining, dominant, units,
     contributions, missing_units, ignored_inputs) = compute(data, weights)
    cycle = _as_int_count(data.get("cycle", 0), "cycle")

    raw_history = data.get("history")
    if raw_history is None:
        raw_history = []
    elif not isinstance(raw_history, list):
        raise InputError("history: expected an array of weighted totals")
    history = [_as_count(h, f"history[{i}]") for i, h in enumerate(raw_history)]

    advisory = cycle >= SOFT_ADVISORY_CYCLE

    if auto_zero and gates_remaining == 0:
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
        # Input the check received and deliberately did not use. Empty in the normal
        # case; non-empty means a caller's value was dropped, and they are entitled
        # to know that rather than inferring it from a confusing `missing_units`.
        "ignored_inputs": ignored_inputs,
        # No dominant-unit routing while a required check is missing: the client
        # must clear `missing_units` first, not keep repairing a reported unit.
        "dominant_unit": dominant if (state == "CONTINUE" and not missing_units) else None,
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


def dry_run_preview(data, ceiling):
    """Preview what the loop will do without running or writing anything."""
    _validate_record_schema(data)
    review_type = data.get("review_type", "unspecified")
    gates = _as_object(data.get("gates"), "gates")
    gates_will_fire = [k for k in GATE_KEYS if _as_int_count(gates.get(k, 0), f"gates.{k}") > 0]
    declared = data.get("units_in_scope")
    declared = declared if isinstance(declared, list) else []
    in_scope = sorted((set(_as_object(data.get("units"), "units")) - {"U_consistency"})
                      | set(declared) | ({"U_consistency"} if data.get("consistency") else set()))
    return {
        "dry_run": True,
        "review_type": review_type,
        "predicate": ("every in-scope auto-unit == 0 AND every human gate "
                      "CONFIRMED AND ai-disclosure.md current"),
        "universal_floor": list(UNIVERSAL_FLOOR),
        "units_in_scope": in_scope,
        "human_gates_that_will_fire": gates_will_fire,
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

    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise InputError("input must be a JSON object")

        if args.dry_run:
            print(json.dumps(dry_run_preview(data, args.ceiling), indent=2))
            return 0

        result = verdict(data, DEFAULT_WEIGHTS, args.ceiling)

        if args.manifest:
            record = append_to_manifest(args.manifest, data, result)
            result["manifest_record"] = record
            result["floor_guard"] = record["floor_guard"]
    except InputError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2
    except (ValueError, OSError) as e:
        # Reached only by the manifest read/write now that the input read has its
        # own handler above. UnicodeDecodeError is a ValueError, so an undecodable
        # manifest lands here and is labelled as what it is.
        print(json.dumps({"error": f"manifest error: {e}"}), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))

    return 0 if result["state"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
