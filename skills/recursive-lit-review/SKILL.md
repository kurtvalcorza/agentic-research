---
name: recursive-lit-review
description: "Recursive literature review with adaptive batching for 50-500+ papers. Use when processing large document corpora that exceed single-context limits, handling systematic reviews with hundreds of papers, or conducting comprehensive literature analysis requiring batch-and-merge compression approaches"
---

# Recursive Literature Review (RLM) v2.0

## Purpose

Process large document corpora (50-500+ papers) that exceed single-context limits through batch-and-merge compression. Implements a "divide and conquer" approach where documents are processed in batches, compressed into atomic claims, then recursively merged into meta-themes.

**Key Features (v2.0):**
- **Adaptive batching** - Varies batch size (1-10 papers) by paper complexity
- **Quality validation** - Gates at every merge level prevent error propagation
- **Hybrid state** - JSON manifest + human-readable execution log
- **Time estimation** - Dynamic prediction with ETA updates
- **Auto-resume** - Multiple checkpoint recovery points

---

## When to Use

**Use Recursive Review Literature when:**
- Corpus exceeds 50 papers
- Standard Review Literature would hit context limits
- Need comprehensive coverage (no paper left behind)
- Building systematic reviews or meta-analyses

**Use Standard Review Literature when:**
- Corpus is <50 papers
- Quick mode (3-phase) is sufficient
- Tight timeline

---




### Phase Dependencies
**See:** _None_

### Input Files
**MUST exist before execution:**
- `corpus/candidates/` - Input PDFs/MD for screening
- `settings/screening-criteria.md` - Inclusion/exclusion criteria (or use defaults)

### Output Directories
**Auto-created if missing:**
- `corpus/approved/` - Papers passing screening
- `corpus/rejected/` - Papers failing screening
- `.cache/rlm/` - Staging files, manifest, execution log
- `outputs/` - Final results

### Related Workflows
- **[[../review-literature/SKILL|Review Literature]]** - Standard workflow for <50 papers
- **[[../write-manuscript/SKILL|Write Manuscript]]** - Drafting after synthesis


---

## Architecture: Batch-and-Merge

```
┌─────────────────────────────────────────────────────────────┐
│                    CORPUS (150 papers)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                    Phase 1: Screening
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPROVED (100 papers)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                    Phase 2: Batch Extraction (Adaptive)
                              │
        ┌─────────┬─────────┬─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼
    Batch 1   Batch 2   Batch 3   ...     Batch 20
   (10 simple) (3 complex) (5 std)       (varies)
        │         │         │               │
        ▼         ▼         ▼               ▼
    staging-  staging-  staging-  ...   staging-
    batch-1   batch-2   batch-3         batch-20
        │         │         │               │
        └─────────┴────┬────┴───────────────┘
                       │
             Phase 3: Meta-Synthesis (Quality Gates)
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
         Level 1   Level 1   Level 1
        (A:1-5)   (B:6-10)  (C:11-15)...
             │         │         │
             └────┬────┘         │
                  ▼              ▼
              Level 2        Level 2
              (X:A-B)        (Y:C-D)
                  │              │
                  └──────┬───────┘
                         │
                         ▼
             Phase 4: Final Report
                         │
                         ▼
            ┌──────────────────┐
            │ Final_Report.md  │
            └──────────────────┘
```

**Key:** Number of levels scales with corpus size (100 papers = 3 levels, 500 papers = 5 levels)

---

## Adaptive Batching Algorithm

### Complexity Detection

For each paper, detect complexity based on:
- Page count (≤5 = simple, ≤15 = standard, ≤50 = complex, >50 = book-chapter)
- Presence of tables, formulas, figures
- Word density

### Batch Size Assignment

```
Complexity weights:
  simple: 1 unit
  standard: 3 units
  complex: 5 units
  book-chapter: 10 units (process alone)

Max load per batch: 15 units

Example results:
  Batch 001: 10 simple papers (10 units)
  Batch 002: 3 standard papers (9 units)
  Batch 003: 2 complex papers (10 units)
  Batch 004: 1 complex + 2 standard (11 units)
  Batch 005: 1 book chapter (10 units, alone)
```

