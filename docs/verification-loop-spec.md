# Spec: Units-Driven Verification Loop for `orchestrate-research`

**Status:** Draft for review — no implementation yet
**Date:** 2026-06-20
**Adapted from:** `autoresearch` (uditgoenka/autoresearch) orchestrator pattern — *mechanism only*
**Author note:** This transfers autoresearch's *self-correcting loop with a mechanical success
predicate + plateau/ceiling backstops + checkpointed audit trail*. It deliberately **inverts** one
assumption: where autoresearch loops to *avoid* human intervention, this loop runs to *cleanly hand
off* to the human gates the methodology requires (`appraise-risk-of-bias`, numeric verification,
conflict adjudication).

---

## 1. Problem

`orchestrate-research` v3.0 is a **dispatcher + linear pipeline runner**: each validation stage
(`validate-citations`, `verify-sources`, `validate-consistency`, `prisma-flow`,
`validate-evidence`) runs **once**. But the failure modes the suite exists to catch are exactly the
kind that survive a single pass:

- citations that `verify-sources` flags `UNVERIFIED`/`RETRACTED` (fabrication rates 14–90%)
- screening disagreements above the Cohen's κ floor
- PRISMA arms whose arithmetic does not reconcile
- a `validate-consistency` score below the 75/100 gate
- GRADE domains left ungraded

Today, surfacing these does not automatically drive them to resolution and re-check. A bounded
loop that **re-runs the relevant check until a mechanical "done" predicate holds — or until only a
human can move the number** closes that gap without sacrificing the human gates.

---

## 2. The Success Predicate

"Done" is mechanical and declared **once, upfront** (confirmed by the user before any cycles run):

```
REVIEW VERIFIED  ⟺  (all auto-reducible units == 0)
                 AND (every human gate in scope is CONFIRMED)
                 AND (ai-disclosure.md emitted and current)
```

The predicate is printed in the upfront confirmation and re-evaluated every cycle. It is never
silently changed mid-run.

---

## 3. Units Remaining

A vector of non-negative integers, lower is better, recomputed every cycle from **real artifacts
the existing skills already emit**. The loop's progress scalar is a **weighted** sum
`U = Σ (weightᵢ × unitᵢ)` — fabricated/unverifiable citations dominate routing because they are the
headline integrity risk (decision Q1). Human-gate counts are tracked **separately** (they are not
auto-reducible — see §5).

### 3.1 Auto-reducible units (the loop may drive these to zero)

| Unit | Weight | Source skill | Mechanical signal | Counts |
|------|:------:|--------------|-------------------|--------|
| `U_cite_external` | **3** | `verify-sources` | per-citation status | # citations not `VERIFIED` (i.e. fabricated/no-resolve/`RETRACTED`) |
| `U_cite_internal` | 1 | `validate-citations` | draft-vs-matrix consistency | # draft citations with no matrix match |
| `U_screen` | 1 | `screen-literature` | dual-reviewer disagreement list; `kappa.py --min-kappa` | # unresolved disagreements (κ-below-floor → BLOCKED flag, see §5) |
| `U_extract` | 1 | `extract-synthesis` | dual-extraction reconcile | # extraction fields flagged unreconciled |
| `U_prisma` | 1 | `prisma-flow` | `prisma_flow.py --strict` | # arms that fail reconciliation (0/1/2) |
| `U_consistency` | 1 | `validate-consistency` | graded gap below the 75 gate + critical breaks | `# critical breaks` + `max(0, 75 − score)` (decision Q2) |
| `U_grade` | 1 | `validate-evidence` | GRADE coverage | # themes/outcomes not yet graded |

**Weighting (Q1).** `U_cite_external` carries weight **3**; all others weight **1**. This affects
*routing* (the dominant-unit pick prefers citation integrity) and the *climb gradient* (clearing one
fabricated citation moves the scalar as much as three reconciliation fixes) — it does **not** change
the predicate, which still requires *every* unit at 0. Weights live in one config block so they are
tunable without touching loop logic.

