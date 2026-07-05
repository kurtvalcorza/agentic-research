---
name: verify-review
description: Drive a research review to a verifiably-finished end-state by looping the validation skills (verify-sources, validate-citations, validate-consistency, prisma-flow, validate-evidence) against a mechanical "units remaining" predicate until every auto-reducible defect is zero — then cleanly hand off to the human gates (risk-of-bias confirmation, numeric verification, conflict adjudication). Use after a draft/synthesis exists, to verify a manuscript before submission, or as the validation phase of orchestrate-research. Runs on top of single-pass validation (the snapshot is its cycle-0 baseline) as a bounded, audited self-correcting loop.
---

# verify-review

## Purpose

The suite's validation skills (`validate-citations`, `verify-sources`, `validate-consistency`, `prisma-flow`, `validate-evidence`) each run **once** in the normal pipeline. But the failure modes they catch — fabricated citations, screening disagreements above the κ floor, PRISMA arms that don't reconcile, a consistency score below the gate, ungraded GRADE domains — are exactly the kind that survive a single pass and need *re-checking after a repair*.

`verify-review` is a **bounded, self-correcting loop** over those checks. It computes a mechanical **units remaining** scalar from the artifacts the existing skills already emit, routes one repair at a time at the highest-leverage defect, re-checks, and repeats until a **success predicate** holds — or until only a human can move the number, at which point it **stops and hands off**.

It does **not** re-implement any check or judgment. It *sequences and re-runs* the existing skills and accounts the result.

> Full design rationale: [`docs/verification-loop-spec.md`](../../docs/verification-loop-spec.md). Deep mechanics: `references/loop-protocol.md`.

## The inversion that matters

This loop is adapted from a general autonomous code-improvement engine, but with one deliberate inversion: **where that pattern loops to *avoid* human intervention, this loop runs to *cleanly hand off* to it.** Risk-of-bias appraisal, numeric verification, and screening-conflict adjudication are documented LLM weak points — they are **human gates by design**, never auto-resolved. The loop's job is to clear everything mechanical so the human's attention lands only where it's actually needed.

## When to use

