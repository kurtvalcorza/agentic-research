---
name: orchestrate-research
description: "Master orchestrator for literature review workflows with intelligent routing and auto-configuration. Use when starting a literature review from a PDF corpus, running a full research synthesis pipeline, or letting the agent auto-select the optimal review workflow."
---








# Orchestrate Research: Master Literature Review Orchestrator

**Version:** 3.0
**Model:** Sonnet
**Created:** 2026-01-17

---

## Purpose

**Master orchestrator** that intelligently routes literature review workflows based on corpus characteristics, user context, and project structure. Eliminates manual tool selection through adaptive decision-making.

**Zero-Configuration Philosophy:**
- User provides corpus path
- Orchestrator detects corpus size, project context, existing work
- Auto-selects optimal workflow: Standard review (review-literature skill) vs Recursive LRA
- Auto-configures output paths (Example Research Institute vs Research vs Standalone)
- Seamlessly integrates validation skills at appropriate phases

---

## Key Innovation: Intelligent Routing

**Problem:** User confusion about which tool to invoke
- "Should I use LRA or Recursive LRA?"
- "Where should outputs be saved?"
- "Do I need to run validation separately?"

**Solution:** Master orchestrator makes all decisions
- Auto-detects corpus size → Routes to Standard review (<50 papers) or Recursive LRA (50+)
- Auto-detects project context → Routes outputs to Example Research Institute/Research/Standalone
- Auto-invokes validation skills at correct phases
- Auto-resumes interrupted workflows

**Result:** User says "review this corpus" → Everything else is automatic

---

## Architecture & Workflow Selection

The orchestrator uses a **Three-Layer Intelligence Stack**:
1. **Context Detection:** Analyzes corpus size, existing work, and project path patterns.
2. **Intelligent Routing:** Selects the optimal workflow (Standard review vs Recursive LRA) and resolves output paths.
3. **Execution & Recovery:** Invokes child skills, manages phase transitions, and handles validation gates.

**Core Decision Tree:**
- **Corpus <= 15 papers:** Standard review (Quick Mode)
- **Corpus <= 50 papers:** Standard review (Full Mode)
- **Corpus > 50 papers:** Recursive Lit Review (Adaptive Batching)
- **Existing Work Detected:** Resume mode from last completed phase.

For detailed logic specs, path resolution rules, and decision matrices, see:
- **[[references/orchestration_logic|Orchestration Logic & Architecture]]**
- **[[references/detailed-guide|Implementation Details & Templates]]**

---

## Phase -2 (Optional Front-Of-Front-End): Review Protocol

> **This is an OPTION at the very front of the pipeline, ahead of everything else — including corpus acquisition.** It applies to **registrable / systematic-style reviews** (systematic, scoping, rapid, umbrella). For the **lighter narrative-review path** (a quick synthesis, a small bring-your-own corpus, an exploratory scan), skip this phase entirely — it remains the quick default and is unchanged.

**Branch decision — is this a registrable/systematic review?**

```
User intent
      ↓
      ├─ Registrable / systematic-style review
      │  (systematic, scoping, rapid, umbrella; intended to be reproducible/publishable)
      │  → PROTOCOL FRONT-END (new OPTION):
      │       design-review-protocol  → choose review TYPE → frame question (PICO/PEO/SPIDER/PCC)
      │                                → write registrable PRISMA-P protocol.md
      │       → THEN route to generate-screening-criteria → acquire-corpus → … as usual
      │
      └─ Narrative / exploratory review (lighter path)
         → skip the protocol phase → proceed straight to acquisition or bring-your-own corpus
```

When this is a registrable/systematic review, the orchestrator routes to **`design-review-protocol` BEFORE `generate-screening-criteria` and `acquire-corpus`**. This is the true front-of-the-front-end: it pre-specifies the review so everything downstream derives from it.

- **`design-review-protocol`** — selects the review TYPE (systematic / scoping / rapid / umbrella / narrative), frames the question with the right structured framework (PICO / PEO / SPIDER / PCC), and writes a registrable, PRISMA-P-aligned `protocol.md` (eligibility, search plan, screening/extraction/RoB/synthesis methods, amendments). Its outputs feed the rest of the pipeline:
  - its **eligibility** feeds `generate-screening-criteria` (which operationalizes it into inclusion/exclusion rules),
  - its **search plan** feeds `acquire-corpus` (which executes it), and
  - its **appraisal plan** feeds `appraise-risk-of-bias` (which instrument applies to which study design).

