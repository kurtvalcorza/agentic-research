# Extract Synthesis

Specialist agent for extracting structured data from research papers and synthesizing cross-cutting themes.

## What This Does

Reads screened research papers, extracts structured evidence into a matrix, and synthesizes thematic insights. Works as Phase 2 specialist in the `synthesize-research` workflow.

## When to Use

Typically invoked automatically by `synthesize-research`, but can be used standalone when:

- You have a screened corpus and need structured extraction
- You want to build an evidence matrix for analysis
- You need thematic synthesis across multiple papers
- You're regenerating Phase 2 outputs after criteria changes

## What You Need

**Required Inputs**:
- **corpus/**: Directory with research papers
- **phase1-report.md**: Screening report identifying papers to include

**Optional**:
- Custom extraction fields (defaults to standard academic fields)

## What You Get

Two complementary outputs:

- **phase2-matrix.md**: Structured extraction table
  - Study metadata (Author, Year, Title)
  - Research design and methods
  - Key findings
  - Limitations
  - **Citations** in standardized format

- **phase2-synthesis.md**: Thematic synthesis
  - Cross-cutting themes across studies
  - Patterns and trends
  - Gaps and contradictions
  - Evidence strength assessment

## How It Works

1. Reads `phase1-report.md` to identify included papers
2. Extracts structured data from each paper
3. Builds extraction matrix with standardized citations
4. Identifies themes across all papers
5. Synthesizes findings into coherent narrative

## Dual Extraction & Reconciliation (recommended)

Single-pass extraction is the **default for quick work**. For rigorous reviews — especially those feeding a meta-analysis — run **dual independent extraction**, the gold-standard analogue:

1. **Second independent pass** — re-extract the included papers in a fresh pass (ideally a different model and/or prompt) into a separate matrix, without seeing the first pass's output.
2. **Diff the two matrices** — compare row-by-row, field-by-field, and flag every discrepancy.
3. **Reconcile** — adjudicate each conflict against the source and carry reconciled values into the canonical matrix.
4. **Human verification of numeric fields (required)** — before any numeric field enters synthesis or meta-analysis, a human must verify **effect sizes, sample sizes (n), and confidence intervals (CIs)** against the source. Single-extractor numeric errors change pooled estimates, so this gate is non-negotiable for quantitative synthesis.

After extraction, the included studies go to `appraise-risk-of-bias` (per-study risk-of-bias appraisal) before evidence grading.

## Key Features

- **Adaptive Check**: Skips if `phase2-matrix.md` and `phase2-synthesis.md` already exist and are complete
- **Citation Generation**: Creates standardized citations for downstream use
- **Thematic Analysis**: Identifies patterns beyond individual paper summaries
- **Structured Format**: Markdown tables for easy manipulation and reference
- **State Awareness**: Detects and validates existing outputs before regenerating

## Matrix Structure

The extraction matrix uses markdown table format with columns for:
- Study ID (Author, Year)
- Research Question/Objective
- Methods/Design
- Key Findings
- Limitations
- Citation

## Synthesis Format

The thematic synthesis organizes findings into:
- Major themes with supporting evidence
- Contradictions or gaps in literature
- Methodological considerations
- Implications for research questions

## Reporting: SWiM

This skill produces **narrative / thematic synthesis, not a meta-analysis** — it does not compute pooled effect estimates. For non-meta-analytic synthesis, the output follows the **SWiM (Synthesis Without Meta-analysis)** reporting guideline (Campbell et al., 2020, *BMJ*; via the EQUATOR Network). The synthesis note (`phase2-synthesis.md`) includes a short **"Synthesis methods (SWiM)"** header capturing:

- **Grouping rationale** — how studies were grouped and why
- **Standardized metric / effect-direction** — the metric or effect-direction convention used to compare findings
- **Synthesis method** — how findings were combined (e.g., thematic grouping, vote-counting by direction of effect)
- **Presentation method** — how results are presented (grouped tables, theme narratives, effect-direction plots)
- **Structured findings summary** — a structured summary per group/theme
- **Synthesis limitations** — limitations of the synthesis itself (heterogeneity, vote-counting weaknesses, risk of bias across the evidence base)

Final drafts built on this synthesis must pass `verify-sources` (external citation verification) before they are trusted or submitted.

## Related

- **`appraise-risk-of-bias`** — per-study risk-of-bias appraisal that runs after extraction and before evidence grading.
