---
name: synthesize-research
description: "Orchestrate a Deep Research Synthesis workflow. Use when you need to coordinate screening, extraction, drafting, and validation of research into a publication-ready manuscript."
---








# Orchestrator: Synthesize Research

## Core Mission
You manage the end-to-end process of turning raw research files into a publication-ready manuscript. You coordinate specialists for screening, extraction, drafting, and validation.

## Specialists

**Optional protocol front-end (Phase −1 — only for registrable / publishable reviews):**
- **[[../design-review-protocol/SKILL|Review Protocol Designer]]** - The true front-of-the-front-end. Before any criteria or search: selects the review TYPE (systematic / scoping / rapid / umbrella / narrative), frames the question with the right structured framework (PICO / PEO / SPIDER / PCC), and produces a registrable, PRISMA-P-aligned `protocol.md` (pre-specified eligibility, search plan, screening/extraction/RoB/synthesis methods, amendments). Its eligibility feeds Phase 1 screening, its search plan feeds Phase 0 acquisition, and its appraisal plan feeds the risk-of-bias step. Output: `protocol.md` ready for PROSPERO / OSF / protocols.io registration.

**Optional acquisition front-end (Phase 0 — only when starting from a question without a corpus):**
- **[[../acquire-corpus/SKILL|Corpus Acquirer]]** - Searches bibliographic databases (OpenAlex keyless primary; CrossRef/PubMed/arXiv; scite MCP optional) + backward/forward citation snowballing, and writes a PRISMA-S search log. Output: `corpus/candidates.jsonl` + `corpus/search-log.md`.
- **[[../dedupe-records/SKILL|Record Deduplicator]]** - Record-level dedup (DOI-exact + fuzzy-title + preprint↔published reconciliation) of the acquired candidates, run before screening. Emits the duplicates-removed count for the PRISMA flow.

