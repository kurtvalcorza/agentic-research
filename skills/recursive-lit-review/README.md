# Recursive Literature Review

Recursive literature review system for 50-500+ papers using batch-and-merge compression with adaptive batching by paper complexity.

## Why Recursive?

**Standard lit review**: Works for 10-50 papers, hits context limits beyond that.

**Recursive approach**: Batch papers → extract per batch → merge summaries → recurse up the tree → final meta-synthesis.

## The Phases (0-4)

**Phase 0: Initialization**
- Load all papers
- Classify by complexity (simple, moderate, complex)
- Adaptive batch sizing (10-20 papers depending on complexity)
- Generate batch plan

**Phase 1: Screening**
- Apply screening criteria to each batch
- Track included/excluded with reasons
- Quality gate: flag batch if >50% excluded (possible criteria mismatch)

**Phase 2: Extraction**
- Extract structured data per batch
- Generate batch synthesis

**Phase 3: Structuring (Merge)**
- Merge batch summaries
- Recurse: treat summaries as new "papers" and batch again
- Continue until single meta-synthesis

**Phase 4: Meta-Synthesis & Final Report**
- Synthesize across all batch merges
- Generate final report with:
  - Overall findings
  - Theme emergence
  - Cross-cutting patterns
  - Gaps and contradictions

## Adaptive Batching

**Paper Complexity Classification:**
- **Simple**: Abstracts only, short papers (<10 pages), clear structure
- **Moderate**: Full papers, standard length (10-20 pages)
- **Complex**: Long papers (20+ pages), dense methods, multiple studies

**Batch Sizes:**
- Simple papers: 20 per batch
- Moderate papers: 15 per batch
- Complex papers: 10 per batch
- Mixed batches: Weighted average

## Quality Gates

**After Each Batch Extraction:**
- Minimum data completeness (80% of fields filled)
- Flag if too many papers excluded
- Verify synthesis coherence

**After Each Merge:**
- No information loss from child summaries
- Themes preserved or elevated
- Contradictions noted, not erased

## State Management

**JSON + Markdown Hybrid:**
- `state.json` - Batch tree, progress, metadata
- `batch-[N]/extraction.md` - Per-batch data
- `batch-[N]/synthesis.md` - Per-batch summary
- `merge-[level]/synthesis.md` - Merge-level summaries
- `final-report.md` - Top-level output

## Auto-Resume with Checkpoints

**Checkpoints saved after:**
- Each batch extraction
- Each merge level
- Each quality gate

**Resume logic:**
- Reads `state.json`
- Identifies last completed phase
- Continues from next incomplete batch/merge

## Example Workflow (100 papers)

```
100 papers
├─ Batch 1: 15 papers → summary-1.md
├─ Batch 2: 15 papers → summary-2.md
├─ Batch 3: 15 papers → summary-3.md
├─ Batch 4: 15 papers → summary-4.md
├─ Batch 5: 15 papers → summary-5.md
├─ Batch 6: 15 papers → summary-6.md
└─ Batch 7: 10 papers → summary-7.md

7 summaries → Merge Level 1
├─ Merge 1: summaries 1-3 → meta-summary-A.md
├─ Merge 2: summaries 4-6 → meta-summary-B.md
└─ Merge 3: summary 7 → meta-summary-C.md

3 meta-summaries → Merge Level 2
└─ Final synthesis → final-report.md
```

## When to Use

- **50-100 papers**: Marginal benefit, consider standard review
- **100-300 papers**: Sweet spot for recursive approach
- **300-500+ papers**: Essential, standard review fails

## Outputs

- **Final Report**: Meta-synthesis across all papers
- **Batch Summaries**: Intermediate syntheses (useful for subsection writing)
- **Extraction Matrix**: Full structured data (CSV/Excel)
- **Batch Tree Visualization**: Shows merge hierarchy

## Related Skills

- `review-literature` - Standard 7-phase review (for <50 papers)
- `generate-screening-criteria` - Phase 0, used here too
- `synthesize-research` - Final report uses synthesis patterns
- `validate-citations` - Can validate across all batches

## Typical Timeline

- **100 papers**: 6-10 hours (depends on full-text availability)
- **200 papers**: 12-20 hours
- **500 papers**: 24-40 hours (run overnight with checkpoints)

## Performance Tips

- Pre-organize PDFs into folders matching batches
- Use screening criteria to cut volume early
- Run extraction batches in parallel if API rate limits allow
- Use checkpoints to pause/resume across sessions
