---
tags: [reference, workflow, phases, literature-review]
created: 2026-01-11
---

# Detailed Phase Descriptions

Complete reference for all 7 phases of the Review Literature workflow.

## Phase 1: Corpus Screening

**Agent:** [[phase1-screener|Screener]]
**Mode:** 🤖 Automated
**Duration:** 5-30 minutes (depending on corpus size)

### Purpose
Evaluate research PDFs against defined criteria to produce an approved corpus.

### Inputs
- Candidate PDFs in `corpus/candidates/`
- `settings/screening-criteria.md` (inclusion/exclusion rules)
- `settings/research-question.md` (relevance context)

### Process
1. Read each PDF (abstract, intro, conclusion)
2. Apply screening criteria
3. Assign relevance score (0-10)
4. Make decision: INCLUDE / EXCLUDE / UNCERTAIN
5. Provide justification for each decision

### Outputs
- `outputs/phase1-screening-report_project.md`
- `outputs/phase1-prisma-flow-diagram_project.md`
- `outputs/phase1-screening-progress_project.md`
- Decisions for all PDFs with justifications
- Edge cases flagged for human review

### Checkpoint 1
**User reviews screening report and:**
- Confirms approved papers are relevant
- Checks rejected papers weren't missed
- Addresses edge cases
- Moves approved PDFs to `corpus/approved/`

**Quality Gate:** Approved corpus size 5-100 papers (warn if outside range)

---

## Phase 2: Extraction & Synthesis

**Agent:** [[phase2-extractor|Extractor]]
**Mode:** 🤖 Automated
**Duration:** 15-45 minutes (depending on corpus size)

### Purpose
Extract key findings and identify cross-paper themes, claims, gaps, and contradictions.

### Inputs
- Approved PDFs in `corpus/approved/`
- `settings/research-question.md` (thematic focus)
- `outputs/phase1-screening-report_project.md` (context)

### Process
1. Read each approved paper systematically
2. Extract claims, evidence, limitations
3. Cluster findings into themes
4. Identify consensus areas (3+ papers agree)
5. Surface contradictions (papers disagree)
6. Identify research gaps

### Outputs
- `outputs/phase2-paper-pXXX-extraction_project.md`
- `outputs/phase2-extraction-matrix_project.md`
- `outputs/phase2-synthesis-matrix_project.md`
- `outputs/phase2-extraction-quality-report_project.md`
- Themes with supporting papers
- Consensus and contradictions mapped
- Research gaps identified
- Reading lenses for Phase 4

### No Checkpoint
Proceeds automatically to Phase 3.

---

## Phase 3: Argument Structuring

**Agent:** [[phase3-structurer|Structurer]]
**Mode:** 🤖 Automated
**Duration:** 10-20 minutes

### Purpose
Build logical argument outline using Known → Unknown → Contribution framework.

### Inputs
- `outputs/phase2-synthesis-matrix_project.md` (themes, gaps)
- `settings/research-question.md` (contribution framing)
- `outputs/phase1-screening-report_project.md` (corpus context)

### Process
1. Extract "Known" (consensus from Phase 2)
2. Extract "Unknown" (gaps from Phase 2)
3. Map Known → Unknown logical flow
4. Frame "Your Contribution" (how work fills gap)
5. Provide 3 framing options (supportive, challenging, extending)
6. Validate logical flow

### Outputs
- `outputs/phase3-argument-outline_project.md`
- Known section (consensus claims)
- Unknown section (research gaps)
- Contribution statement
- Framing options for Phase 6

### Checkpoint 2 (CRITICAL)
**User reviews outline and:**
- Validates "Known" accurately reflects consensus
- Challenges identified gaps (are they defensible?)
- Tests contribution logic (does it follow from gap?)
- Revises outline if needed

**This is the HANDOFF POINT to Phase 4 (human-led).**

---

## Phase 4: Drafting (Human-Led)

**Agent:** [[phase4-drafter|Drafter Support]]
**Mode:** 👤 Human-led (AI provocation mode)
**Duration:** Variable (user-driven)

### Purpose
User writes literature review with AI provocations, NOT AI writing.

### Inputs
- `outputs/phase4-handoff-document_project.md` (created by orchestrator)
- `outputs/phase2-synthesis-matrix_project.md` (as reading lenses)
- `outputs/phase3-argument-outline_project.md` (as scaffold)
- Approved papers in `corpus/approved/` (user MUST read)
- [[../../enhance-writing/references/academic-writing|Enhance Writing Protocol]]

### Process
**BEFORE Writing:**
1. Answer critical provocations (Understanding, Gap Validation, Contribution Test)
2. Read approved papers yourself (use Phase 2 as lenses, not replacements)
3. Challenge Phase 3 outline based on YOUR reading

**DURING Writing:**
1. Use Enhance Writing academic writing protocol
2. Write in YOUR voice, YOUR framing
3. AI provides provocations when requested:
   - "Can you defend this claim?"
   - "Have you read this paper yourself?"
   - "What's your assumption here?"

**AVOID:**
- ❌ Copy-pasting Phase 2 synthesis
- ❌ Citing papers you haven't read
- ❌ Accepting Phase 3 outline uncritically

### Outputs
- User's Structure Arguments (user provides location)
- Provocations logged in conversation

### Checkpoint 3
Continuous provocations during writing (no formal checkpoint).

**Quality Gate:** User must read papers themselves, not rely on AI summaries.

