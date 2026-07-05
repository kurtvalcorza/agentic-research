#!/usr/bin/env python3
"""
review_units.py — compute the weighted "units remaining" scalar and the loop
verdict for the verify-review skill.

Stdlib only. Mirrors the convention of the other runnable backends in this
suite (screen-literature/kappa.py, prisma-flow/prisma_flow.py).

INPUT (a JSON file, or stdin):
{
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
  "consistency": {"score": 71, "critical_breaks": 0},   # optional -> derives U_consistency
  "gates": {"H_rob": 4, "H_screen_adj": 0, "H_cite_manual": 1},  # human-gate counts
  "history": [14, 11, 9],                # prior WEIGHTED totals, oldest first (optional)
  "denominators": {"citations": 40, "studies": 22, "themes": 8},  # optional, floor-guard
  "exclusions_logged": false             # optional: a denominator drop is backed by a
                                         #   logged eligibility/exclusion reason (§5)
}

Only pass the units that are IN SCOPE for the review type (see SKILL.md §
"Units in scope"). Omitted units are treated as absent, not as zero-to-achieve.
Citation integrity + consistency are the UNIVERSAL FLOOR: a VERIFIED verdict
requires them to be present and zero for *every* review type — an empty or
citation-less units map can never be VERIFIED (the gate fails closed).

OUTPUT: a JSON verdict on stdout. Exit code 0 only when VERIFIED; non-zero
otherwise (so it can gate a pipeline like `prisma_flow.py --strict`).
"""

import argparse
import json
import sys

# --- configuration (single source of truth for weights / thresholds) --------
# Q1: fabricated/unverifiable citations dominate routing and the climb gradient.
DEFAULT_WEIGHTS = {
    "U_cite_external": 3,
    "U_cite_internal": 1,
    "U_screen": 1,
    "U_extract": 1,
    "U_prisma": 1,
    "U_grade": 1,
    "U_consistency": 1,
}
CONSISTENCY_GATE = 75      # validate-consistency pass threshold
PLATEAU_K = 3              # consecutive flat-or-worse cycles -> PLATEAU
SOFT_ADVISORY_CYCLE = 10   # advisory only; does NOT stop the loop
CEILING = 25               # hard backstop

GATE_KEYS = ("H_rob", "H_screen_adj", "H_cite_manual")

# Citation integrity + consistency are universal for EVERY review type (spec
# §3.3): the floor the loop guarantees for any review. A VERIFIED verdict must
# have these present and zero, so an empty/partial units map fails closed.
UNIVERSAL_FLOOR = ("U_cite_external", "U_cite_internal", "U_consistency")


def derive_consistency_unit(consistency):
    """Q2: graded gradient = critical_breaks + max(0, 75 - score).

    Returns None (unit absent) when there is no numeric score — a consistency
    object without a real score means the check was not measured, so the floor
    unit must stay absent (fail closed) rather than fabricate a present-and-zero
    U_consistency that could satisfy the gate without a genuine >=75 result.
    """
    if not consistency:
        return None
    score = consistency.get("score")
    if score is None:
        return None
    breaks = int(consistency.get("critical_breaks", 0))
    return breaks + max(0, CONSISTENCY_GATE - float(score))


def compute(data, weights):
    units = dict(data.get("units", {}))

    cu = derive_consistency_unit(data.get("consistency"))
    if cu is not None:
        units["U_consistency"] = cu

    # weighted total (the routing/progress scalar)
    weighted_total = 0.0
    contributions = {}
    for key, count in units.items():
        w = weights.get(key, 1)
        contrib = w * float(count)
        contributions[key] = contrib
        weighted_total += contrib

    # Fail closed: the universal-floor units must be PRESENT before the loop can
    # call a review done. A missing floor unit is "not yet checked", not zero.
    missing_units = [u for u in UNIVERSAL_FLOOR if u not in units]

    # predicate uses RAW counts: every in-scope unit present AND all == 0
    auto_units_zero = (
        not missing_units and all(float(c) == 0 for c in units.values())
    )

    gates = data.get("gates", {})
    gates_remaining = sum(int(gates.get(k, 0)) for k in GATE_KEYS)

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
            units, contributions, missing_units)


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
     contributions, missing_units) = compute(data, weights)
    cycle = int(data.get("cycle", 0))
    history = data.get("history", [])

    advisory = cycle >= SOFT_ADVISORY_CYCLE

    if auto_zero and gates_remaining == 0:
        state = "VERIFIED"
    elif auto_zero and gates_remaining > 0:
        state = "BLOCKED_ON_HUMAN"
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
        "dominant_unit": dominant if state == "CONTINUE" else None,
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
    if not curr_denoms or not prev_denoms:
        return "ok"
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

    denominators = data.get("denominators", {})
    prev_denoms = history[-1].get("denominators", {}) if history else {}
    guard = floor_guard_status(prev_denoms, denominators,
                               bool(data.get("exclusions_logged")))

    record = {
        "cycle": result["cycle"],
        "state": result["state"],
        "weighted_total": result["weighted_total"],
        "by_unit": result["by_unit"],
        "gates": {k: int(data.get("gates", {}).get(k, 0)) for k in GATE_KEYS},
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
    review_type = data.get("review_type", "unspecified")
    gates = data.get("gates", {})
    gates_will_fire = [k for k in GATE_KEYS if int(gates.get(k, 0)) > 0]
    in_scope = sorted(set(data.get("units", {})) |
                      ({"U_consistency"} if data.get("consistency") else set()))
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

    raw = open(args.input).read() if args.input else sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON: {e}"}), file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps(dry_run_preview(data, args.ceiling), indent=2))
        return 0

    result = verdict(data, DEFAULT_WEIGHTS, args.ceiling)

    if args.manifest:
        try:
            result["manifest_record"] = append_to_manifest(args.manifest, data, result)
        except (ValueError, OSError) as e:
            print(json.dumps({"error": f"manifest write failed: {e}"}), file=sys.stderr)
            return 2

    print(json.dumps(result, indent=2))

    return 0 if result["state"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