**Core pipeline:**
1. **[[../screen-literature/SKILL|Literature Screener]]** - Filters the corpus. Single-pass is the quick default; **supports DUAL mode** (two independent passes + conflict adjudication, with Cohen's kappa via `screen-literature/scripts/kappa.py`) for rigor.
2. **[[../extract-synthesis/SKILL|Extractor & Synthesizer]]** - Extracts data and identifies themes. Single-pass is the quick default; **supports DUAL mode** (two independent extraction passes + reconciliation, kappa-checked) for rigor.
3. **[[../appraise-risk-of-bias/SKILL|Risk-of-Bias Appraiser]]** - Per-study risk-of-bias appraisal with the design-appropriate instrument (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2). **HUMAN-GATED**: the agent extracts signaling-question evidence and proposes a PROVISIONAL rating; a human confirms/overrides before it is final. Runs after extraction, before grading; its confirmed overall ratings feed the risk-of-bias domain of GRADE (`validate-evidence`).
4. **[[../draft-section/SKILL|Drafter]]** - Writes the manuscript sections.
5. **[[../validate-citations/SKILL|Citation Validator]]** - Ensures internal draft↔matrix integrity.
6. **[[../verify-sources/SKILL|Source Verifier]]** - External citation verification (DOI existence, retraction/correction/concern, claim-vs-source fidelity).
7. **[[../verify-review/SKILL|Verified End-State Loop]]** - *Optional.* After the Phase 4 validation snapshot, drives the review to a *verified end-state*: re-runs the same checks on a bounded units-remaining loop, repairing one defect at a time until every in-scope defect is 0, then hands off to the human gates (`VERIFIED` / `BLOCKED_ON_HUMAN`). Use for a submission-ready synthesis; the single-pass snapshot alone is enough for a quick draft.

**Reporting:**
8. **[[../prisma-flow/SKILL|PRISMA Flow Assembler]]** - Builds the real PRISMA 2020 flow diagram from actual identification (acquire-corpus), duplicates-removed (dedupe-records), and screening/eligibility (screen-literature) counts; fails if the arithmetic does not reconcile.

## Synthesis Method Declaration

This pipeline produces a **NARRATIVE / thematic synthesis** — it groups studies and summarizes evidence directionally; it does **not** perform meta-analysis. Quantitative pooling (effect-size aggregation, forest plots, heterogeneity statistics) is **out of scope**: if statistical pooling is needed, a human should use a dedicated meta-analysis tool, not this orchestrator.

Report the synthesis per **SWiM** ("Synthesis Without Meta-analysis", Campbell et al. 2020, BMJ, via EQUATOR) — the synthesis writeup (`phase2-synthesis.md` / Methods of the draft) should state these six SWiM elements:
1. **Grouping** — how studies were grouped for synthesis.
2. **Standardized metric** — the standardized metric / effect-direction used to compare them.
3. **Synthesis method** — the synthesis method applied (e.g. vote-counting by direction, thematic grouping).
4. **Presentation** — how results are presented (tables, narrative, structured summary).
5. **Structured findings summary** — a structured summary of findings across studies.
6. **Synthesis limitations** — limitations specific to the synthesis (heterogeneity not statistically combined, etc.).

## Workflow

### Initialization
1.  **Check Context**: Determine the starting point.
    - If `corpus/` already exists (bring-your-own-corpus) → proceed straight to **Phase 1: Screening**. This is the default, unchanged path.
    - If there is **no corpus** and you are starting from a research question → run the optional **Phase 0: Acquisition** below to build one first.
2.  **Create Workspace**: Establish the dated synthesis workspace at `.agent/outputs/synthesis-YYYY-MM-DD/`. All phase outputs, state, and the dashboard live here. (`WS/` below refers to this workspace path.)
3.  **Load State**: Read `WS/execution-log.json` (create if missing).
4.  **Update Dashboard**: Write/Update `WS/dashboard.md`.

### Phase −1: Protocol Design (OPTIONAL — only for registrable / publishable reviews)
Skip this phase entirely for ad-hoc syntheses; single-pass quick synthesis remains the default. Run it when the review is meant to be reproducible, registrable, or publishable.

- **Specialist**: `design-review-protocol`
- **Goal**: Pre-specify the review *before* searching — select the review TYPE (systematic / scoping / rapid / umbrella / narrative), frame the question (PICO / PEO / SPIDER / PCC), and write a registrable, PRISMA-P-aligned `protocol.md` (eligibility, search plan, screening/extraction/RoB/synthesis methods, amendments).
- **Hand-off**: The protocol's **eligibility** feeds Phase 1 screening (and `generate-screening-criteria` if used), its **search plan** feeds Phase 0 acquisition (`acquire-corpus`), and its **appraisal plan** feeds the risk-of-bias step (between Phase 2 and Phase 3).
- **Output**: `protocol.md` (ready for PROSPERO / OSF / protocols.io registration).
- **Provenance**: Stamp protocol design as an AI-assisted step in `WS/execution-log.json` per `.agent/steering/ai-research-provenance.md`.

### Phase 0: Acquisition (OPTIONAL — only when starting from a question without a corpus)
Skip this phase entirely if you already have a `corpus/` (bring-your-own-PDFs still works exactly as before). Run it only when the user starts from a research question and has no collected papers yet.

- **Specialists**: `acquire-corpus` then `dedupe-records` (in that order).
- **Step 0a — Acquire**: Run `acquire-corpus` to search bibliographic databases (OpenAlex keyless primary; add CrossRef/PubMed/arXiv as the topic warrants; scite MCP optional) and snowball from seed papers. Produces `corpus/candidates.jsonl` (merged candidate set) and `corpus/search-log.md` (PRISMA-S search documentation: databases, exact queries, dates run, per-source counts, snowball seeds/yield).
- **Step 0b — Dedupe**: Run `dedupe-records` on `corpus/candidates.jsonl` → `corpus/deduped.jsonl` + `corpus/dedup-report.md`. This applies DOI-exact + fuzzy-title (year/author-guarded) + preprint↔published reconciliation and emits the **duplicates-removed count** required by the PRISMA flow. **Do not dedupe inside acquire-corpus** — keeping dedup a separate, auditable step is what makes the PRISMA numbers defensible.
- **Hand-off**: The deduped set (`corpus/deduped.jsonl`, with retrievable records) becomes the `corpus/` input to **Phase 1: Screening**. Carry the identification (per-source + snowball) and duplicates-removed counts forward — `prisma-flow` (Phase 6) consumes them.
- **Adaptive Check**: If `corpus/candidates.jsonl` / `corpus/deduped.jsonl` already exist → Skip acquisition and reuse them.
- **Provenance**: Stamp the search + dedup as AI-assisted steps in `WS/execution-log.json` per `.agent/steering/ai-research-provenance.md`.

### Phase 1: Screening
- **Specialist**: `screen-literature`
- **Goal**: Filter `corpus/` into `WS/phase1-report.md`.
- **Mode**: Single-pass is the quick default. For rigor, run **DUAL mode** — two independent screening passes (different model/prompt) followed by conflict adjudication. Inter-rater agreement is computed with `screen-literature/scripts/kappa.py` (Cohen's kappa + MCC/recall vs an adjudicated reference + a disagreement list); `--min-kappa` can gate the run below an agreement floor. Dual independent screening is the gold standard; the LLM analogue is two independent passes plus adjudication. (Active-learning prioritization + a defined stopping rule are good practice for large screening sets.)
- **Adaptive Check**: If `phase1-report.md` exists -> Skip?
- **Checkpoint**: User must approve the screening list.

### Phase 2: Extraction & Synthesis
- **Specialist**: `extract-synthesis`
- **Goal**: Create `WS/phase2-matrix.md` (structured extraction table) and `WS/phase2-synthesis.md` (thematic analysis).
- **Mode**: Single-pass is the quick default. For rigor, run **DUAL mode** — two independent extraction passes (different model/prompt) followed by reconciliation of disagreements; agreement can be kappa-checked the same way as screening. Dual independent extraction is the gold standard; the LLM analogue is two independent passes plus conflict adjudication.
- **Adaptive Check**: If matrix exists and has >80% coverage -> Skip?

### Phase 2b: Risk-of-Bias Appraisal (HUMAN-GATED — for systematic reviews / GRADE)
Run this between extraction and drafting whenever the synthesis will grade certainty of evidence (GRADE). Skip for ad-hoc syntheses that do not grade evidence.

- **Specialist**: `appraise-risk-of-bias`
- **Goal**: Appraise each included study's risk of bias with the **design-appropriate validated instrument** (RoB 2 for RCTs, ROBINS-I for non-randomized interventions, Newcastle-Ottawa for observational, QUADAS-2 for diagnostic accuracy).
- **HUMAN-GATED — by design**: RoB appraisal is the weakest link for LLMs (reported accuracy ~0.62). The agent **extracts the signaling-question evidence** and **proposes a PROVISIONAL rating** with reasoning; a **human confirms or overrides** every domain judgment and the overall rating before it is final. An appraisal with unconfirmed machine ratings is **not** complete.
- **Hand-off**: The confirmed overall ratings feed the **risk-of-bias domain of GRADE** in `validate-evidence`.
- **Provenance**: Log the human confirmation/override per `.agent/steering/ai-research-provenance.md`.

### Phase 3: Drafting
- **Specialist**: `draft-section`
- **Goal**: Create `WS/phase3-draft.md`.
- **Process**: Iteratively draft Introduction, Methods, Results, Discussion.

### Phase 4: Validation (Quality Gate)
This phase has **two gates** that are different layers — run both; a run is not "complete" until both PASS.

#### 4a. Internal consistency gate
- **Specialist**: `validate-citations`
- **Goal**: Pass with ZERO fabricated citations (every draft citation traces to the extraction matrix).
- **Action**: If fail -> Trigger Auto-Fix -> If still fail -> HALT and ask user.
- **Scope note**: `validate-citations` only checks **internal** draft-vs-extraction-matrix consistency. It cannot tell whether a source is real, retracted, or faithfully represented — that is gate 4b.

#### 4b. External source-verification gate
- **Specialist**: `verify-sources`
- **Goal**: External citation verification of `phase3-draft.md` — resolve each citation against bibliographic databases (scite MCP preferred, else CrossRef / OpenAlex), confirm DOI existence + author/year match, check retraction/correction/concern, and check claim-vs-source fidelity.
- **Output**: `verification/source-verification.md` with per-citation status (VERIFIED / RETRACTED / UNVERIFIED / FLAGGED / MISMATCH) and a PASS/FAIL gate.
- **Gate**: PASS requires **zero RETRACTED, zero UNVERIFIED, and zero un-reviewed MISMATCH**.
- **Completion rule**: A **verify-sources FAIL blocks completion.** The synthesis run is not "complete" until verify-sources PASSES on the draft, in addition to validate-citations. Present failures grouped by severity (retracted/fabricated first); do not soften.
- **Verified end-state (optional)**: for a submission-ready synthesis, route the passing snapshot to **`verify-review`** — it treats this Phase 4 snapshot as its cycle 0 and drives the review to a verified end-state (`VERIFIED`, or `BLOCKED_ON_HUMAN` when only human gates remain), rather than stopping at a single point-in-time pass. On a quick draft the snapshot alone is enough.
- **Override**: The gate is reportable but **not silently overridable**. If the user chooses to proceed past a FAIL, log it as a `human_override` provenance event per `.agent/steering/ai-research-provenance.md`.

### Phase 5: AI Provenance & Disclosure
- **Reference**: `.agent/steering/ai-research-provenance.md`
- **Provenance stamping**: Each phase's automated decisions (include/exclude, extraction, grade, citation verification) are **provenance-stamped** in `WS/execution-log.json` with `model`, `model_version`, and `prompt_id` (plus `human_override` on any override) so any questionable decision is attributable and reproducible.
- **Disclosure artifact**: Emit `WS/ai-disclosure.md` (PRISMA-trAIce aligned) summarizing which stages used AI, the model + version, and the human role — so the author can paste it into a methods/acknowledgements section. ICMJE/COPE: substantive AI assistance must be disclosed; AI is never listed as an author. This artifact is **mandatory** for any output intended for submission or external sharing.

### Phase 6: PRISMA Flow (Reporting)
- **Specialist**: `prisma-flow`
- **Goal**: Assemble the **real** PRISMA 2020 flow diagram from the actual counts produced by this run — identification (from Phase 0 `acquire-corpus`, if run), duplicates removed (from Phase 0 `dedupe-records`, if run), and records screened / excluded with reasons / included (from Phase 1 `screen-literature`).
- **Process**: Collect the counts into a `counts.json` and run `prisma-flow` (`scripts/prisma_flow.py counts.json --strict`). The skill renders a Mermaid PRISMA 2020 flowchart and runs a reconciliation check; it **FAILS if the arithmetic does not reconcile**.
- **Output**: `WS/prisma-flow.md` — the Mermaid flow diagram + the reconciliation result (✅/⚠️), with full-text exclusions tabulated **with reasons**.
- **No-acquisition note**: If Phase 0 was skipped (bring-your-own-corpus), there is no documented database-identification count or duplicates-removed count to report. Use the corpus size as the records-screened starting point and note in `prisma-flow.md` that identification was a pre-collected corpus (not a documented database search). Do **not** invent identification or duplicate numbers — `prisma-flow` only consumes real counts.
- **Provenance**: This is a reporting step over real run data; the counts come from the upstream stages that own them, never fabricated.

## Dashboard Template
```markdown
# Research Synthesis Dashboard

| Phase | Status | Output | Notes |
|-------|--------|--------|-------|
| −1. Protocol (optional) | ⚪ | [Protocol](protocol.md) | design-review-protocol; only for registrable / publishable reviews |
| 0. Acquisition (optional) | ⚪ | [Candidates](../../../corpus/candidates.jsonl) · [Search log](../../../corpus/search-log.md) · [Dedup](../../../corpus/dedup-report.md) | acquire-corpus → dedupe-records; only when starting from a question without a corpus |
| 1. Screening | ⚪ | [Report](phase1-report.md) | single-pass default; DUAL mode + kappa for rigor |
| 2. Extraction | ⚪ | [Matrix](phase2-matrix.md) · [Synthesis](phase2-synthesis.md) | single-pass default; DUAL mode + kappa for rigor |
| 2b. Risk of bias (optional) | ⚪ | [RoB appraisal](phase2b-risk-of-bias.md) | appraise-risk-of-bias — HUMAN-GATED; feeds GRADE |
| 3. Drafting | ⚪ | [Draft](phase3-draft.md) | |
| 4a. Validation (internal) | ⚪ | [Validation](phase4-validation.md) | validate-citations |
| 4b. Source verification (external) | ⚪ | [Verification](verification/source-verification.md) | verify-sources — GATE: blocks completion |
| 4c. Verified end-state (optional) | ⚪ | [Verify-review](verification/verify-review-report.md) | verify-review — loops the snapshot to VERIFIED / BLOCKED_ON_HUMAN; for submission-ready |
| 5. AI disclosure | ⚪ | [Disclosure](ai-disclosure.md) | provenance + PRISMA-trAIce |
| 6. PRISMA flow (reporting) | ⚪ | [Flow](prisma-flow.md) | prisma-flow — fails if counts do not reconcile |
```

## Error Handling
- **Missing Corpus**: Prompt user to create it.
- **Validation Failure (internal)**: "CRITICAL FAILURE: Citations do not match corpus. Please review [Validation Report]."
- **Source-Verification Failure (external)**: "GATE FAIL: verify-sources found retracted / unverified / mismatched citations. Run is NOT complete. Review [verification/source-verification.md] — retracted and fabricated citations first." Do not mark the synthesis complete until verify-sources PASSES.

## Related
- `design-review-protocol` — optional protocol front-end (Phase −1): selects review type, frames the question (PICO/PEO/SPIDER/PCC), and writes a registrable PRISMA-P `protocol.md`; run before criteria/search for registrable reviews. Its eligibility/search/appraisal plans feed downstream phases.
- `appraise-risk-of-bias` — per-study risk-of-bias appraisal (Phase 2b, between extraction and drafting) with the design-appropriate instrument (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2); HUMAN-GATED; confirmed ratings feed the GRADE risk-of-bias domain in `validate-evidence`.
- `acquire-corpus` — optional acquisition front-end (Phase 0): database search + snowballing + PRISMA-S search log; run when starting from a question without a corpus.
- `dedupe-records` — record-level dedup (Phase 0b) after acquisition, before screening; emits the duplicates-removed count for the PRISMA flow.
- `prisma-flow` — reporting step (Phase 6): assembles the real PRISMA 2020 flow from identification + duplicates-removed + screening counts; fails if the arithmetic does not reconcile.
- `verify-sources` — external citation verification gate (4b); blocks completion on FAIL.
- `validate-citations` — internal draft↔matrix consistency gate (4a); complementary to verify-sources (run both).
- `verify-review` — optional verified-end-state loop (4c) after the Phase 4 snapshot; drives the review to `VERIFIED`/`BLOCKED_ON_HUMAN` for a submission-ready synthesis (the snapshot is its cycle 0).
- `.agent/steering/ai-research-provenance.md` — per-decision provenance stamping + the mandatory `ai-disclosure.md` artifact (PRISMA-trAIce / ICMJE / COPE).

## Internal Metadata
- **capabilities**: [file-read, file-write, command-exec, file-search]
- **domain**: research
- **status**: active
- **version**: 2.0
- **type**: orchestrator