**Benefit:** Processes more papers faster while maintaining quality

---

## Workflow Phases

### Phase 0: Initialization

1. **Check for Manifest** at `.cache/rlm/manifest.json`
   - IF MISSING: Ask "Initialize new RLM for [Project Name]?"
   - IF PRESENT: Read to determine current phase and offer resume

2. **Classify paper complexity** (scan all PDFs)
   - Count simple/standard/complex/book-chapter papers
   - Calculate adaptive batch assignments

3. **Estimate time** based on corpus size and complexity
   - Display: "📊 Corpus: N papers (M adaptive batches), ⏱️ Est: X hours"

4. **Create directory structure and manifest**

---

### Phase 1: Screening

**Input:** Files in `corpus/candidates/`

**Process:**
1. List files in `corpus/candidates/`
2. Select next **10 unprocessed** files (batch size)
3. Read abstracts, introductions, conclusions
4. Evaluate against screening criteria
5. **Move** approved → `corpus/approved/`, rejected → `corpus/rejected/`
6. **Update Manifest and execution-log.md**

**Checkpoint:** User confirms screening batch before proceeding

**Iterate:** Repeat until all candidates processed

---

### Phase 2: Extraction (The Compressor)

**Input:** Files in `corpus/approved/`

**Process:**
1. Assign papers to adaptive batches (based on complexity)
2. For each batch:
   - Read papers
   - Extract atomic claims with page/section references
   - Identify methodology, findings, limitations
   - Note contradictions
   - Write `staging-batch-[N].md`
   - Update manifest (mark batch complete)
   - Update execution-log.md
   - Calculate updated time estimate

**Batch Output Format:**
```markdown
# Staging Batch [N]

## Papers in Batch
1. [Author2023] Title...

## Extracted Claims

### Theme: [Emergent Theme 1]
- Claim: "[Specific finding]" (Author2023, p.12)
- CONTRADICTION: Author2023 claims X, but Author2024 claims Y

## Methodological Notes
- [Author2023]: RCT, n=500, K-12 context

## Gaps Identified
- No papers address [specific gap]
```

**Checkpoint:** Every 5 batches creates a resume point

---

### Phase 3: Structuring (The Architect)

**Quality Gates at Every Merge Level**

Before merging batches, validate:
1. **Citation consistency** - No >10% duplication
2. **Theme duplication** - Flag semantically similar themes
3. **Evidence strength consistency** - Same theme labeled consistently
4. **Coverage check** - No papers lost

**If quality score ≥75:** Proceed with merge
**If quality score <75:** Pause, show issues, request user decision (fix/force/halt)

**Merge Process:**
- Level 0 → Level 1: Merge 5 staging batches into meta-batch
- Level 1 → Level 2: Merge meta-batches into super-batches
- Continue until single root synthesis

**Output:** `outputs/meta-themes.md`

---

### Phase 4: Final Synthesis (Root)

**Input:** Final merged synthesis

**Process:**
1. Generate Final Argument Outline OR Full Report
2. Structure as Known → Gap → Contribution
3. Include citation map to original papers

**Output:** `outputs/[Project_Name]_Report.md`

**Handoff:** Ready for Review Literature Phases 4-7 (drafting, validation)

---

## State Persistence

### manifest.json (Machine-Readable)

```json
{
  "project": "atlas-policy-analysis",
  "corpus_size": 150,
  "batch_strategy": "adaptive",
  "batch_assignments": {
    "batch-001": {
      "papers": ["P001", "P002", "P003", "P004", "P005"],
      "complexity_load": 9,
      "status": "completed",
      "staging_file": ".cache/rlm/batch-001/staging.md",
      "completed_at": "2026-01-17T10:23:00Z"
    }
  },
  "merge_levels": {
    "level-1": { "meta_batches": 6, "completed": 0, "status": "pending" }
  },
  "quality_metrics": {
    "avg_batch_consistency": 87,
    "theme_duplication_rate": 0.05,
    "citation_coverage": 0.98
  },
  "time_estimates": {
    "elapsed_minutes": 45,
    "estimated_remaining_minutes": 105,
    "completion_eta": "2026-01-17T13:00:00Z"
  },
  "checkpoints": [
    { "level": 0, "batch": 5, "timestamp": "...", "can_resume_from": true }
  ],
  "current_state": { "level": 0, "batch": 15, "phase": "Extraction", "resumable": true }
}
```

