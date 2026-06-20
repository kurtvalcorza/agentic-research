# verify-review — Loop Protocol & Schemas

Deep mechanics for the `verify-review` skill. The `SKILL.md` is the operational
summary; this is the reference for the state schema, the `review_units.py`
contract, and the edge cases.

---

## 1. `units.json` input schema

Assembled each cycle from the in-scope checks' outputs and passed to
`scripts/review_units.py`:

```json
{
  "review_type": "systematic",
  "cycle": 3,
  "units": {
    "U_cite_external": 2,
    "U_cite_internal": 0,
    "U_screen": 1,
    "U_extract": 0,
    "U_prisma": 0,
    "U_grade": 0
  },
  "consistency": { "score": 71, "critical_breaks": 0 },
  "gates": { "H_rob": 4, "H_screen_adj": 0, "H_cite_manual": 1 },
  "history": [14, 11, 9]
}
```

Rules:
- **Only include in-scope units.** An omitted unit is *absent* (narrative review
  has no `U_prisma`), not zero-to-achieve. Including it as `0` is also fine — it
  just contributes nothing.
- `consistency` is optional; when present it derives `U_consistency =
  critical_breaks + max(0, 75 − score)` (graded gradient, Q2).
- `history` is the list of prior **weighted totals**, oldest first, *excluding*
  the current cycle. The script appends the current total internally for plateau
  detection.

## 2. `review_units.py` output contract

```json
{
  "state": "CONTINUE",
  "weighted_total": 13.0,
  "auto_units_zero": false,
  "gates_remaining": 0,
  "dominant_unit": "U_cite_external",
  "cycle": 2,
  "ceiling": 25,
  "soft_advisory": false,
  "units_evaluated": { "U_cite_external": 2.0, "U_prisma": 3.0, "U_consistency": 4.0 }
}
```

- `state` ∈ {`VERIFIED`, `BLOCKED_ON_HUMAN`, `PLATEAU`, `CEILING`, `CONTINUE`}.
- Exit code is `0` only for `VERIFIED`, non-zero otherwise — so it gates a
  pipeline like `prisma_flow.py --strict`.
- `dominant_unit` is populated only when `state == CONTINUE`; it is the in-scope
  unit with the largest **weighted** contribution (ties broken by weight, then
  name). This is the routing target.
- `soft_advisory` is `true` from cycle 10 onward; it is informational and never
  changes `state`.

## 3. State machine (precedence order)

Evaluated top-down each cycle; first match wins:

1. `auto_units_zero AND gates_remaining == 0` → **VERIFIED**
2. `auto_units_zero AND gates_remaining > 0` → **BLOCKED_ON_HUMAN**
3. plateau (`PLATEAU_K = 3` consecutive non-improving cycles) → **PLATEAU**
4. `cycle ≥ ceiling (25)` → **CEILING**
5. otherwise → **CONTINUE**

Note ordering: a run that reaches all-mechanical-zero **and** has open human
gates is `BLOCKED_ON_HUMAN`, not `PLATEAU`, even if the scalar was flat while the
human work waited — human-gate work is not a stall.

## 4. Plateau definition

`PLATEAU` = the weighted total was **flat or worse** (`total[i] ≥ total[i-1]`)
for `PLATEAU_K = 3` consecutive cycles, counting backward from the current cycle.
This catches both true stalls (no progress) and thrash (oscillation that nets
zero). A cycle whose units cannot be computed (a check crashed) should be
recorded as `unknown` and **excluded** from the history array, so it does not
falsely trip or reset the plateau counter; repeated `unknown`s on the same unit
are an operational failure to surface, not a `PLATEAU`.

## 5. `verification_units` manifest extension

Append one record per cycle to the orchestrator's existing `manifest.json`
(do **not** create a separate state file):

```json
"verification_units": [
  { "cycle": 0, "weighted_total": 14.0,
    "by_unit": {"U_cite_external": 9.0, "U_consistency": 4.0, "U_prisma": 1.0},
    "gates": {"H_rob": 4, "H_cite_manual": 1},
    "outcome": "baseline" },
  { "cycle": 1, "weighted_total": 11.0,
    "by_unit": {"U_cite_external": 6.0, "U_consistency": 4.0, "U_prisma": 1.0},
    "gates": {"H_rob": 4, "H_cite_manual": 1},
    "outcome": "progressed: verify-sources cleared 1 fabricated citation" }
]
```

`outcome` ∈ {`baseline`, `progressed: …`, `no-op: …`, `failed: …`,
`blocked: …`}. A `no-op` is recorded (not silently dropped) so the plateau
counter and the audit trail both see it.

## 6. Floor-guard accounting (worked)

The floor-guard (`SKILL.md` § anti-gaming) is enforced at units-accounting time,
not by the script:

- If a cycle reduced `U_cite_external` by deleting a citation rather than
  resolving it, record `outcome: "no-op: citation removed without logged
  exclusion reason"` and **do not** credit the reduction — recompute the unit as
  if the citation still needed resolution, or route it to `H_cite_manual`.
- A citation the backend can only mark `UNVERIFIED (manual)` is moved from
  `U_cite_external` to `gates.H_cite_manual` in the next `units.json`. It is never
  counted as a cleared auto-unit.
- A regression (consistency dropped below 75, a reconciled PRISMA arm re-opened)
  is reverted before the next compute; the reverted state is what gets recorded.

## 7. Worked example (systematic, abbreviated)

```
cycle 0  baseline           U=14  gates{H_rob:4,H_cite_manual:1}  → CONTINUE (U_cite_external)
cycle 1  verify-sources     U=11  (cleared 1 fabricated cite)     → CONTINUE (U_cite_external)
cycle 2  verify-sources     U= 8  (1 cite → H_cite_manual)        → CONTINUE (U_consistency)
cycle 3  validate-consistency U=4 (score 71→76)                   → CONTINUE (U_prisma)
cycle 4  prisma-flow        U= 0  arithmetic reconciles           → BLOCKED_ON_HUMAN
                            (auto-zero; H_rob:4, H_cite_manual:2 await human)
         → emit handoff checklist; stop. Not VERIFIED until human confirms gates.
```

## 8. Standalone vs orchestrated invocation

- **Orchestrated:** `orchestrate-research` sets `review_type` in the manifest and
  calls `verify-review` at the validation phase; the verdict + `handoff` fold back
  into the manifest for any downstream step.
- **Standalone** ("verify this manuscript"): no manifest — classify `review_type`
  from the draft and the artifacts present, resolve in-scope units, and write a
  fresh `manifest.json` in the run workspace so state/provenance still accrue.