**Graded `U_consistency` (Q2).** Instead of a binary `score < 75 → 1`, the unit is
`# critical breaks + max(0, 75 − score)`. This gives the loop a smooth gradient to climb toward the
gate (a draft at 60 reads as worse than one at 73), rather than a flat 1 until it crosses 75. The
unit still only reaches 0 when the score is ≥ 75 **and** there are no critical breaks — the existing
gate semantics are preserved, just made continuous below the threshold.

A cycle where a unit cannot be computed (script crash, missing input) returns `unknown` for that
unit. Unknowns are **excluded from plateau counting**; repeated unknowns on the same unit route to
`BLOCKED`, not `PLATEAU` (mirrors autoresearch).

### 3.2 Human-gate counts (tracked, never auto-zeroed)

| Gate | Source skill | Signal | Terminal? |
|------|--------------|--------|-----------|
| `H_rob` | `appraise-risk-of-bias` | # studies without **human-confirmed** rating | Yes — hard gate |
| `H_screen_adj` | `screen-literature` | # conflicts requiring human adjudication | Yes |
| `H_cite_manual` | `verify-sources` | # citations only resolvable as `UNVERIFIED (manual)` | Yes — human confirms/removes |

### 3.3 Units-in-scope by review type (Q4 — the loop applies to *both* paths)

The loop runs on **both** the registrable/systematic path and the lighter narrative path — but the
units-in-scope are **derived from the review type**, because some units only exist when the upstream
artifact exists. A narrative review with a bring-your-own corpus has no dual-screening κ, no PRISMA-S
search log, and often no formal GRADE table, so those units are simply **not in scope** and never
block — they are not counted as "0 to be achieved," they are absent.

| Unit | Systematic / scoping / rapid / umbrella | Narrative / exploratory |
|------|:--------------------------------------:|:-----------------------:|
| `U_cite_external` (w3) | ✅ | ✅ |
| `U_cite_internal` | ✅ | ✅ |
| `U_consistency` | ✅ | ✅ |
| `U_extract` | ✅ | ✅ (if an extraction matrix exists) |
| `U_grade` | ✅ | ⬜ only if evidence grading was performed |
| `U_prisma` | ✅ | ⬜ no PRISMA flow on the narrative path |
| `U_screen` | ✅ (dual-reviewer) | ⬜ no dual-screening κ |
| Human gates `H_*` | all in scope | `H_cite_manual` only (no RoB/κ-adjudication) |

The in-scope set is resolved once at classification, printed in the upfront confirmation, and frozen
for the run. **Citation integrity (`U_cite_*`) and consistency are universal** — every path, however
light, must end with real, faithfully-represented citations. That is the floor the loop guarantees
for *any* review.

---

## 4. The Loop

```
classify review type (systematic | scoping | rapid | umbrella | narrative)
  → derive Success predicate + units-in-scope (confirm ONCE)
  → round-0 baseline: run each in-scope check once, compute U_0, screen any shell commands
  → print banner: predicate, units-in-scope, human gates that WILL fire, ceiling
  → LOOP (cycle n):
        compute U_n  (re-run only the checks whose inputs changed since n-1)
        if predicate met                       → STOP: VERIFIED
        if only human-gate units remain         → STOP: BLOCKED_ON_HUMAN  (§5)
        if plateau (U flat/worse k=3 cycles)    → STOP: PLATEAU
        if n == 10                              → emit SOFT ADVISORY (methodology check), continue
        if n ≥ ceiling (25)                     → STOP: CEILING
        else:
          route to the single highest-leverage repair skill for the dominant unit
          run it (its own bounded inner behaviour, unchanged)
          record outcome: progressed | no-op | failed | blocked
          fold its report into manifest + append U_n to units history
  → emit checkpoint + verdict report + refresh ai-disclosure.md
```

### Routing (dominant-unit → repair skill)

| Dominant unit | Route to |
|---------------|----------|
| `U_cite_external` | `verify-sources` (re-resolve), then draft fix for misrepresented claims |
| `U_cite_internal` | `validate-citations` auto-recovery → `write-manuscript`/`draft-section` repair |
| `U_prisma` | `prisma-flow` → trace the dropped-records stage upstream |
| `U_consistency` | `validate-consistency` auto-repair suggestions |
| `U_screen` | `screen-literature` re-screen of the disagreement subset |
| `U_grade` | `validate-evidence` for ungraded themes |

