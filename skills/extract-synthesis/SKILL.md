---
name: extract-synthesis
description: "Extract structured data from screened papers and synthesize cross-cutting themes. Use when building an extraction matrix from included papers, synthesizing themes across studies, or running Phase 2 of a literature review."
---








# Specialist: Extractor & Synthesizer

## Purpose
Extract structured data from included papers and synthesize cross-cutting themes.

## Inputs
- `outputs/phase1-report.md` (List of included papers)
- `corpus/`

## Outputs
- `outputs/phase2-matrix.md` (Extraction Matrix)
- `outputs/phase2-synthesis.md` (Thematic Synthesis)

## Workflow

### 1. Verification & Adaptive Check
- Check if `outputs/phase1-report.md` exists.
- **Adaptive Check**: If `phase2-matrix.md` exists and has entries for all included papers -> **SKIP Extraction**.

### 2. Extraction Loop
For each paper in `Included List`:
1.  **Read File**.
2.  **Extract**: Method, Findings, Limitations.
    - **Auto-Fix**: If "Method" section missing, search for "Approach" or "Study Design".
3.  **Save Row**: Append to `phase2-matrix.md`.

### Dual extraction & reconciliation (recommended)
> Single-pass extraction (Step 2 above) remains the **default for quick work**. For rigorous reviews — especially any that feed a meta-analysis — run **dual independent extraction**, the gold-standard analogue: two independent passes plus conflict adjudication.

1.  **Second independent pass**: Re-extract the same `Included List` in a fresh pass — ideally a different model and/or a different prompt — to a separate matrix (e.g., `phase2-matrix-passB.md`). Do not let the second pass see the first pass's output.
2.  **Diff the matrices**: Compare the two extraction matrices row-by-row, field-by-field. Flag every discrepancy (mismatched values, missing fields, divergent interpretations).
3.  **Reconcile discrepancies**: Adjudicate each flagged conflict — re-read the source passage, decide the correct value, and record the resolution. Carry reconciled values into the canonical `phase2-matrix.md`.
4.  **Human verification of numeric fields (REQUIRED)**: Before any numeric field enters synthesis or meta-analysis, a human MUST verify the **effect sizes, sample sizes (n), and confidence intervals (CIs)** against the source. Single-extractor numeric errors change pooled estimates — this gate is non-negotiable for quantitative synthesis. Mark each numeric field as `verified` only after human confirmation.

### 3. Synthesis Phase
1.  **Analyze Matrix**: Look for patterns.
2.  **Identify Themes**: Group findings by topic.
3.  **Write Synthesis**: Create `phase2-synthesis.md`.

> **Handoff**: After extraction, the included studies go to `appraise-risk-of-bias` (per-study risk-of-bias appraisal) before evidence grading.

### Reporting: SWiM
This skill produces **narrative / thematic synthesis, not a meta-analysis** — no pooled effect estimates are computed. Because it is non-meta-analytic, the synthesis output should follow the **SWiM (Synthesis Without Meta-analysis)** reporting guideline (Campbell et al., 2020, *BMJ*; via EQUATOR Network). Include a short **"Synthesis methods (SWiM)"** header near the top of `phase2-synthesis.md` that captures these elements:

- **Grouping rationale** — how studies were grouped (e.g., by theme, population, intervention, or design) and why.
- **Standardized metric / effect-direction** — the standardized metric or effect-direction convention used to compare findings across studies.
- **Synthesis method** — the method used to combine findings (e.g., thematic grouping, vote-counting by direction of effect, narrative synthesis).
- **Presentation method** — how results are presented (e.g., grouped tables, theme narratives, harvest/effect-direction plot).
- **Structured findings summary** — a structured summary of findings per group/theme.
- **Synthesis limitations** — limitations of the synthesis itself (heterogeneity, vote-counting weaknesses, risk of bias across the body of evidence).

> Final drafts built on this synthesis must pass `verify-sources` (external citation verification) before they are trusted or submitted.

## Related
- `appraise-risk-of-bias` — per-study risk-of-bias appraisal; runs after extraction, before evidence grading.

## Error Handling
- **Extraction Fail**: Mark row as "FAILED" in matrix, continue to next.


## Internal Metadata
- **capabilities**: [file-read, file-write, command-exec, file-search]
- **domain**: research
- **status**: active
- **version**: 2.0
- **type**: specialist