### execution-log.md (Human-Readable)

```markdown
# Recursive Literature Review Execution Log

**Project:** Project Atlas Policy Analysis
**Started:** 2026-01-17 09:00 GMT+8
**Corpus Size:** 150 papers
**Batch Strategy:** Adaptive

---

## Progress Summary

**Current Status:** Level 0 (Batch Extraction) - 50% Complete

**Completed:**
- ✅ Batch 001-015 (75 papers extracted)
- ✅ Avg consistency score: 87/100

**Time Estimates:**
- Elapsed: 45 minutes
- Remaining: ~105 minutes
- ETA: 1:00 PM

---

## Batch Details

### Batch 001 ✅ Completed
- **Papers:** P001-P005 (5 papers)
- **Themes Extracted:** 2
- **Consistency Score:** 92/100
- **Time:** 3 minutes

...
```

---

## Resume Logic

**If interrupted:**

```
User: "Resume literature review"

Agent:
1. Detect manifest.json
2. Read current_state
3. Display resume options:
   "📍 Detected interrupted Recursive Review Literature
    Last Checkpoint: Batch 15 (50% complete)
    Resume from:
    1️⃣ Batch 15 (Recommended)
    2️⃣ Batch 10
    3️⃣ Start over"

4. Resume from selected checkpoint
```

---

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `batch_strategy` | adaptive | adaptive, fixed-5, fixed-10 |
| `max_load_per_batch` | 15 | Complexity units per batch |
| `screening_batch` | 10 | Papers per screening batch |
| `quality_threshold` | 75 | Minimum consistency score for merges |
| `auto_resume` | true | Auto-resume from manifest |
| `max_papers` | 500 | Safety limit |

---

## Integration with Standard Review Literature

**Routing Logic:**
```
IF corpus ≤ 15 papers → Review Literature Quick Mode (15-25 min)
IF corpus ≤ 50 papers → Review Literature Full Mode (60-90 min)
IF corpus ≤ 500 papers → Recursive Review Literature (2-6 hours)
IF corpus > 500 → Split corpus first
```

**Handoff to Review Literature Phases 4-7:**
After RLM Phase 4:
- Copy `meta-themes.md` to Review Literature `outputs/synthesis-notes.md`
- Review Literature continues with human-led drafting (Phase 4+)

---

## Quality Checks

### Per-Batch Validation
- [ ] All papers in batch were read
- [ ] Claims include citations with page numbers
- [ ] Contradictions explicitly flagged
- [ ] Staging file saved
- [ ] Manifest updated

### Final Validation
- [ ] All batches processed
- [ ] Meta-themes span multiple batches
- [ ] No orphan claims
- [ ] Gaps logically derived from evidence

---

## Success Criteria

Recursive Review Literature successful when:
1. ✅ All papers processed (no papers lost)
2. ✅ Final synthesis created
3. ✅ Quality gates passed (≥75 at all merges)
4. ✅ Execution log complete (human-readable)
5. ✅ Manifest updated (machine-readable)
6. ✅ Handoff to standard Review Literature successful

---

## Related Skills

- **[[../review-literature/SKILL|Review Literature]]** - Standard workflow for <50 papers
- **[[../validate-consistency/SKILL|Validate Consistency]]** - Quality gates
- **[[../write-manuscript/SKILL|Write Manuscript]]** - Drafting after synthesis

---

## Version History

### v2.0 - 2026-01-18
- Consolidated from recursive-lra enhancements
- Adaptive batching (1-10 papers based on complexity)
- Quality validation at merge points
- JSON + Markdown hybrid state (execution-log.md)
- Dynamic time estimation with ETA
- Enhanced resume capability (multiple checkpoints)

### v1.0 - 2026-01-17
- Initial implementation
- Fixed batch size (5 papers)
- Basic 4-phase workflow
- JSON manifest only

---

*Last updated: 2026-01-18*
