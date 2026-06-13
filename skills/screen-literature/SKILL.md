---
name: screen-literature
description: "Screen research papers against defined criteria with auto-fix for metadata. Use when filtering a PDF corpus for inclusion, running Phase 1 screening, or applying inclusion/exclusion criteria to research papers."
---








# Specialist: Literature Screener

## Purpose
Filter the `corpus/` directory using `settings/screening-criteria.md`.

## Inputs
- `corpus/*.pdf` or `corpus/*.md`
- `settings/screening-criteria.md`

## Scripts
- `scripts/kappa.py` — inter-rater agreement for **dual-reviewer mode** (Cohen's kappa + observed agreement + disagreement list; sensitivity/recall + MCC vs a gold/adjudicated reference). Stdlib only. Supports `--min-kappa` to fail a run below a kappa floor. See **Dual-reviewer mode** below.

> **Corpus source (full pipeline).** This skill works on whatever sits in `corpus/` — the bring-your-own-PDFs path is still fully supported. In the **full review pipeline**, however, the corpus should come from `acquire-corpus` → `dedupe-records` rather than a hand-collected pile: `acquire-corpus` produces a documented, PRISMA-S search (real *identification* counts per source + snowball), and `dedupe-records` removes duplicates and emits a real *duplicates-removed* count (`corpus/deduped.jsonl` + `corpus/dedup-report.md`). Feeding screening from that deduped set is what makes the upstream PRISMA numbers REAL instead of placeholders. Point `corpus/` at `dedupe-records`' output (`corpus/deduped.jsonl`, resolving PDFs/metadata from it) when running end to end.

## Outputs
- `outputs/phase1-report.md`
- **Screening/eligibility counts** for the PRISMA flow (see PRISMA Reporting below): records screened, excluded at title/abstract, full-text sought / not retrieved / assessed, excluded-with-reasons, included.

## Workflow

### 1. Verification
- Validate `corpus/` is not empty.
- Validate `screening-criteria.md` exists.

### 2. State Recovery
- Check `outputs/phase1-progress.md`.
- **Resume Logic**: Load processed list, continue from next file.

### 3. Execution (Iterative)
For each file in `corpus/`:
1.  **Extract Metadata**: Title, Author, Year.
    - **Auto-Fix**: If metadata extraction fails, infer from filename (e.g., "Smith_2024.pdf").
2.  **Apply Criteria**: Compare against `screening-criteria.md`.
3.  **Decision**: Include/Exclude/Uncertain.
4.  **Save State**: Update `phase1-progress.md` immediately.

### 3b. Dual-reviewer mode (recommended for systematic reviews)

Single-pass (Step 3 above) remains the **quick default**. For systematic reviews, dual independent screening is the gold standard, because one screener silently drifts on ambiguous criteria; the LLM analogue is **two independent screening passes** whose agreement you can measure and whose conflicts you adjudicate.

1. **Run two independent passes.** Screen the whole corpus twice, independently — a second model **or** a second prompt (do not let pass 2 see pass 1's labels). Each pass emits the same Include/Exclude/Uncertain decision per record. Capture both label sets keyed by record id, e.g. as JSONL: `{"id": "p001", "rater_a": "INCLUDE", "rater_b": "EXCLUDE"}` (one line per record). If you have a manually adjudicated/gold subset, add a `reference` field for those records.
2. **Measure agreement + list conflicts.** Run the script over the two label sets:
   ```
   python scripts/kappa.py dual-screen.jsonl
   # CSV with custom columns: python scripts/kappa.py dual-screen.csv --a rater_a --b rater_b --ref reference
   # Gate a run: python scripts/kappa.py dual-screen.jsonl --min-kappa 0.60   (exit 1 if below)
   ```
   It reports **Cohen's kappa** (chance-corrected — raw % agreement is inflated by the include/exclude class imbalance), observed agreement, and the **disagreement list** (the record ids a third reviewer/human must resolve).
3. **Adjudicate disagreements.** Route every disagreement to a **third pass** (a tie-breaker model/prompt) or to a **human adjudicator**. The adjudicated decision is the final label for those records; agreed records keep their shared label.
4. **Report and gate.**
   - Report **kappa**. **Target ≥ 0.60** (substantial). If kappa is **lower**, the criteria are likely ambiguous — refine `screening-criteria.md` (tighten/clarify the ambiguous rules, add examples) and **re-screen**, rather than trusting the split.
   - When a **gold/adjudicated subset** exists, also report each pass's **sensitivity/recall** and **MCC** vs that reference (the metrics the LLM-screening literature uses). Recall is the metric that matters for screening — a missed include is the costly error; report it (and the chance-corrected MCC), not raw accuracy, which class imbalance inflates.

### 3c. Active learning & stopping rule (large screening sets)

For large corpora, **prioritize the most-likely-relevant records first** (active learning): rank candidates by relevance (e.g. similarity to the criteria / already-included papers) and screen the top of the queue first, re-ranking as decisions accrue. This front-loads the includes so most relevant papers surface early. Pair this with a **defined stopping rule** — decide in advance when to stop screening the long tail (e.g. *N* consecutive records screened with zero new includes, or a target recall on a known-positive sample) — and record the rule and where it triggered, so the stopping decision is transparent and reproducible rather than ad hoc. (Active-learning prioritization + an explicit stopping criterion are good practice; they do not replace dual screening — they decide *order* and *when to stop*, not the per-record decision.)

### 4. Finalization
- Generate `outputs/phase1-report.md` with:
    - Summary Table (Included/Excluded count).
    - List of Included papers.
    - List of Excluded papers (with reason).
    - **Stage tallies for PRISMA** (see below): records screened, excluded at title/abstract, full-text sought / not retrieved / assessed, **excluded-with-reasons** (one count per reason), included.

### 5. PRISMA Reporting (hand off to `prisma-flow` — do not emit a standalone flow)
This skill **does not draw the PRISMA flow diagram itself.** Instead, surface the actual screening/eligibility counts and hand them to the **`prisma-flow`** skill, which assembles the PRISMA 2020 Mermaid diagram and **fails if the arithmetic does not reconcile**:
- From this skill: records screened, excluded at title/abstract, reports sought / not retrieved / assessed, reports excluded **with reasons**, studies included.
- From `acquire-corpus`: identification counts (per database + snowball).
- From `dedupe-records`: duplicates-removed count.

Combine these into the `counts.json` consumed by `prisma-flow` (schema in its `scripts/prisma_flow.py`) and let that skill render `prisma-flow.md`. This replaces emitting a hollow flow whose identification/duplicate numbers came from nowhere — those upstream rows must come from `acquire-corpus`/`dedupe-records`, and the screening/eligibility rows from the tallies above.

## Error Handling
- **Unreadable File**: Mark as "Excluded (Corrupted)" and log error.

## Related
- `design-review-protocol` — the front-of-front-end; before screening, it selects the review type, frames the question (PICO/PEO/SPIDER/PCC), and writes the registrable PRISMA-P `protocol.md`. Its eligibility criteria feed `generate-screening-criteria`, which produces the `screening-criteria.md` this skill applies.
- `acquire-corpus` — upstream search front end; produces real *identification* counts + the candidate corpus.
- `dedupe-records` — runs between acquisition and this skill; produces the deduped corpus (`corpus/deduped.jsonl`) and the *duplicates-removed* count.
- `appraise-risk-of-bias` — downstream of extraction; per-study RoB with the design-appropriate instrument (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2), **human-gated**. Like dual screening here, RoB appraisal benefits from dual review, but stays human-gated (LLM appraisal accuracy is the weakest link).
- `prisma-flow` — downstream reporting; assembles the PRISMA 2020 flow diagram from this skill's screening/eligibility counts plus the upstream identification/duplicate counts.
- Canonical order: `design-review-protocol` → `generate-screening-criteria` → `acquire-corpus` → `dedupe-records` → **`screen-literature`** (single-pass or DUAL) → extract/synthesize → `appraise-risk-of-bias` → `validate-evidence` (GRADE) / draft → `prisma-flow`.


## Internal Metadata
- **capabilities**: [file-read, file-write, command-exec, file-search]
- **domain**: research
- **status**: active
- **version**: 2.0
- **type**: specialist