# Screen Literature

Specialist agent for screening research papers against inclusion criteria with automatic metadata recovery.

## What This Does

Evaluates research papers in a corpus against defined screening criteria, producing Include/Exclude/Uncertain decisions. Works as Phase 1 specialist in the `synthesize-research` workflow.

## When to Use

Typically invoked automatically by `synthesize-research`, but can be used standalone when:

- You need to screen papers for a literature review
- You want to validate a corpus against specific criteria
- You're building a reference library with quality filters
- You need to recover from interrupted screening sessions

## What You Need

**Required Inputs**:
- **corpus/**: Directory containing research papers (PDF, markdown, or text files)
- **screening-criteria.md**: Inclusion/exclusion criteria for screening

> **Where the corpus comes from.** Bring-your-own-PDFs still works exactly as before. In the **full review pipeline**, the corpus should instead come from `acquire-corpus` → `dedupe-records`: `acquire-corpus` runs a documented PRISMA-S search (real identification counts), and `dedupe-records` removes duplicates and reports a real duplicates-removed count (`corpus/deduped.jsonl`). Screening from that deduped set is what makes the upstream PRISMA numbers real rather than placeholders.

## What You Get

- **phase1-report.md**: Screening report with decisions for each paper
  - Include: Meets all criteria
  - Exclude: Fails one or more criteria
  - Uncertain: Needs manual review

## How It Works

1. Scans `corpus/` directory for research papers
2. Reads `screening-criteria.md`
3. Evaluates each paper against criteria
4. Produces screening decisions with justifications
5. Saves state for resume capability

## Key Features

- **Auto-Fix Metadata**: Recovers missing author/year information from paper content
- **State Recovery**: Resume interrupted screening sessions
- **Justifications**: Explains Include/Exclude/Uncertain decisions
- **Multi-Format Support**: Handles PDF, markdown, and text files
- **Criteria Transparency**: Clear mapping of decisions to specific criteria

## Decision Logic

- **Include**: Paper meets ALL inclusion criteria
- **Exclude**: Paper fails one or more criteria (explicit justification provided)
- **Uncertain**: Ambiguous case requiring manual review

## Dual-Reviewer Mode (recommended for systematic reviews)

Single-pass screening (above) stays the **quick default**. For systematic reviews, dual independent screening is the gold standard — one screener silently drifts on ambiguous criteria. The LLM analogue runs **two independent passes** (a second model or a second prompt, pass 2 blind to pass 1), then measures and adjudicates:

1. **Two independent passes** over the corpus, each emitting Include/Exclude/Uncertain per record. Capture both label sets keyed by id (JSONL: `{"id": "p001", "rater_a": "INCLUDE", "rater_b": "EXCLUDE"}`); add a `reference` field for any manually adjudicated/gold records.
2. **`scripts/kappa.py`** over the two label sets returns **Cohen's kappa** (chance-corrected, since raw % agreement is inflated by the include/exclude imbalance), observed agreement, and the **disagreement list**.
3. **Adjudicate** every disagreement via a **third pass** (tie-breaker model/prompt) or a **human adjudicator** — that becomes the final label.
4. **Report kappa** (target **≥ 0.60**; if lower, the criteria are likely ambiguous — refine `screening-criteria.md` and re-screen). When a **gold/adjudicated subset** exists, also report each pass's **sensitivity/recall + MCC** vs that reference. Recall is the metric that matters for screening — a missed include is the costly error.

```
python scripts/kappa.py dual-screen.jsonl
python scripts/kappa.py dual-screen.csv --a rater_a --b rater_b --ref reference
python scripts/kappa.py dual-screen.jsonl --min-kappa 0.60   # exit 1 below the floor
```

## Active Learning & Stopping Rule (large screening sets)

For large corpora, **prioritize the most-likely-relevant records first** (active learning): rank candidates by relevance and screen the top of the queue, re-ranking as decisions accrue, so relevant papers surface early. Pair this with a **defined stopping rule** — decided in advance (e.g. *N* consecutive records with zero new includes, or a target recall on known positives) — and record where it triggered, so stopping is transparent rather than ad hoc. This decides *order* and *when to stop*, not the per-record decision, and does not replace dual screening.

## Recovery Mode

If screening is interrupted, the skill detects existing `phase1-report.md` and offers to resume from the last processed paper, avoiding redundant work.

## PRISMA Flow Diagram

This skill does **not** draw the PRISMA flow diagram itself. It surfaces the real screening/eligibility counts (records screened, excluded at title/abstract, full-text sought / not retrieved / assessed, excluded-with-reasons, included) and hands them to the **`prisma-flow`** skill. `prisma-flow` combines them with the upstream identification counts (`acquire-corpus`) and duplicates-removed count (`dedupe-records`), renders the PRISMA 2020 diagram, and fails if the arithmetic does not reconcile — replacing any standalone, hollow flow whose duplicate/identification numbers came from nowhere.

## Related Skills

- **design-review-protocol** — front-of-front-end; sets the review type, frames the question, and writes the PRISMA-P protocol. Its eligibility criteria flow through `generate-screening-criteria` into the `screening-criteria.md` this skill applies.
- **acquire-corpus** — search/acquisition front end; documented PRISMA-S search + identification counts.
- **dedupe-records** — record-level dedup between acquisition and screening; produces the deduped corpus and duplicates-removed count.
- **appraise-risk-of-bias** — per-study risk-of-bias appraisal (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2), human-gated, downstream of extraction.
- **prisma-flow** — assembles the PRISMA 2020 flow diagram from this skill's screening/eligibility counts plus the upstream identification/duplicate counts.

Canonical pipeline order: `design-review-protocol` → `generate-screening-criteria` → `acquire-corpus` → `dedupe-records` → **screen-literature** (single-pass or DUAL) → extract / synthesize → `appraise-risk-of-bias` → `validate-evidence` / draft → `validate-*` + `verify-sources` → `prisma-flow` → `verify-review` (loop to verified end-state; consumes the `prisma-flow` reconciliation as `U_prisma`).
