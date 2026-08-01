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
| `U_prisma` | 1 | `prisma-flow` | stages failing reconciliation **plus stages nothing could reach** (`prisma_flow.py --strict`). Both terms, because a record naming only two ends fails nothing for want of anything to check, and a unit counting only failures would report it as zero work |
| `U_consistency` | 1 | `validate-consistency` | `critical_breaks + max(0, 75 − score)` (graded) |
| `U_grade` | 1 | `validate-evidence` | results failing `grade_profile.py --strict` — missing domain, illegal upgrade, arithmetic mismatch, unjustified starting level. **Read the `U_grade: N` line the check prints; do not count diagnostics.** One result can raise four, and counting messages books four units of work for one broken result |
| `U_rob_trace` | 1 | `validate-evidence` | studies cited as confirmed-appraisal backing that do not resolve at the named `(study, result)` target (`grade_profile.py --rob`); matching but unconfirmed appraisals are excluded and counted only by `H_rob` |
| `U_checklist` | 1 | `prisma-flow` | PRISMA rows neither located nor justified (`prisma_checklist.py --strict`), over all **42** addressable rows |

> **`U_grade` was redefined.** It previously counted "themes/outcomes not yet GRADE-graded", which
> had no operational definition and so could never fail for the right reason. It is now **defined
> as** the count `grade_profile.py --strict` reports. `H_rob` likewise changed source — from a
> hand-entered assertion to the count `rob_appraisal.py` reports — while keeping its key and
> meaning.

## Derived counts — the `checks` block

Four of the units and one gate are **derived by running the check**, not read from `units.json`.
Name the record each check runs against:

```json
"checks": {
  "prisma_flow":      {"record": "artifacts/counts.json"},
  "prisma_checklist": {"record": "artifacts/checklist.json"},
  "rob_appraisal":    {"record": "artifacts/appraisal.json"},
  "grade_profile":    {"record": "artifacts/certainty.json",
                       "rob_record": "artifacts/appraisal.json"}
}
```

| Entry | Derives |
|:--|:--|
| `prisma_flow` | `U_prisma` |
| `prisma_checklist` | `U_checklist` |
| `grade_profile` | `U_grade`, and `U_rob_trace` **only when `rob_record` is given** |
| `rob_appraisal` | the `H_rob` gate |

What the check reports overrides what the record asserts, and a disagreement is named in
`ignored_inputs` rather than resolved in silence.

**When `units_in_scope` is declared, a unit a check could have derived may not be self-reported**:
it is listed under `underived_units` and the verdict is held at `CONTINUE`. A check that cannot
produce a verdict — exit 2, a crash, a timeout — is an error, never a count of zero.

**`H_rob` is required whenever `U_rob_trace` is in scope.** A gate cannot be named in
`units_in_scope`, so it reads its scope from the unit it moves with — the two are in scope for
exactly the same review types, and both come from the appraisal record. Omitting the
`rob_appraisal` entry lists `H_rob` under `underived_gates` and holds the verdict. Without that
rule a systematic review reached `VERIFIED` with a signature still pending, which is this feature's
own failure mode surviving for the one count no loop may ever auto-zero.

The check name is a key into a fixed table, never a path. The command line is built by the
backend (`--strict --json`, plus `--rob`); nothing in `units.json` reaches it, because whoever can
write that file would otherwise control what runs. Record paths must resolve inside
`--records-root`, which defaults to the directory holding `units.json`.

### ⚠️ What the backend CANNOT verify

Running the checks makes the counts **derived rather than asserted**. It does not make them
unforgeable: a caller can still point `record` at a doctored file. What the loop verifies is that
the checks were run and what they reported — **not that the underlying review is true.**

Four units have **no runnable check here at all** and stay self-reported: `U_cite_external`,
`U_cite_internal`, `U_screen` and `U_extract`. `U_consistency` is derived, but from an object in
`units.json` rather than from a run. For those five, "defined as the count the check reports"
still describes where the number is supposed to come from in the pipeline, not something the
backend enforces — and no scope declaration will catch a hand-written zero.

Do not read a clean verdict as "every count was derived". Read `underived_units` and the list
above.

**A skill directory copied out on its own cannot derive anything.** Principle III keeps every skill
runnable in isolation, and this one honours it by never importing a sibling — but the checks it runs
are sibling *scripts*, and a lone copy has none of them. Point `--skills-root` at the parent of a
directory named `skills` if the tree exists elsewhere. Otherwise a standalone copy has one honest
option: **do not declare `units_in_scope`.** With scope declared and no checks reachable, every
derivable unit is held under `underived_units` and no cycle count will ever clear it.

The **predicate uses raw counts** (every unit must reach 0); the **weights only shape routing and the climb gradient**. Weights/thresholds live in one config block in `scripts/review_units.py`.

### Human gates (tracked separately, never auto-zeroed)