- After a draft/synthesis exists and you want it **verified to a finished state**, not just spot-checked.
- Before submitting or trusting any AI-assisted manuscript, review, or synthesis.
- As the **validation phase of `orchestrate-research`** (it routes here **in addition to** the single-pass `validate-*` fan-out, whose snapshot becomes this loop's cycle-0 baseline — both run, neither replaces the other).
- Ad hoc: "verify this review", "drive this manuscript to clean", "check this is submission-ready".

## The success predicate

"Done" is mechanical and declared **once, upfront** (confirmed before any cycles run):

```
REVIEW VERIFIED  ⟺  (every in-scope auto-unit == 0)
                 AND (every in-scope human gate CONFIRMED)
                 AND (ai-disclosure.md emitted and current)
```

It is re-evaluated every cycle and never silently changed mid-run.

## Units remaining

The progress scalar is a **weighted** sum `U = Σ (weightᵢ × unitᵢ)`, recomputed each cycle from real skill outputs. Citation integrity dominates routing (weight 3) because fabricated/unverifiable citations are the headline risk.

| Unit | Weight | From | Counts |
|:-----|:------:|:-----|:-------|
| `U_cite_external` | **3** | `verify-sources` | citations not `VERIFIED` (fabricated / no-resolve / `RETRACTED`) |
| `U_cite_internal` | 1 | `validate-citations` | draft citations with no extraction-matrix match |
| `U_screen` | 1 | `screen-literature` | unresolved dual-reviewer disagreements |
| `U_extract` | 1 | `extract-synthesis` | extraction fields flagged unreconciled |
| `U_prisma` | 1 | `prisma-flow` | arms failing reconciliation (`prisma_flow.py --strict`) |
| `U_consistency` | 1 | `validate-consistency` | `critical_breaks + max(0, 75 − score)` (graded) |
| `U_grade` | 1 | `validate-evidence` | themes/outcomes not yet GRADE-graded |

The **predicate uses raw counts** (every unit must reach 0); the **weights only shape routing and the climb gradient**. Weights/thresholds live in one config block in `scripts/review_units.py`.

### Human gates (tracked separately, never auto-zeroed)

| Gate | From | Counts |
|:-----|:-----|:-------|
| `H_rob` | `appraise-risk-of-bias` | studies without a **human-confirmed** rating |
| `H_screen_adj` | `screen-literature` | conflicts requiring human adjudication |
| `H_cite_manual` | `verify-sources` | citations only resolvable as `UNVERIFIED (manual)` |

## Units in scope (by review type)

The loop runs on **both** registrable/systematic reviews and the lighter narrative path — but in-scope units are **derived from the review type**, because a unit only exists when its upstream artifact does. Omitted units are **absent**, not "zero to achieve."

| Unit | systematic / scoping / rapid / umbrella | narrative / exploratory |
|:-----|:--:|:--:|
| `U_cite_external`, `U_cite_internal`, `U_consistency` | ✅ | ✅ (universal floor) |
| `U_extract` | ✅ | ✅ if an extraction matrix exists |
| `U_grade` | ✅ | only if evidence grading was performed |
| `U_prisma` | ✅ | ⬜ no PRISMA flow |
| `U_screen` | ✅ dual-reviewer | ⬜ no dual-screening κ |
| Human gates | all | `H_cite_manual` only |

**Citation integrity and consistency are universal** — every review, however light, must end with real, faithfully-represented citations. The in-scope set is resolved once at classification and frozen for the run. These three floor units (`U_cite_external`, `U_cite_internal`, `U_consistency`) must be **present** in `units.json` for a `VERIFIED` verdict: `review_units.py` **fails closed** — an empty or citation-less units map lists them under `missing_units` and can never report `VERIFIED`, so a malformed or partial input cannot gate a review complete.

## Procedure

### Step 1 — Classify & scope
Determine the review type (from the manifest if `orchestrate-research` set it; otherwise classify from the draft + available artifacts). Resolve the in-scope unit set per the table above, and pass it to the backend as `units_in_scope` in each cycle's `units.json` — the backend then requires every in-scope unit (not just the universal floor) to be present and 0 before `VERIFIED`, so a run that silently omits an in-scope check (e.g. a systematic review missing `U_prisma`) is caught rather than passed.

### Step 2 — Derive the predicate & confirm once
State the success predicate, the units in scope, and **which human gates will fire**. Get one upfront confirmation. Catching a misclassification at cycle 0 is free; at cycle 15 it is not.

> **`--dry-run`** — when invoked with `--dry-run`, stop here: print the derived review type, the success predicate, the units in scope, the human gates that will fire, and the ceiling (25) — then **execute nothing**. This is the cheap "what will this do before I spend compute?" preview; it runs no checks and writes no state. Drop the flag to run for real.

### Step 3 — Baseline (cycle 0)
Run each in-scope check once. Assemble a `units.json` (see `references/loop-protocol.md` for the schema) and compute the baseline scalar:

```
python scripts/review_units.py units.json
```

Print the banner: predicate, in-scope units, gates that will fire, ceiling (25).

### Step 4 — Loop
Each cycle:
1. Recompute units (re-run only the checks whose inputs changed since last cycle).
2. Read the verdict from `review_units.py`:
   - `VERIFIED` → stop, emit final report + refresh `ai-disclosure.md`.
   - `BLOCKED_ON_HUMAN` → stop; emit the human-handoff report (§ below).
   - `PLATEAU` (3 non-improving cycles) → stop; report the stall.
   - `CEILING` (cycle 25) → stop; this almost always means a methodology problem.
   - `CONTINUE` → route to the repair skill for the `dominant_unit`, run it, fold its report into the manifest, append the cycle to the units history.
   - Non-empty `missing_units` → a universal-floor check has no value this cycle: **run those checks first** (or carry forward their last-known value) before routing — a missing floor unit blocks `VERIFIED`/`BLOCKED_ON_HUMAN`, so clear it before the loop can terminate cleanly.
3. At **cycle 10**, emit the **soft advisory** (a high pass-count usually signals an upstream methodology issue, not a loop that needs more cycles) — then continue.

**Routing (dominant unit → repair skill):**

| Dominant unit | Route to |
|:--|:--|
| `U_cite_external` | `verify-sources` (re-resolve) → draft fix for misrepresented claims |
| `U_cite_internal` | `validate-citations` auto-recovery → `draft-section`/`write-manuscript` |
| `U_prisma` | `prisma-flow` → trace the stage that dropped records upstream |
| `U_consistency` | `validate-consistency` auto-repair suggestions |
| `U_screen` | `screen-literature` re-screen of the disagreement subset |
| `U_grade` | `validate-evidence` for the ungraded themes |

One repair per cycle, highest-leverage first — no blind "fix everything" passes; each cycle stays auditable.

### Step 5 — Human handoff (on `BLOCKED_ON_HUMAN`)
Emit a crisp "here's what needs you" report: the studies awaiting RoB confirmation, the conflicts awaiting adjudication, the citations only resolvable manually — each with the **provisional machine judgment** so the human can confirm or override quickly. Do **not** loop through these and do **not** synthesize a confirmation.

## The anti-gaming floor-guard (non-negotiable)

A loop optimizing a scalar will "cheat" — drop a hard-to-verify citation, exclude a contentious study, delete a theme — to make a unit fall. For a methodology tool that is corruption, not progress.

1. A unit reduction achieved by **removing content** (citation / study / theme / claim) is a **no-op** for units accounting **unless** backed by a logged eligibility/exclusion reason with a provenance stamp.
2. A citation moving to `UNVERIFIED (manual)` is **not** a cleared `U_cite_external` — it moves to the `H_cite_manual` human gate.
3. A regressing change (re-opening a reconciled PRISMA arm, dropping consistency below 75) is **reverted**, never kept.

**The backend makes this detectable, not just declared.** Pass per-cycle `denominators` (citation / study / theme counts) in `units.json`; `review_units.py --manifest` records them and sets a `floor_guard` status on each cycle's record — a denominator that **fell** since the previous cycle is flagged `UNLOGGED (no-op per §5)` unless you also pass `exclusions_logged: true`. Judging legitimacy stays with you, but a content-removal that games a unit to zero is now written into the audit trail instead of relying on honest self-report. See `references/loop-protocol.md` §6.

## State, checkpoints & provenance

Reuse the orchestrator's existing `manifest.json` / `execution-log.json` — do **not** create a parallel state file.

- Append each cycle to `verification_units: [{cycle, state, weighted_total, by_unit, gates, denominators, floor_guard, outcome}]` in the manifest — **written by the backend, not by hand**: pass `--manifest <path>` and `review_units.py` appends the computed record (creating the file/array if absent). This history **is** the audit trail.

  ```
  python scripts/review_units.py units.json --manifest manifest.json
  ```

  Pass the agent's per-cycle annotation in `units.json` as `"outcome": "progressed: …"` (or `no-op` / `failed` / `blocked`); cycle 0 defaults to `"baseline"`.
- Write a checkpoint on every stop state so partial progress is resumable.
- Provenance-stamp each repair cycle's decisions (model, version, prompt, human_override) per `.agent/steering/ai-research-provenance.md` — the loop is a *producer* of those stamps.
- On `VERIFIED`, refresh `ai-disclosure.md` — the verification activity is itself an AI-assisted step PRISMA-trAIce expects disclosed.

## Output

- `verification/verify-review-report.md` — verdict, cycle-by-cycle units history, per-cycle repair log, and (on `BLOCKED_ON_HUMAN`) the human-handoff checklist.
- A one-line summary for a calling skill: `verify-review: cycle N, U=<weighted>, GATE: VERIFIED | BLOCKED_ON_HUMAN | PLATEAU | CEILING`.

## Boundaries

- This skill **orchestrates**; it never re-implements a check or makes a human-gated judgment. It runs the existing skills and accounts the result.
- It cannot drive human-gate units to zero — by design it stops and hands off.
- A `VERIFIED` verdict means "every mechanical defect is cleared and every human gate is confirmed as of this run" — not "the argument is correct."

## Related

- `verify-sources`, `validate-citations`, `validate-consistency`, `prisma-flow`, `validate-evidence` — the checks this loop sequences.
- `appraise-risk-of-bias` — the human gate it hands off to (consumes confirmation, never re-judges).
- `orchestrate-research` — routes here at the validation phase; folds the verdict back into the manifest.
- `validate-manuscript` — the single-pass batch QA that produces this loop's cycle-0 snapshot; `verify-review` drives that snapshot to a verified end-state (it extends the batch QA, it does not skip it).
- `.agent/steering/ai-research-provenance.md` — provenance + disclosure convention.