**Documentation mode:** Stop after Phase 4 for technical documentation or background sections.

---

## Phase 6: Contribution Framing

**Agent:** [[phase6-framer|Framer]]
**Mode:** ?? Hybrid
**Duration:** 10-20 minutes

### Purpose
Generate contribution framing options and help user choose positioning.

### Inputs
- User's draft (Phase 4 output)
- `outputs/phase3-argument-outline_project.md` (preliminary framing)
- `settings/research-question.md` (context)
- `outputs/phase2-synthesis-matrix_project.md` (themes)

### Process
1. Analyze draft positioning
2. Generate 3 framing options:
   - **Option A: Supportive** (extends consensus)
   - **Option B: Challenging** (questions assumptions)
   - **Option C: Extending** (applies to new context)
3. Map each option to Phase 3 outline
4. Provide trade-off analysis (pros/cons)
5. Make recommendation based on user's goals
6. **Post-framing revision pass:** User revises the draft to align with chosen framing

### Outputs
- `outputs/phase6-contribution-framing_project.md`
- 3 framing options with trade-offs
- Decision matrix
- Recommendation with rationale

### Checkpoint 4
**User chooses framing:**
- Selects Option A, B, or C
- Or proposes own framing
- Revises draft to align with chosen framing

**Then proceeds to Phase 5.**

---

## Phase 5: Citation Validation

**Agent:** [[phase5-validator|Validator]]
**Mode:** ?? Automated
**Duration:** 10-30 minutes

### Purpose
Validate all citations against source papers to detect fabrication, misattribution, overstatement.

### Inputs
- User's framed and revised full draft
- Approved PDFs in `corpus/approved/`
- `outputs/phase2-synthesis-matrix_project.md` (for copy-paste detection)

### Process
1. Extract all citations from draft
2. For each citation:
   - Read cited section in source paper
   - Verify claim accuracy
   - Check for overstatement/understatement
3. Detect copy-paste from Phase 2 (>80% similarity)
4. Flag missing citations
5. Validate consensus claims (3+ sources required)

### Outputs
- `outputs/phase5-citation-validation_project.md`
- ? Accurate citations
- ?? Citations needing revision (overstatements)
- ? Incorrect citations (fabrication/misattribution)
- Copy-paste sections detected
- Recommended fixes

### No Formal Checkpoint
User fixes issues before Phase 7.

**Quality Gate:** All ? incorrect citations must be fixed.

---

## Phase 7: Consistency Validation

**Agent:** [[phase7-consistency|Consistency Validator]]
**Mode:** 🤖 Automated
**Duration:** 10-20 minutes

### Purpose
Final QA check for consistency across intro, body, conclusion.

### Inputs
- User's final draft
- `outputs/phase3-argument-outline_project.md` (original structure)
- `outputs/phase6-contribution-framing_project.md` (chosen positioning)
- All previous outputs

### Process
1. **Introduction ↔ Conclusion alignment:**
   - Research question stated and answered?
   - Key themes previewed and concluded?
   - Framing consistent?

2. **Claims ↔ Evidence alignment:**
   - All claims supported by evidence?
   - Citations accurate (cross-check Phase 5)?
   - Consensus claims have 3+ sources?

3. **Argument flow:**
   - Follows Known → Unknown → Contribution?
   - Logical transitions between sections?
   - Narrative coherence?

4. **Phase 3 outline consistency:**
   - "Known" accurately represented?
   - "Unknown" gaps addressed?
   - Contribution aligns with chosen framing?

### Outputs
- `outputs/phase7-consistency-report_project.md`
- Overall consistency score (0-100%)
- Detailed analysis by section
- Critical/moderate/minor issues flagged
- Recommendations for fixes

### Checkpoint 5 (Final)
**User reviews consistency report:**
- If score ≥ 75%: Ready for finalization (address critical issues)
- If score < 75%: Fix flagged issues, optionally re-run Phase 7

**Quality Gate:** Consistency score ≥75% target for approval.

---

## Workflow Summary

| Phase | Duration | Mode | Checkpoint? | Purpose |
|-------|----------|------|-------------|---------|
| 1. Screening | 5-30 min | 🤖 Automated | **YES** | Approve corpus |
| 2. Extraction | 15-45 min | 🤖 Automated | No | Extract themes, gaps |
| 3. Structuring | 10-20 min | 🤖 Automated | **YES** | Build outline |
| **HANDOFF** | — | — | **YES** | User takes ownership |
| 4. Drafting | Variable | 👤 Human-led | Continuous | User writes |
| 6. Framing | 10-20 min | 🤝 Hybrid | **YES** | Choose positioning |
| 5. Validation | 10-30 min | 🤖 Automated | No | Check citations |
| 7. Consistency | 10-20 min | 🤖 Automated | **YES** | Final QA |

**Total automated time:** 1-3 hours (depending on corpus size)
**Total user time:** 5-15 hours (reading + writing)
**Time saved:** 10-20 hours (vs. manual screening + extraction)

## Version History

### v1.0 - 2026-01-11
- Initial workflow phases documentation
- 7-phase breakdown with inputs/outputs
- Checkpoint descriptions
- Duration estimates

## Related

- [[../SKILL|Main Skill Definition]]
- [[../INTEGRATION|Hybrid Workflow Philosophy]]
- [[../README|Quick Start Guide]]
- [[handoff-guide|Phase 3→4 Handoff Guide]]
- [[checkpoint-protocol|Checkpoint Protocol]]