| Gate | From | Counts |
|:-----|:-----|:-------|
| `H_rob` | `appraise-risk-of-bias` | **appraisals** without a human-confirmed rating — identity is `(study, result)`, so a study appraised for two results and confirmed for neither contributes 2. Never deduplicate the producer's count to studies: the gate counts sign-offs still owed |
| `H_screen_adj` | `screen-literature` | conflicts requiring human adjudication |
| `H_cite_manual` | `verify-sources` | citations only resolvable as `UNVERIFIED (manual)` |
| `H_numeric` | `extract-synthesis` | numeric results (effect sizes / sample sizes / CIs) awaiting **human numeric verification** |

## Units in scope (by review type)

The loop runs on **both** registrable/systematic reviews and the lighter narrative path — but in-scope units are **derived from the review type**, because a unit only exists when its upstream artifact does. Omitted units are **absent**, not "zero to achieve."

| Unit | systematic | umbrella | rapid | scoping | narrative |
|:-----|:--:|:--:|:--:|:--:|:--:|
| `U_cite_external`, `U_cite_internal`, `U_consistency` | ✅ | ✅ | ✅ | ✅ | ✅ (universal floor) |
| `U_extract` | ✅ | ✅ | ✅ | ✅ | ✅ if an extraction matrix exists |
| `U_grade` | ✅ | ✅ | ✅ | ⬜ no certainty grading | only if grading was performed |
| `U_rob_trace` | ✅ | ✅ | ⬜ heuristic basis permitted | ⬜ | ⬜ |
| `U_checklist` | ✅ | ✅ | ✅ | ⬜ ScR variant not implemented | ⬜ |
| `U_prisma` | ✅ | ✅ | ✅ | ✅ | ⬜ no PRISMA flow |
| `U_screen` | ✅ dual-reviewer | ✅ | ⬜ single screening permitted | ✅ | ⬜ no dual-screening κ |
| `H_rob` | ✅ | ✅ | ⬜ | ⬜ | ⬜ |
| Other human gates | all | all | `H_cite_manual` | `H_cite_manual` | `H_cite_manual` only |

`U_rob_trace` and `H_rob` are out of scope for **rapid** reviews because the heuristic risk-of-bias
basis is permitted there when the streamlined method is disclosed — a rapid review still grades
certainty, so `U_grade` applies. `U_checklist` is out of scope for **scoping** reviews because the
PRISMA-ScR variant is deliberately unimplemented (see `prisma-flow`); it is absent, not zero.

**Citation integrity and consistency are universal** — every review, however light, must end with real, faithfully-represented citations. The in-scope set is resolved once at classification and frozen for the run. These three floor units (`U_cite_external`, `U_cite_internal`, `U_consistency`) must be **present** in `units.json` for a `VERIFIED` verdict: `review_units.py` **fails closed** — an empty or citation-less units map lists them under `missing_units` and can never report `VERIFIED`, so a malformed or partial input cannot gate a review complete.

## Procedure

### Step 1 — Classify & scope
Determine the review type (from the manifest if `orchestrate-research` set it; otherwise classify from the draft + available artifacts). Resolve the in-scope unit set per the table above, and pass it to the backend as `units_in_scope` in each cycle's `units.json` — the backend then requires every in-scope unit (not just the universal floor) to be present and 0 before `VERIFIED`, so a run that silently omits an in-scope check (e.g. a systematic review missing `U_prisma`) is caught rather than passed.

Declaring scope also commits you to the `checks` block: every in-scope unit a check can derive needs an entry naming its record, or the verdict is held at `CONTINUE` with the unit under `underived_units`. Assemble it in this step, alongside the scope it mirrors.

### Step 2 — Derive the predicate & confirm once
State the success predicate, the units in scope, and **which human gates will fire**. Get one upfront confirmation. Catching a misclassification at cycle 0 is free; at cycle 15 it is not.

> **`--dry-run`** — when invoked with `--dry-run`, stop here: print the derived review type, the success predicate, the units in scope, the human gates that will fire, the checks declared, the units they will derive, the ones that will be left underived, and the ceiling (25) — then **execute nothing**. This is the cheap "what will this do before I spend compute?" preview; it validates the `checks` block in full — unknown names, stray keys, records that do not resolve — but runs no checks and writes no state. Drop the flag to run for real.

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
   - Non-empty `ignored_inputs` → you supplied something the check deliberately did not use, and the remedy is in the message. Two cases: `U_consistency` written into `units` is dropped, because it is derived only from a `consistency` object with a real score — otherwise a hand-written zero would satisfy the floor without one; and a unit or gate a declared check derived, where the record asserted a different number. For the first, read this alongside `missing_units`, which will name the same unit; the two together mean "supplied, but not in a form that counts", not "forgotten".
   - Non-empty `underived_units` or `underived_gates` → a unit or gate in scope that a check could have derived, and no `checks` entry named its record. **Add the entry**; the verdict is held until you do. These are the items in the verdict that no amount of repair work will clear.
   - Non-empty `unattributed_issues` → a check reported work that no unit and no gate counts, so it appears nowhere else. Today this is a risk-of-bias record failing its own instrument: fix the appraisal record. It is the agent's to clear, not a human's.