One repair per cycle (highest-leverage first) keeps each cycle auditable — no blind "fix
everything" passes.

### Tunables (review cycles are expensive → tighter than autoresearch's code defaults)

| Param | Default | Rationale |
|-------|---------|-----------|
| `plateau_k` | 3 | autoresearch uses 5 for code; review re-checks are costlier and slower to move — plateau, not the ceiling, is the primary stop |
| `soft_advisory` | 10 | **advisory checkpoint, not a stop** (Q3): at cycle 10 the loop emits a "you've run 10 verification passes — this often indicates a methodology issue upstream, not a loop that needs more cycles; review before continuing" note, then keeps going |
| `ceiling` | 25 | hard backstop (raised from 10 — Q3). 10 was too tight: a legitimately citation-heavy review can need more than 10 passes to clear `U_cite_external` one repair at a time. Plateau-3 still catches genuine stalls long before 25 |
| `--dry-run` | off | print review type, predicate, units-in-scope, gates that will fire, ceiling; execute nothing |
| `--max-cycles N` | 25 | override ceiling |

> **Why keep the "methodology problem" idea but move it off the ceiling (Q3):** the original
> intent — *a high pass-count should surface a methodology problem, not be ground through* — is now
> carried by the **soft advisory at 10** (informs without halting) plus **plateau-3** (halts on real
> stalls). The hard ceiling at 25 only exists to stop a runaway; it should rarely be the reason a run
> ends.

---

## 5. Human gates are terminal — and the anti-gaming floor-guard

This is the critical inversion from autoresearch and the part that protects methodological integrity.

**Human-gate units are never reduced by the loop.** When the only remaining nonzero units are
`H_rob`, `H_screen_adj`, or `H_cite_manual`, the loop stops in `BLOCKED_ON_HUMAN` and emits a crisp
"here's what needs you" report (the studies/conflicts/citations awaiting sign-off, with the
provisional machine judgment for each). It does **not** loop through them and it does **not**
synthesize a human confirmation.

**Floor-guard against metric-gaming.** A loop optimizing a scalar will cheat — e.g. *drop* a
hard-to-verify citation, *exclude* a contentious study, or *delete* a theme to make a unit go down.
For a methodology tool that is corruption, not progress. Rules:

1. A unit reduction achieved by **removing content** (citation, study, theme, claim) counts as a
   **no-op** for units accounting **unless** it is backed by a logged eligibility/exclusion reason
   with a provenance stamp (per `steering/ai-research-provenance.md`).
2. A citation transitioning to `UNVERIFIED (manual)` is **not** "resolved" — it moves to `H_cite_manual`
   (human gate), never counted as a cleared `U_cite_external`.
3. A regressing change (re-opening a previously reconciled PRISMA arm, dropping consistency below
   75) is **reverted**, mirroring autoresearch's keep/revert discipline.

---

## 6. State, checkpoints & provenance (reuse, don't bolt on)

`orchestrate-research` already maintains `manifest.json` + `execution-log.json` and a resume mode.
**Extend those**, do not introduce a parallel `orchestrator-state.json`:

- Add `verification_units: [{cycle, U_total, by_unit:{...}, gates:{...}, outcome}]` to the manifest —
  this history doubles as the **audit trail** the provenance convention wants.
- Write a checkpoint on every STOP (`VERIFIED` | `BLOCKED_ON_HUMAN` | `PLATEAU` | `CEILING`) so partial
  progress is resumable, consistent with the existing resume-from-last-phase behaviour.
- Each repair cycle's decisions are provenance-stamped (model, version, prompt, human_override) per
  `steering/ai-research-provenance.md` — the loop is a *producer* of those stamps, not an exception.
- On `VERIFIED`, refresh `ai-disclosure.md` (the loop's verification activity is itself an
  AI-assisted step that PRISMA-trAIce expects disclosed).

---

## 7. Entry point: the `verify-review` skill (Q5)

The loop ships as a **dedicated skill, `verify-review`** — not a `--verify-loop` flag on
`orchestrate-research`. Rationale:

