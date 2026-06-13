---
name: write-manuscript
description: Synthesize research notes into academic manuscripts with quality gates and validation. Supports Full Mode (45 min, comprehensive) and Express Mode (15-20 min, streamlined). Use when writing manuscripts, papers, research synthesis, or transforming notes into structured academic documents.
---

# Write Manuscript (Research Synthesis)

## Purpose

Transform already-processed research notes (Markdown files, AI summaries, literature extracts) into coherent academic manuscripts through structured workflow with quality gates and comprehensive validation.

**Core Philosophy:** Bridge "summary" to "synthesis" - manuscripts are argumentative, not descriptive.

---

## Modes

Two workflow modes optimized for different content types and time constraints.

| Mode | Time | Use Cases |
|------|------|-----------|
| **Full Mode** | 45 min | Thesis chapters, journal papers, original research, grant proposals |
| **Express Mode** | 15-20 min | Blog posts, news releases, policy briefs, executive summaries |

**Key Difference:**
- **Full Mode:** Comprehensive structure analysis, deep tension exploration
- **Express Mode:** Streamlined workflow, lighter analysis, same quality gates

[Detailed specifications: [[references/mode-specifications|Mode Specifications]]]

---

## Dependencies

### Required Capabilities
- **file-read** - Ingest research notes and outlines
- **file-write** - Create drafts and handoff documents
- **file-search** - Locate research notes in workspace

### Input Files
- **Research Notes:** Markdown files with findings/summaries (from any source: LRA outputs, manual notes, AI summaries)
- **Target Outline:** (Optional) Desired structure
- **Synthesis Matrix:** (Optional) From LRA Phase 2 output

### Output Directories
- Same directory as input notes
- `outputs/` (if working from project directory)
- `validation/` (for Phase 5 validation reports)

### Optional Skill Integrations
- **recursive-lit-review** - Provides meta-themes for structuring
- **review-literature** - Provides argument outline and synthesis notes
- **validate-manuscript** - Auto-invoked at Phase 5 for comprehensive validation

[Integration details: [[references/integration-protocols|Integration Protocols]]]

---

## Workflow

### Phase 1: Source Synthesis

**Objective:** Understand research notes and identify single most important contribution.

**Process:**
1. Read all provided research notes
2. Identify three core elements:
   - **Knowns** - What sources agree on
   - **Gaps** - What remains unaddressed
   - **Key Claims** - Central arguments in sources

3. **Contribution Test:**
   - Full Mode: "What is the single most important contribution this manuscript makes? If I deleted this paper, what knowledge would be lost?"
   - Express Mode: "What's the one thing you want readers to take away?"

**Checkpoint:** User must articulate contribution before proceeding. This is a BLOCKING checkpoint.

**Mode Variations:**
- **Full Mode:** Deep read, comprehensive tension analysis
- **Express Mode:** Quick scan, skip deep tension analysis