3. At **cycle 10**, emit the **soft advisory** (a high pass-count usually signals an upstream methodology issue, not a loop that needs more cycles) — then continue.

**Routing (dominant unit → repair skill):**

| Dominant unit | Route to |
|:--|:--|
| `U_cite_external` | `verify-sources` (re-resolve) → draft fix for misrepresented claims |
| `U_cite_internal` | `validate-citations` auto-recovery → `draft-section`/`write-manuscript` |
| `U_prisma` | `prisma-flow` → trace the stage that dropped records upstream |
| `U_consistency` | `validate-consistency` auto-repair suggestions |
| `U_screen` | `screen-literature` re-screen of the disagreement subset |
| `U_extract` | `extract-synthesis` re-reconcile the flagged extraction fields |
| `U_grade` | `validate-evidence` → fix the results `grade_profile.py --strict` reports: a missing domain, an illegal upgrade, arithmetic that does not reconcile, or a starting level inconsistent with the predominant design |
| `U_rob_trace` | `appraise-risk-of-bias` → create the missing appraisal or correct the study/result identifiers the certainty record cites. **Matching but unconfirmed appraisals are excluded from this unit and counted only by the human gate (`H_rob`) — hand off, do not loop.** |
| `U_checklist` | `prisma-flow` → address the reported rows in the manuscript, or record an explicit `not_applicable` justification for each. Remember completeness is over all **42** rows, not the 27 numbered items |

**Every unit in `DEFAULT_WEIGHTS` must appear in this table.** The backend can nominate any
registered unit as `dominant_unit`, and Step 4's `CONTINUE → route to the repair skill` has nothing
to do for a unit with no route — the loop would stall on exactly the failure it just detected.

One repair per cycle, highest-leverage first — no blind "fix everything" passes; each cycle stays auditable.

### Step 5 — Human handoff (on `BLOCKED_ON_HUMAN`)
Emit a crisp "here's what needs you" report: the appraisals awaiting RoB confirmation, the conflicts awaiting adjudication, the citations only resolvable manually — each with the **provisional machine judgment** so the human can confirm or override quickly. Do **not** loop through these and do **not** synthesize a confirmation.

## The anti-gaming floor-guard (non-negotiable)

A loop optimizing a scalar will "cheat" — drop a hard-to-verify citation, exclude a contentious study, delete a theme — to make a unit fall. For a methodology tool that is corruption, not progress.

1. A unit reduction achieved by **removing content** (citation / study / theme / claim) is a **no-op** for units accounting **unless** backed by a logged eligibility/exclusion reason with a provenance stamp.
2. A citation moving to `UNVERIFIED (manual)` is **not** a cleared `U_cite_external` — it moves to the `H_cite_manual` human gate.
3. A regressing change (re-opening a reconciled PRISMA arm, dropping consistency below 75) is **reverted**, never kept.

**The backend makes this detectable *and* blocking, not just declared.** Pass per-cycle `denominators` (citation / study / theme counts) in `units.json`; `review_units.py --manifest` records them and sets a `floor_guard` status on each cycle's record — a denominator that **fell** (or whose key was removed entirely) since the previous cycle is flagged `UNLOGGED (no-op per §5)` unless you also pass `exclusions_logged: true`. An `UNLOGGED` drop **holds a would-be `VERIFIED` as `BLOCKED_ON_HUMAN`** (with a `hold_reason`) so a review whose units were zeroed by *removing* content cannot be gated complete on the exit code — a human must adjudicate whether the removal was a legitimate logged exclusion. See `references/loop-protocol.md` §6.

## State, checkpoints & provenance

Reuse the orchestrator's existing `manifest.json` / `execution-log.json` — do **not** create a parallel state file.

- Append each cycle to `verification_units: [{schema_version, cycle, state, weighted_total, by_unit, gates, denominators, floor_guard, outcome}]` in the manifest — **written by the backend, not by hand**: pass `--manifest <path>` and `review_units.py` appends the computed record (creating the file/array if absent). This history **is** the audit trail.

  `schema_version` is on every record because the units have been redefined once already: a
  `by_unit.U_grade` written before that redefinition and one written after look identical and mean
  different things, so a history without it cannot be read as one series. Records written before
  the field existed are stamped `"unversioned"` on the next append — an explicit "the definitions
  these counts were computed under are unknown", rather than adopting them into the current
  version, which would assert exactly what cannot be checked.

  **The field labels the record; the backend does not act on it.** Its reader is you, or a
  resuming agent, comparing cycles in the audit trail. The one cross-cycle comparison the backend
  makes is the floor guard's, and that reads `denominators`, which the redefinition did not touch —
  so a legacy record remains a valid baseline deliberately, since skipping it would let a
  denominator drop across the version boundary go unflagged. The plateau series the loop routes on
  is `history` in your input `units.json`, a bare array of prior totals the backend can neither
  version nor verify: comparing totals across a redefinition stays your responsibility.

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
