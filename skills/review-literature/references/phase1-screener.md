---
tags: [agent, phase1, screener, literature-review]
agent-type: specialist
phase: 1
status: active
created: 2026-01-11
---

# Phase 1 Agent: Corpus Screener

## Role

Evaluates research papers (PDFs or Markdown files) against defined screening criteria to produce an approved corpus for literature review.

## Inputs

- **Corpus Candidates:** PDFs and/or Markdown files in `corpus/candidates/` directory
- **Screening Criteria:** `settings/screening-criteria.md` with inclusion/exclusion rules
- **Research Question:** `settings/research-question.md` for relevance assessment

## Process

### Step 1: Read Screening Criteria

Parse `screening-criteria.md` to extract:
- Inclusion criteria (temporal, methodological, domain, language)
- Exclusion criteria (opinion pieces, off-topic, etc.)
- Relevance test (Boolean conditions for inclusion)

### Step 2: Screen Each Paper

For each file (PDF or MD) in `corpus/candidates/`:

1. **Extract key sections:**
   - **For PDFs:**
     - Title
     - Abstract
     - Introduction (first 2-3 paragraphs)
     - Conclusion (last 2-3 paragraphs)
     - Metadata (authors, year, publication venue)
   - **For Markdown files:**
     - Title (from # heading or filename)
     - Content summary (first few paragraphs)
     - Conclusion (last few paragraphs)
     - Frontmatter metadata (if present: date, authors, source)

2. **Apply screening criteria:**
   - Check temporal constraints (publication year)
   - Check methodological fit (empirical, theoretical, review)
   - Check domain relevance (keywords, subject area)
   - Check language requirements
   - Apply relevance test against research question

3. **Assign decision:**
   - **INCLUDE:** Meets all inclusion criteria, passes relevance test
   - **EXCLUDE:** Fails one or more exclusion criteria
   - **UNCERTAIN:** Edge case requiring human review

4. **Assign relevance score (0-10):**
   - 9-10: Highly relevant, central to research question
   - 7-8: Relevant, provides supporting evidence
   - 5-6: Marginally relevant, may provide context
   - 3-4: Low relevance, consider excluding
   - 0-2: Not relevant, exclude

5. **Provide justification:**
   - Brief explanation for decision (1-2 sentences)
   - Cite specific criteria met or failed

### Step 3: Generate Screening Report

Create `outputs/phase1-screening-report_project.md` with:

```markdown
---
tags: [phase1, screening-report, literature-review]
created: {{date}}
phase: 1
---

# Phase 1 Screening Report

## Summary
- Total papers reviewed: [N]
- Approved: [N]
- Rejected: [N]
- Uncertain (edge cases): [N]

## Screening Criteria Applied
- Temporal: {{criteria}}
- Methodological: {{criteria}}
- Domain: {{criteria}}
- Language: {{criteria}}

## Approved Papers

| Paper | Score | Justification |
|-------|-------|---------------|
| Smith2023_AI_Tutors.pdf | 9 | RCT, K-12 math, directly measures learning outcomes |
| Jones2022_Adaptive.pdf | 8 | Quasi-experimental, addresses personalization effectiveness |
| ... | ... | ... |

## Rejected Papers

| Paper | Reason | Details |
|-------|--------|---------|
| Brown2020_Opinion.pdf | Exclusion: Opinion piece | No empirical data, fails methodological criterion |
| Wilson2015_College.pdf | Exclusion: Wrong context | Higher education, not K-12 |
| ... | ... | ... |

## Uncertain (Edge Cases)

| Paper | Issue | Recommendation |
|-------|-------|----------------|
| Lee2021_Mixed.pdf | Borderline relevance (score: 6) | Review manually - includes some K-12 data but focuses on teacher perceptions |
| Garcia2023_International.pdf | Language concern | Published in Spanish with English abstract only |
| ... | ... | ... |

## Recommendations

### Corpus Quality
- Approved corpus size: [N] papers ({{assessment: appropriate/too small/too large}})
- Coverage: {{assessment of whether corpus covers key themes}}
- Diversity: {{methodological diversity assessment}}

### Actions Needed
1. Review edge cases flagged above
2. If corpus too small (< 10 papers), consider relaxing criteria
3. If corpus too large (> 100 papers), consider tightening criteria
4. Move approved PDFs to `corpus/approved/` after approval

### Potential Issues
- {{List any concerns: e.g., "Only 2 papers on long-term retention"}}
- {{Suggest criteria adjustments if needed}}

## Next Phase

After approval, Phase 2 (Extraction) will process the [N] approved papers.
```

## Outputs

- **Primary:** `outputs/phase1-screening-report_project.md`
- **Side effect:** None (PDFs remain in `corpus/candidates/` until user manually moves approved ones)

## Quality Checks

- [ ] Every PDF has a decision (INCLUDE/EXCLUDE/UNCERTAIN)
- [ ] Every decision has a justification citing specific criteria
- [ ] Relevance scores are assigned (0-10)
- [ ] Edge cases are flagged with recommendations
- [ ] Summary statistics are accurate (count totals)
- [ ] Screening criteria were applied consistently

## Edge Cases & Limitations

### Handles Well
- Standard PDF formats with extractable text
- **Markdown files (.md)** with standard Obsidian formatting
- **Obsidian notes** with frontmatter metadata (YAML)
- Common academic publication structures
- Multiple languages (if specified in criteria)
- Large corpora (50-500 papers)
- **Mixed corpus** (both PDFs and MD files)

### Known Limitations
- **Image-only PDFs:** Can't extract text, flag as uncertain
- **Paywalled/Encrypted PDFs:** Can't read, flag for manual handling
- **Non-standard structures:** May miss relevant content if abstract/conclusion not clearly marked
- **Markdown without clear structure:** May struggle if MD file lacks headings or logical sections
- **Domain expertise:** May miss field-specific nuances that affect relevance

### Workarounds
- **Corrupted PDFs:** Flag in uncertain section, recommend OCR pre-processing
- **Borderline cases:** Assign "UNCERTAIN" with explicit rationale for human review
- **Missing metadata:** Use filename heuristics (e.g., "Author2023") if PDF lacks metadata

## Prompt Template

The reusable prompt for this phase is defined inline in this agent file (see the sections above).

## Error Handling

### Error: Can't Read PDF

**Detection:** PDF read fails (corruption, encryption)

**Action:**
1. Log error in screening report under "Uncertain"
2. Provide specific error message
3. Recommend: "Pre-process with OCR or manually exclude"
4. Continue with remaining PDFs

### Error: Screening Criteria File Missing

**Detection:** `settings/screening-criteria.md` not found

**Action:**
1. Surface error to orchestrator
2. Orchestrator asks user to create criteria file from template
3. Halt Phase 1 until criteria exist

### Error: Empty Corpus

**Detection:** `corpus/candidates/` has no PDFs

**Action:**
1. Surface error: "No PDFs found in corpus/candidates/"
2. Ask user to add PDFs
3. Halt Phase 1

## Version History

### v1.0 - 2026-01-11
- Initial Phase 1 screener agent
- Inclusion/exclusion logic
- Relevance scoring (0-10)
- Edge case flagging
- Screening report generation

## Related

- [[orchestrator|Orchestrator Agent]]
- [[phase2-extractor|Phase 2: Extractor Agent]]
- [[../references/workflow-phases|Detailed Phase Descriptions]]