[Detailed logic: [[references/phase-logic#phase-1|Phase 1 Logic]]]

---

### Phase 2: Argument Structuring

**Objective:** Transform source understanding into argumentative structure.

**Framework:** Known → Gap → Contribution

**Process:**
1. **Map Consensus**
   - What do all notes agree on?
   - What's the established "state of the art"?

2. **Identify Tensions**
   - Where do notes disagree?
   - Highlight contradictions (don't smooth over)
   - Tensions are research opportunities

3. **Scaffold Outline**
   - Create `manuscript-outline.md`
   - Structure the argument, not just topics
   - Each section advances the argument

**Output Format:**
```markdown
## 1. Introduction
**Argument:** Establish problem space and significance
**Key claim:** [What reader should believe after intro]

## 2. Background / Literature Review
**Argument:** Show what's known and what's missing
**Consensus:** [Agreed findings]
**Tensions:** [Disagreements/contradictions]
**Gap:** [Specific gap addressed]

## 3. Methodology / Approach
**Argument:** Justify method for addressing gap
**Why this method:** [Reasoning]

## 4. Results / Findings
**Argument:** Present evidence for contribution
**Key evidence:** [Main findings]

## 5. Discussion
**Argument:** Interpret findings in context of gap
**Implications:** [What this means]
**Limitations:** [What not addressed]

## 6. Conclusion
**Argument:** Restate contribution and future directions
**Take-away:** [One sentence summary]
```

**Mode Variations:**
- **Full Mode:** Complete consensus mapping, detailed tension analysis
- **Express Mode:** Quick mapping, outline without deep tension analysis

[Complete template: [[references/manuscript-templates#outline|Outline Template]]]
[Detailed logic: [[references/phase-logic#phase-2|Phase 2 Logic]]]

---

### Phase 3: Interactive Drafting

**Objective:** Transform outline into manuscript prose while maintaining quality.

**Core Pattern: Challenge-Before-Assist**

**Process:**
1. Draft section-by-section
2. Present alternative framings when multiple approaches exist
3. Require user adjudication of tensions
4. Verify all claims trace to sources

**Alternative Framing Presentation:**

When multiple framings possible:
- Identify 2-3 alternative approaches
- Explain implications of each
- Require user to choose
- Proceed with user's adjudicated position

**Tension Adjudication Requirement:**

When sources disagree:
- Highlight tension explicitly
- DO NOT smooth over disagreement
- Require user to take a position
- User's position becomes manuscript's stance

**Source Traceability:**
- Every claim must trace to input sources
- Flag untraceable claims immediately
- Warn on introduction of outside sources

**Mode Variations:**
- **Full Mode:** Continuous challenge, deep assumption surfacing, multiple alternatives
- **Express Mode:** 1-2 key challenges per section, focus on claim accuracy and evidence support

**Outputs:**
- `[section]-draft.md` for each section
- `manuscript-draft.md` (complete manuscript)

[Detailed logic: [[references/phase-logic#phase-3|Phase 3 Logic]]]

---

### Phase 4: Quality Gates

**Objective:** Verify manuscript meets quality standards before validation.

**Citation Check:**
- Stick to sources provided in input notes
- Warn if user introduces outside claims without evidence
- Flag any claim that can't be traced to a source

**Consistency Check:**
- Does Conclusion match Introduction?
- Does Gap identified match Contribution claimed?
- Are same terms used consistently throughout?

**Quality Checklists:**

**Before Writing:**
- [ ] User articulated single most important contribution
- [ ] Tensions in sources identified
- [ ] User adjudicated contradictions (not ignored)

**During Writing:**
- [ ] Every claim traces to source in input notes
- [ ] User actively thinking (not just accepting)
- [ ] Argument advances in each section

**After Writing:**
- [ ] Conclusion matches Introduction
- [ ] Contribution addresses stated Gap
- [ ] No hallucinated citations
- [ ] Limitations acknowledged

**Output:** `citation-check.md` (verification report)

[Complete quality gates: [[references/quality-gates|Quality Gates]]]
[Detailed logic: [[references/phase-logic#phase-4|Phase 4 Logic]]]

---

### Phase 5: Validation Handoff

**Objective:** Auto-invoke comprehensive validation suite for deeper analysis.

**Process:**
1. After Phase 4 quality gates pass, offer validation
2. Pre-populate validation with:
   - `manuscript-draft.md` (from Phase 3)
   - `synthesis-notes.md` (from LRA or input)
   - `manuscript-outline.md` (from Phase 2)
3. Invoke validate-manuscript skill
4. Run 4-skill validation sequence
5. Return consolidated report

**Validation Options:**
- **Full Validation:** Complete suite, ~5 minutes, consolidated report (recommended)
- **Quick Validation:** Citations + consistency only, ~2 minutes
- **Skip Validation:** Export as-is (not recommended for publication)

**Validation Results:**

**Overall Score:** X/100

**Status:**
- **PASS** - Ready for submission
- **NEEDS ATTENTION** - Review validation-report.md, address issues
- **FAIL** - Critical issues, do not proceed to submission

**Next Steps:**
- If PASS: Ready for submission, proceed to export
- If NEEDS ATTENTION: Review validation-report.md, address issues
- If FAIL: Address critical issues before proceeding

**Outputs:**
- `validation-report.md` (consolidated score and findings)
- `validation/*.md` (detailed sub-reports)

[Integration details: [[references/integration-protocols#validate-manuscript|Validation Integration]]]
[Detailed logic: [[references/phase-logic#phase-5|Phase 5 Logic]]]

---

## Anti-Patterns

What NOT to do when synthesizing manuscripts.

| Anti-Pattern | Why It's Bad |
|--------------|--------------|
| **Copy-Pasting** | Concatenating summaries ≠ synthesis |
| **Ghostwriting** | Writing sections without user input on the point |
| **Hallucinated Citations** | Inventing sources not in input notes |
| **Smoothing Tensions** | Resolving contradictions user hasn't adjudicated |
| **Accepting Uncritically** | Letting user accept AI framing without examination |

[Complete anti-patterns: [[references/quality-gates#anti-patterns|Anti-Patterns]]]

---

## Output Files

| File | Purpose | Created In |
|------|---------|------------|
| `manuscript-outline.md` | Argument structure | Phase 2 |
| `[section]-draft.md` | Section drafts | Phase 3 |
| `manuscript-draft.md` | Full draft | Phase 3 completion |
| `citation-check.md` | Verification report | Phase 4 |
| `validation-report.md` | Consolidated validation | Phase 5 (if run) |
| `validation/*.md` | Detailed sub-reports | Phase 5 (if run) |

[File organization: [[references/manuscript-templates#output-files|Output Files]]]

---

## Integration with Other Skills

### With Literature Review Automation (LRA)

**Handoff from LRA Phase 3:**
- LRA provides `argument-outline.md` and `synthesis-notes.md`
- Write Manuscript takes these as input
- **Critical:** User should NOT accept LRA outputs uncritically

**Bridge Protocol:**
1. Read LRA outputs
2. Challenge: "LRA identified [Gap X]. Do you agree this is the real gap, or is it missing something?"
3. Proceed with user's adjudicated position

---

### With Recursive Lit Review (RLM)

**After RLM generates `meta-themes.md`:**
- Write Manuscript helps structure themes into argument
- Ensure meta-themes become YOUR argument, not just a report of what papers said
- Transform descriptive themes into argumentative contributions

---

### With Validate Manuscript

**Auto-handoff at Phase 5:**
- Write Manuscript → Validate Manuscript (seamless)
- Validation runs 4 skills in sequence
- Returns consolidated score and report

**Integration Benefits:**
- No manual file referencing
- Consistent validation every time
- Clear pass/fail before submission

[Complete integration protocols: [[references/integration-protocols|Integration Protocols]]]

---

## Critical Distinctions

| What This Skill DOES | What This Skill Does NOT |
|---------------------|--------------------------|
| Challenge arguments | Auto-generate full manuscripts |
| Check logic | Write sections without user input |
| Force "summary" → "synthesis" bridge | Accept AI synthesis uncritically |
| Surface tensions in sources | Smooth over contradictions |

**Core Philosophy:**
- Manuscripts are argumentative, not descriptive
- User owns intellectual position
- Tensions are research opportunities, not problems to hide
- Quality over speed (though Express Mode available)

---

## Version History

### v1.1 - 2026-01-18
- **Express Mode** for short-form content (blog posts, news releases, policy briefs)
- **Validate Manuscript auto-handoff** at Phase 5 completion
- 56% time savings (45 min → 15-20 min) for Express Mode
- Lighter analysis with maintained quality gates
- Integration with validation suite for seamless quality assurance

### v1.0 - 2026-01-17
- Initial implementation
- 4-phase workflow (Ingest → Structure → Draft → Validate)
- Anti-pattern documentation
- Integration with LRA and RLM