**Canonical full order (registrable review):** `design-review-protocol → generate-screening-criteria → acquire-corpus → dedupe-records → screen-literature → extract-synthesis → appraise-risk-of-bias → validate-evidence (+ structure-arguments / draft) → validate-* + verify-sources → verify-review (loop to verified end-state) → prisma-flow (reporting)`. The lighter narrative path drops the protocol/RoB stages and uses the acquisition front-end (or a bring-your-own corpus) directly.

See **[[references/detailed-guide|Implementation Details & Templates]]** for the protocol-branch wiring.

---

## Phase -1 (Optional Front-End): Corpus Acquisition

> **This is an OPTION upstream of the existing workflow, not a forced replacement.** The bring-your-own-corpus path is unchanged: if the user already has a folder of PDFs/Markdown in `corpus/candidates/`, the orchestrator skips straight to corpus analysis and screening as before.

**Branch decision — does a corpus already exist?**

```
User provides input
      ↓
      ├─ Corpus path with PDFs/MD already present (corpus/candidates/ non-empty)
      │  → BRING-YOUR-OWN path (existing behavior, unchanged) → corpus analysis → screening
      │
      └─ A research QUESTION but NO corpus yet (empty/absent candidates)
         → ACQUISITION front-end (new OPTION):
              1. acquire-corpus  → search + snowball → corpus/candidates.jsonl + corpus/search-log.md (PRISMA-S)
              2. dedupe-records  → record-level dedup → emits duplicates-removed count
              3. → hand off to the EXISTING screening phase (Phase 1) with the deduped candidates
```

**Acquisition front-end steps (run only when there is no pre-collected corpus):**

1. **`acquire-corpus`** — the search/acquisition front end. Searches bibliographic databases (OpenAlex keyless primary; CrossRef/PubMed/arXiv; scite MCP optional, paid, never assumed) plus backward/forward citation snowballing. Writes a **PRISMA-S** search log (databases, exact queries, dates run, per-source counts, snowball seeds/yield). Outputs: `corpus/candidates.jsonl` + `corpus/search-log.md`.
2. **`dedupe-records`** — record-level dedup run AFTER acquisition and BEFORE screening: DOI-exact + fuzzy-title (year/author guarded) + preprint-vs-published reconciliation. Emits the **duplicates-removed** count that the PRISMA flow needs.
3. **Hand off to screening** — the deduped candidate set feeds the existing Phase 1 screening exactly as a bring-your-own corpus would. Everything downstream (extraction, synthesis, drafting, validation) is unchanged.

**Canonical front-end order:** `acquire-corpus → dedupe-records → screen-literature → (extract / synthesize / draft) → validate-* + verify-sources → verify-review (loop to verified end-state) → prisma-flow (reporting)`. The identification counts (from `acquire-corpus`) and duplicates-removed count (from `dedupe-records`) are carried forward to the reporting phase so `prisma-flow` can build a REAL PRISMA 2020 diagram (see below).

See **[[references/detailed-guide|Implementation Details & Templates]]** for the acquisition-branch wiring and count hand-off.

---

## External Source Verification & AI Provenance

Two layers complete the validation phase. Both are routed automatically and must not be skipped on substantive reviews.

### External-Verification Gate (Phase 5+)

Alongside the existing internal validation skills (`validate-citations`, `validate-consistency`, `validate-evidence`), the orchestrator routes the draft to **`verify-sources`** at the validation phase. The two layers are complementary and BOTH must run:

- **`validate-citations`** — INTERNAL consistency only: checks the draft against the extraction matrix. It cannot tell whether a cited source is real, exists, or has been retracted.
- **`verify-sources`** — EXTERNAL verification: resolves each citation against bibliographic databases (scite MCP preferred, else CrossRef/OpenAlex API), confirms DOI existence and author/year match, checks for retraction/correction/expression-of-concern, and tests claim-vs-source fidelity. It emits `verification/source-verification.md` with a per-citation status (VERIFIED / RETRACTED / UNVERIFIED / FLAGGED / MISMATCH) and a PASS/FAIL gate.

**Gate rule:** A `verify-sources` **FAIL** (any RETRACTED or fabricated/UNVERIFIED citation, or an un-reviewed MISMATCH) **HALTS** the workflow — the review cannot be marked `complete`. PASS requires zero RETRACTED, zero UNVERIFIED, and zero un-reviewed MISMATCH. This gate sits beside the Phase 5 citation-validation gate, the Phase 7 consistency-validation final gate, and the Phase 5c verified-end-state gate (`verify-review` must reach `VERIFIED` — or a logged `BLOCKED_ON_HUMAN` handoff — before a submission-ready review is marked `complete`). If the user overrides the gate to proceed, the override must be logged as a `human_override` provenance event (see below).