- **Single responsibility.** `orchestrate-research` *plans and routes the build* of a review;
  `verify-review` *drives it to a verified end-state*. Two different jobs, two skills — consistent
  with how the suite already separates `validate-citations` (internal) from `verify-sources`
  (external) rather than flag-toggling one skill.
- **Composable.** `verify-review` can be invoked standalone on an existing draft ("verify this
  manuscript") without re-entering the full orchestration, and it can be called *by*
  `orchestrate-research` at the verification phase as a normal child-skill hop.
- **Discoverable.** It earns its own row in `SKILLS-REGISTRY.md` with a description an agent can
  match on, instead of being a hidden mode of another skill.

**Integration points:**
- `orchestrate-research` routes to `verify-review` at the end of the validation phase (replacing the
  current single-pass `validate-*` fan-out) and folds its verdict/handoff back into the manifest.
- `verify-review` reads review type from the manifest when present; when invoked standalone it
  classifies from the draft + available artifacts, then resolves units-in-scope per §3.3.
- It consumes the human gates' confirmed outputs; it never re-runs `appraise-risk-of-bias`'s
  judgment, only checks whether confirmation exists (`H_rob`).

The verdicts it can emit are exactly the loop STOP states: `VERIFIED`, `BLOCKED_ON_HUMAN`,
`PLATEAU`, `CEILING`.

---

## 8. Scope & explicit non-goals

**In scope:** the orchestration mechanism above, packaged as the `verify-review` skill and layered
onto the existing skills. No existing skill's internal logic changes; the loop only *sequences and
re-checks* them and accounts the units.

**Non-goals (rejected transfers from autoresearch):**
- The 9 software archetypes (`fix-broken`, `ship-ready`, `harden`…), TDD green-assertion ladder,
  ship gate, STRIDE/OWASP pass — code-domain specific.
- Full autonomy / "wake up to results" — conflicts with the human gates; this loop is explicitly
  *gated*, not unattended.
- A new state file format — reuse `manifest.json`/`execution-log.json`.

---

## 9. Resolved decisions (2026-06-20)

All five open questions are decided; the spec above reflects them.

1. **Unit weighting → weighted.** `U_cite_external` = weight 3, all others 1. Fabricated/unverifiable
   citations dominate routing and the climb gradient. Predicate unchanged (every unit must reach 0). [§3.1]
2. **`U_consistency` → graded gradient.** `# critical breaks + max(0, 75 − score)`, not a binary gate.
   Smooth climb below threshold; same 0-condition as the existing gate. [§3.1]
3. **Ceiling 10 was too tight → raised to 25**, with the "methodology problem" intent re-homed onto a
   **soft advisory at cycle 10** (informs, does not halt) plus **plateau-3** (halts real stalls). [§4 tunables]
4. **Narrative path → both.** The loop applies to systematic *and* narrative reviews, with
   **units-in-scope derived from review type**. Citation integrity + consistency are universal;
   κ/PRISMA/GRADE/RoB units are in scope only when their upstream artifact exists. [§3.3]
5. **Entry point → dedicated `verify-review` skill** (not a flag), invocable standalone or as a child
   hop from `orchestrate-research`'s validation phase. [§7]

## 10. Implementation status

**Built (2026-06-20).** The `verify-review` skill ships at `skills/verify-review/`
(`SKILL.md`, `README.md`, `references/loop-protocol.md`, and the stdlib backend
`scripts/review_units.py` — classification + units-in-scope + weighted scalar + STOP verdicts,
verified across all verdict states). Registered in `SKILLS-REGISTRY.md` and `README.md`.

`orchestrate-research`'s validation phase was updated to run **both** the single-pass `validate-*`
snapshot **and** the `verify-review` loop (new "Phase 5c: Verified End-State Loop"; canonical orders,
related list, and QA gates updated).

The `verification_units` manifest history is **written by the runnable backend**:
`review_units.py --manifest <path>` appends each cycle's computed record (`cycle`, `state`,
`weighted_total`, `by_unit`, `gates`, `outcome`) to `manifest.json`, creating the file/array if
absent and preserving other keys. So the audit trail is an enforced artifact, not a hand-maintained
convention — same spirit as `kappa.py` / `prisma_flow.py` emitting real files.
