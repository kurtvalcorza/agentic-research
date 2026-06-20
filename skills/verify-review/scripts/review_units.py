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
  "history": [14, 11, 9]                 # prior WEIGHTED totals, oldest first (optional)
}

Only pass the units that are IN SCOPE for the review type (see SKILL.md §
"Units in scope"). Omitted units are treated as absent, not as zero-to-achieve.

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
PLATEAU_K = 3              # consecutive non-improving cycles -> PLATEAU
SOFT_ADVISORY_CYCLE = 10   # advisory only; does NOT stop the loop
CEILING = 25               # hard backstop

GATE_KEYS = ("H_rob", "H_screen_adj", "H_cite_manual")


def derive_consistency_unit(consistency):
    """Q2: graded gradient = critical_breaks + max(0, 75 - score)."""
    if not consistency:
        return None
    score = consistency.get("score")
    breaks = int(consistency.get("critical_breaks", 0))
    if score is None:
        return breaks
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

    # predicate uses RAW counts: every in-scope unit must be 0
    auto_units_zero = all(float(c) == 0 for c in units.values())

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

    return weighted_total, auto_units_zero, gates_remaining, dominant, units, contributions


def detect_plateau(history, current_total):
    """PLATEAU = PLATEAU_K consecutive cycles with no improvement (no decrease)."""
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
    weighted_total, auto_zero, gates_remaining, dominant, units, contributions = compute(data, weights)
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
        "dominant_unit": dominant if state == "CONTINUE" else None,
        "cycle": cycle,
        "ceiling": ceiling,
        "soft_advisory": advisory,
        "units_evaluated": {k: round(float(v), 3) for k, v in units.items()},
        # weighted per-unit contribution — the manifest "by_unit" record
        "by_unit": {k: round(float(v), 3) for k, v in contributions.items()},
    }


def append_to_manifest(path, data, result):
    """Append this cycle's record to manifest.json's verification_units array.

    Makes the audit trail a *written artifact*, not a hand-maintained
    convention — same spirit as kappa.py / prisma_flow.py emitting real files.
    Creates the manifest (and the array) if absent; preserves any other keys.
    """
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
        if not isinstance(manifest, dict):
            raise ValueError("manifest root is not a JSON object")
    except FileNotFoundError:
        manifest = {}

    record = {
        "cycle": result["cycle"],
        "state": result["state"],
        "weighted_total": result["weighted_total"],
        "by_unit": result["by_unit"],
        "gates": {k: int(data.get("gates", {}).get(k, 0)) for k in GATE_KEYS},
        # agent-supplied annotation (progressed/no-op/failed/blocked/baseline)
        "outcome": data.get("outcome", "baseline" if result["cycle"] == 0 else ""),
    }

    history = manifest.setdefault("verification_units", [])
    if not isinstance(history, list):
        raise ValueError("manifest.verification_units exists but is not an array")
    history.append(record)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return record


def main():
    ap = argparse.ArgumentParser(description="Compute verify-review units + verdict.")
    ap.add_argument("input", nargs="?", help="JSON file (default: stdin)")
    ap.add_argument("--ceiling", type=int, default=CEILING, help="hard cycle ceiling")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero unless VERIFIED (default behaviour anyway)")
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