### Validation phase: snapshot (`validate-*`) + loop (`verify-review`)

The validation phase runs in **two complementary modes — both are used, neither replaces the other:**

1. **Single-pass snapshot** — the existing `validate-citations` / `verify-sources` / `validate-consistency` / `validate-evidence` checks (batchable via `validate-manuscript`) produce a point-in-time gate result. This is the fast "where does the draft stand right now?" read, and it is what populates the Phase 5/5b/7 gates above.

2. **Verified end-state loop** — the orchestrator then routes to **`verify-review`**, which re-runs those same checks on a **bounded self-correcting loop** against a mechanical *units-remaining* predicate: it repairs the highest-leverage defect (citation integrity weighted ×3), re-checks, and repeats until every in-scope auto-unit is 0 — then **stops and hands off to the human gates** (`appraise-risk-of-bias`, numeric verification, screening adjudication) rather than looping through them. It stops at `VERIFIED`, `BLOCKED_ON_HUMAN`, `PLATEAU`, or `CEILING`.

**How they compose:** the single-pass snapshot establishes the baseline (it *is* `verify-review`'s cycle 0); `verify-review` then drives that baseline to closure. On a quick check the snapshot alone is enough; on a review intended to be *finished* (submission-ready), `verify-review` is what marks it `complete`. `verify-review` appends a `verification_units` history to the run's `manifest.json` (cycle, weighted total, per-unit, gates, outcome) — this doubles as the audit trail. See **[[.agent/skills/verify-review/SKILL|verify-review]]**.

### AI Disclosure & Per-Decision Provenance

- **`ai-disclosure.md` is a required final output artifact** of every completed review, written alongside the phase outputs. It is PRISMA-trAIce (2025) aligned and follows ICMJE/COPE practice — disclose substantive AI assistance, never list AI as an author.
- Every automated **include / exclude, extraction, grade, and verification** decision is **provenance-stamped** (`model` + `model_version` + `prompt_id` + `human_override`) per **`.agent/steering/ai-research-provenance.md`**. Gate overrides (including the `verify-sources` HALT above) are recorded as `human_override` events.
- For non-meta-analytic synthesis, report per the **SWiM** guideline (Synthesis Without Meta-analysis; Campbell et al. 2020, BMJ, via EQUATOR): how studies were grouped, the standardized metric / effect-direction used, the synthesis method, how results are presented, the structured findings summary, and synthesis limitations.

See **[[references/detailed-guide|Implementation Details & Templates]]** for the gate wiring, output list, and provenance stamping specifics.

### PRISMA 2020 Flow Diagram (Reporting Phase)

At the reporting/validation phase, the orchestrator routes to **`prisma-flow`** to emit a **REAL PRISMA 2020 flow diagram** (Mermaid) assembled from the ACTUAL counts produced by this run:

- **Identification** counts (per source) from `acquire-corpus` (`corpus/search-log.md` / `corpus/candidates.jsonl`).
- **Duplicates removed** count from `dedupe-records`.
- **Screening / eligibility / included** counts from the screening phase (`screen-literature`) and the phase-1 screening report.

This **replaces any hollow or hand-made PRISMA artifact** — the diagram is computed from real run data, not drawn by hand.

**Gate rule:** `prisma-flow` **FAILS if the arithmetic does not reconcile** end to end (identified − duplicates − excluded ≠ included). A failure means the counts carried between phases are inconsistent and must be fixed before the review is reported. When the acquisition front-end was NOT used (bring-your-own corpus, so no identification/duplicates counts exist upstream), supply the identification and duplicates-removed counts that `prisma-flow` needs from the corpus's own provenance, or run it in the screening-only mode it supports.

---

## Dual-Reviewer Rigor (Systematic Reviews)

> **OPTION for registrable/systematic reviews, not a forced default.** Single-pass screening and extraction remain the **quick default** for narrative/exploratory work and are unchanged. DUAL mode is the rigorous gold-standard OPTION; turn it on for systematic-style reviews.

Dual **independent** screening, extraction, and appraisal is the systematic-review gold standard. The LLM analogue is **two independent passes** (different model and/or prompt) followed by **conflict adjudication**:

- **Screening (DUAL mode):** run `screen-literature` twice independently, then reconcile. Inter-rater agreement is checked with `screen-literature/scripts/kappa.py` (Cohen's kappa, plus MCC/recall vs a reference set and a disagreement list). A `--min-kappa` gate flags weak agreement so criteria can be tightened and the pass re-run before proceeding. For large screening sets, active-learning prioritization plus a defined stopping rule is good practice.
- **Extraction (DUAL mode):** run `extract-synthesis` twice independently and adjudicate conflicting cells before they enter the synthesis matrix.

Single-pass stays available as the lighter default; DUAL is selected per the protocol (`design-review-protocol`) for reviews that require it.

## Risk-of-Bias Appraisal (Human-Gated, Before Grading)

After extraction and **before** evidence grading (`validate-evidence`), the orchestrator routes a systematic review to **`appraise-risk-of-bias`** — per-study risk-of-bias assessment with the design-appropriate validated instrument (RoB 2 for RCTs, ROBINS-I for non-randomized interventions, Newcastle-Ottawa for observational, QUADAS-2 for diagnostic accuracy).

- **🔒 HUMAN-GATED — by design.** This is the weakest link for LLMs (RoB appraisal accuracy ~0.62). The agent **extracts the signaling-question evidence and proposes a PROVISIONAL rating**; a **human confirms or overrides** every domain judgment and the overall rating before the appraisal is final. An appraisal with unconfirmed machine ratings is **not** complete.
- **Pipeline position:** runs AFTER extraction (`extract-synthesis`) and BEFORE evidence grading. Its **confirmed overall ratings feed the risk-of-bias domain of GRADE** in `validate-evidence`.
- **Provenance:** the human confirmation/override is logged per `.agent/steering/ai-research-provenance.md` (a `human_override`-style provenance event).

The narrative/exploratory path does not require this stage; it is part of the registrable/systematic route.

---

## Related

- **[[.agent/skills/design-review-protocol/SKILL|design-review-protocol]]** — front-of-the-front-end for registrable/systematic reviews: selects the review TYPE, frames the question (PICO/PEO/SPIDER/PCC), and writes a registrable PRISMA-P `protocol.md`. Runs BEFORE `generate-screening-criteria` and `acquire-corpus`; its eligibility/search/appraisal plans feed those skills and `appraise-risk-of-bias`. Skipped on the lighter narrative path.
- **[[.agent/skills/acquire-corpus/SKILL|acquire-corpus]]** — OPTIONAL search/acquisition front end: searches bibliographic databases + citation snowballing, writes a PRISMA-S search log (`corpus/candidates.jsonl` + `corpus/search-log.md`). Use when starting from a question with no corpus yet.
- **[[.agent/skills/dedupe-records/SKILL|dedupe-records]]** — record-level dedup (DOI-exact + fuzzy-title + preprint-vs-published) run after acquisition and before screening; emits the duplicates-removed count for the PRISMA flow.
- **[[.agent/skills/prisma-flow/SKILL|prisma-flow]]** — assembles a REAL PRISMA 2020 flow diagram (Mermaid) from actual identification/duplicates/screening counts; FAILS if the arithmetic does not reconcile. The reporting-phase replacement for any hand-made PRISMA artifact.
- **[[.agent/skills/verify-sources/SKILL|verify-sources]]** — external citation verification (DOI existence, retraction/correction, claim fidelity); the Phase 5+ external gate.
- **[[.agent/skills/validate-citations/SKILL|validate-citations]]** — internal draft-vs-extraction-matrix consistency (complements, does not replace, `verify-sources`).
- **[[.agent/skills/validate-consistency/SKILL|validate-consistency]]** — cross-artifact consistency final gate.
- **[[.agent/skills/verify-review/SKILL|verify-review]]** — drives the validation phase to a verified end-state: a bounded units-remaining loop over the `validate-*`/`verify-sources` checks (citation integrity weighted ×3) that repairs → re-checks → repeats until every mechanical defect is 0, then hands off to the human gates. Used alongside the single-pass checks, not instead of them.
- **[[.agent/skills/appraise-risk-of-bias/SKILL|appraise-risk-of-bias]]** — per-study risk-of-bias appraisal with the design-appropriate instrument (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2). HUMAN-GATED: the agent proposes a provisional rating, a human confirms/overrides. Runs AFTER extraction and BEFORE `validate-evidence`; its confirmed ratings feed the GRADE risk-of-bias domain.
- **[[.agent/skills/validate-evidence/SKILL|validate-evidence]]** — GRADE / Oxford-CEBM evidence grading. Consumes the confirmed risk-of-bias ratings from `appraise-risk-of-bias` for its risk-of-bias domain.
- **[[.agent/steering/ai-research-provenance|ai-research-provenance]]** — per-decision provenance stamping + mandatory `ai-disclosure.md` artifact.

---



## References & Details

Full details, examples, and templates have been moved to [Details](references/detailed-guide.md).
