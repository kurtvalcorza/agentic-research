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
  "schema_version": "1.0",
  "review_type": "systematic",
  "cycle": 3,
  "units_in_scope": ["U_screen", "U_extract", "U_prisma", "U_grade"],
  "units": {
    "U_cite_external": 2,
    "U_cite_internal": 0,
    "U_screen": 1,
    "U_extract": 0,
    "U_prisma": 0,
    "U_grade": 0
  },
  "consistency": { "score": 71, "critical_breaks": 0 },
  "gates": { "H_rob": 4, "H_screen_adj": 0, "H_cite_manual": 1, "H_numeric": 0 },
  "history": [14, 11, 9],
  "denominators": { "citations": 40, "studies": 22, "themes": 8 },
  "exclusions_logged": false,
  "checks": {
    "prisma_flow": { "record": "artifacts/counts.json" },
    "grade_profile": { "record": "artifacts/certainty.json",
                       "rob_record": "artifacts/appraisal.json" }
  }
}
```

Rules:
- `checks` (optional) makes a count **derived** instead of asserted: the named
  check is run with `--strict --json` and what it reports overrides what `units`
  says. `prisma_flow` → `U_prisma`; `prisma_checklist` → `U_checklist`;
  `grade_profile` → `U_grade`, and `U_rob_trace` only when `rob_record` is given;
  `rob_appraisal` → the `H_rob` gate. **When `units_in_scope` is declared, every
  in-scope unit a check can derive needs an entry**, or it lands in
  `underived_units` and the verdict is held. So does **`H_rob` whenever
  `U_rob_trace` is in scope** — a gate cannot be named in `units_in_scope`, so it
  reads its scope from the unit it moves with, and it lands in `underived_gates`.
  A disagreement between a derived and a reported count is named in
  `ignored_inputs`; an agreeing one is not, because nothing was dropped.
  The check name is a key into a fixed table, never a path, and the argv is built
  by the backend — nothing here reaches it. Record paths must resolve inside
  `--records-root` (default: the directory holding `units.json`). A check that
  exits 2, crashes, times out, or emits an envelope the backend cannot validate is
  an **error**, never a count of zero.
- **Only include in-scope units**, but the **universal floor** (`U_cite_external`,
  `U_cite_internal`, `U_consistency`) must always be present — a `VERIFIED` verdict
  is impossible while any floor unit is missing (`missing_units` lists them). An
  omitted *non-floor* unit is *absent* (a narrative review has no `U_prisma`), not
  zero-to-achieve; including it as `0` is also fine — it just contributes nothing.
- `units_in_scope` (optional) is the **frozen in-scope set** resolved at
  classification (spec §3.3). When present, every unit it lists — not just the
  floor — must be present and `0` before `VERIFIED`, so a systematic run that
  silently omits `U_prisma` is caught (`missing_units`) instead of passing. Omit
  it and only the universal floor is enforced. The floor is always required,
  whether or not it appears in the list.
  When a cycle re-runs only the checks whose inputs changed, **carry forward the
  last-known value of every in-scope unit** (floor *and* declared) into that
  cycle's `units.json` (and pass `consistency` with its score) so nothing lands in
  `missing_units` — otherwise the cycle cannot reach `VERIFIED`/`BLOCKED_ON_HUMAN`.
  Declaring `units_in_scope` also **requires the `gates` key to be present** (even
  `{}`): an omitted gates object cannot silently assert all human gates confirmed.
- `U_consistency` is derived **only** from the `consistency` object (which needs a
  numeric `score`); a value placed directly in `units` is ignored, so it cannot
  fake a present-and-zero floor unit.
- Counts must be finite non-negative numbers; gate, cycle, and denominator counts
  must be whole numbers. Booleans, `NaN`/`Infinity`, negatives, and wrong field
  types (incl. an empty `[]`/`""` where an object is expected) fail closed with an
  `{"error": …}` verdict and a non-zero exit — never a spurious `VERIFIED`.
- `denominators` (optional) are the current totals behind the units (citation
  count, study count, theme count …). `exclusions_logged` (optional, a real
  boolean) marks that a drop in a denominator this cycle is backed by a logged
  exclusion reason. Together they drive the floor-guard check (§6).
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
  "missing_units": [],
  "underived_units": [],
  "underived_gates": [],
  "unattributed_issues": [],
  "dominant_unit": "U_cite_external",
  "cycle": 2,
  "ceiling": 25,
  "soft_advisory": false,
  "units_evaluated": { "U_cite_external": 2.0, "U_cite_internal": 0.0, "U_screen": 3.0, "U_consistency": 4.0 },
  "by_unit": { "U_cite_external": 6.0, "U_cite_internal": 0.0, "U_screen": 3.0, "U_consistency": 4.0 }
}
```

- `state` ∈ {`VERIFIED`, `BLOCKED_ON_HUMAN`, `PLATEAU`, `CEILING`, `CONTINUE`}.
- Exit code is `0` only for `VERIFIED`, non-zero otherwise — so it gates a
  pipeline like `prisma_flow.py --strict`.
- `units_evaluated` are the **raw** in-scope counts; `by_unit` are the **weighted**
  contributions (`weightᵢ × countᵢ`) that sum to `weighted_total`.
- `missing_units` lists any **required** unit absent from the input — the
  universal floor (`U_cite_external`, `U_cite_internal`, `U_consistency`) plus any
  unit named in `units_in_scope`. It is **non-empty ⇒ never `VERIFIED`** (and
  never `PLATEAU`: incomplete input reports `CONTINUE` so the missing check can be
  run, not a false stall). So an empty/citation-less `units.json`, or a systematic
  run that omits a declared `U_prisma`, fails closed rather than passing.
  (`U_consistency` is derived **only** from the `consistency` object; a value
  placed directly in `units` is ignored, so it can't fake the floor.)
- `underived_units` lists in-scope units a check could have derived where the
  `checks` block named no record for it. The count is present — it is simply
  self-reported, which on the scope-declaring path is not enough. **Non-empty ⇒
  never `VERIFIED`**, and no amount of repair work clears it: add the entry.
- `underived_gates` is the same for a human gate. A gate cannot appear in
  `units_in_scope`, so it reads its scope from the unit it moves with: `H_rob` is
  required whenever `U_rob_trace` is in scope. **Non-empty ⇒ never `VERIFIED`.**
- `unattributed_issues` lists work a check reported that no unit and no gate
  counts, so it appears nowhere else in the verdict. Today that is a risk-of-bias
  record failing its own instrument. **Non-empty ⇒ never `VERIFIED`.**
- `dominant_unit` is populated only when `state == CONTINUE`; it is the in-scope
  unit with the largest **weighted** contribution (ties broken by weight, then
  name). This is the routing target.
- `soft_advisory` is `true` from cycle 10 onward; it is informational and never
  changes `state`.

## 3. State machine (precedence order)

Evaluated top-down each cycle; first match wins:

1. `underived_units OR underived_gates OR unattributed_issues` non-empty →
   **CONTINUE** (**CEILING** at the ceiling)
2. `auto_units_zero AND gates_remaining == 0` → **VERIFIED**
3. `auto_units_zero AND gates_remaining > 0` → **BLOCKED_ON_HUMAN**
4. `missing_units` non-empty → **CONTINUE** (**CEILING** at the ceiling)
5. plateau (`PLATEAU_K = 3` consecutive non-improving cycles) → **PLATEAU**
6. `cycle ≥ ceiling (25)` → **CEILING**
7. otherwise → **CONTINUE**

Note ordering: a run that reaches all-mechanical-zero **and** has open human
gates is `BLOCKED_ON_HUMAN`, not `PLATEAU`, even if the scalar was flat while the
human work waited — human-gate work is not a stall.

Rule 1 sits above the human gate for the same kind of reason, pointing the other
way. A count nothing established, or work no unit counts, is the **agent's** to
resolve — declare the check, or fix the record the check rejected — and reaching
`BLOCKED_ON_HUMAN` there would park an unestablished verdict on a person, waiting
for a signature nobody asked for. Neither is a repair stall either, so neither may
be reported as `PLATEAU`: the loop is not stuck, it has been handed an incomplete
question.

## 4. Plateau definition

`PLATEAU` = the weighted total was **flat or worse** (`total[i] ≥ total[i-1]`)
for `PLATEAU_K = 3` consecutive cycles, counting backward from the current cycle;
it needs `PLATEAU_K + 1` samples so there are `K` transitions to check. A single
strict improvement breaks the run, so an **actively-descending** loop is never
falsely stalled — even right after a mid-run rise in the scalar (new in-scope
work discovered, then repaired back down, e.g. `3,10,9,8` keeps going). This
catches genuine stalls (`10,10,10,10`); it does **not** early-stop pure
oscillation that dips every other cycle (`8,9,8,9,8`) — that runs to the ceiling
rather than risk aborting a loop that is in fact making progress. A cycle whose
units cannot be computed (a check crashed) should be
recorded as `unknown` and **excluded** from the history array, so it does not
falsely trip or reset the plateau counter; repeated `unknown`s on the same unit
are an operational failure to surface, not a `PLATEAU`.

## 5. `verification_units` manifest extension

Append one record per cycle to the orchestrator's existing `manifest.json`
(do **not** create a separate state file). This is **written by the backend**,
not maintained by hand — `review_units.py --manifest <path>` appends the record
it just computed, creating the file and the array if absent and leaving any other
manifest keys untouched:

```
python scripts/review_units.py units.json --manifest manifest.json
```

The agent's per-cycle annotation rides in on the input `units.json` as
`"outcome": "progressed: …"`; cycle 0 defaults to `"baseline"`. The written
record is `{schema_version, cycle, state, weighted_total, by_unit, gates,
denominators, floor_guard, outcome}` (note `by_unit` is the **weighted**
contribution per unit, so a count of 3 on the ×3-weighted `U_cite_external`
records as `9.0`; `denominators`/`floor_guard` carry the anti-gaming trail
from §6):

```json
"verification_units": [
  { "schema_version": "1.0", "cycle": 0, "state": "CONTINUE", "weighted_total": 14.0,
    "by_unit": {"U_cite_external": 9.0, "U_consistency": 4.0, "U_prisma": 1.0},
    "gates": {"H_rob": 4, "H_screen_adj": 0, "H_cite_manual": 1, "H_numeric": 0},
    "denominators": {"citations": 40, "studies": 22}, "floor_guard": "ok",
    "outcome": "baseline" },
  { "schema_version": "1.0", "cycle": 1, "state": "CONTINUE", "weighted_total": 11.0,
    "by_unit": {"U_cite_external": 6.0, "U_consistency": 4.0, "U_prisma": 1.0},
    "gates": {"H_rob": 4, "H_screen_adj": 0, "H_cite_manual": 1, "H_numeric": 0},
    "denominators": {"citations": 40, "studies": 22}, "floor_guard": "ok",
    "outcome": "progressed: verify-sources cleared 1 fabricated citation" }
]
```

**`schema_version` labels the record, and nothing in this script reads it.** The
units have been redefined once (`U_grade`, `U_rob_trace`), so a `by_unit` value
written before that change and one written after look identical and mean
different things. The field exists so a *reader of the audit trail* — a human, a
resuming agent — can tell which definitions a record's counts were computed
under. It is not consumed here: the only cross-cycle comparison this script makes
is the floor guard's, and that reads `denominators`, which the redefinition did
not touch. A legacy record is therefore still a valid floor-guard baseline, and
deliberately so — skipping it would let a denominator drop across the version
boundary go unflagged, weakening the anti-gaming guard to gain nothing.

A record written before the field existed is stamped `"schema_version":
"unversioned"` on the next append. That is a label, not an adoption: the
definitions those counts were computed under are unknown, and writing `"1.0"`
onto them would assert exactly what cannot be checked. The plateau series the
loop actually routes on is `history` in the **input** `units.json` — a bare array
of prior weighted totals supplied by the caller, which this script cannot version
or verify. Comparing totals across a redefinition remains the caller's
responsibility.

`outcome` ∈ {`baseline`, `progressed: …`, `no-op: …`, `failed: …`,
`blocked: …`}. A `no-op` is recorded (not silently dropped) so the plateau
counter and the audit trail both see it.

## 6. Floor-guard accounting (worked)

The floor-guard (`SKILL.md` § anti-gaming) is judged at units-accounting time —
whether a removal is *legitimate* is a human/agent call — but the backend makes it
**mechanically detectable** rather than trusting self-report. Pass per-cycle
`denominators`; `review_units.py --manifest` records them and sets a `floor_guard`
status on the record: a denominator that **fell** since the previous cycle — or
whose key was **removed entirely** (including wiping all denominators after a prior
cycle reported them) — is flagged `UNLOGGED (no-op per §5): citations 40->38`
unless the input sets `exclusions_logged: true` (then `logged-exclusion: …`). The
drop is written into the audit trail, and an `UNLOGGED` drop also **holds a
would-be `VERIFIED` as `BLOCKED_ON_HUMAN`** (with a `hold_reason`) so the exit code
cannot mark the review complete when its units may have been zeroed by removing
content — a human adjudicates:

- If a cycle reduced `U_cite_external` by deleting a citation rather than
  resolving it, the `citations` denominator falls and `floor_guard` flags it
  `UNLOGGED`; record `outcome: "no-op: citation removed without logged
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
