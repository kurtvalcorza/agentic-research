# Phase Logic

Detailed workflow logic for each phase of write-manuscript skill.

---

## Phase 1: Source Synthesis

### Objective
Understand research notes and identify the single most important contribution.

### Process Steps

**Step 1: Read Research Notes**
- Use `Read` tool to ingest all provided research notes
- Notes may come from: LRA outputs, manual notes, AI summaries from other tools
- Build internal understanding of source material

**Step 2: Identify Core Elements**

Extract three critical elements:

1. **Knowns** - What sources agree on
   - Established facts
   - Consensus findings
   - "State of the art"

2. **Gaps** - What remains unaddressed
   - Unanswered questions
   - Missing evidence
   - Unexplored areas

3. **Key Claims** - Central arguments in sources
   - Main theses
   - Core contributions
   - Competing positions

**Step 3: Contribution Test**

**Critical question:**
> "What is the **single most important contribution** this manuscript makes? If I deleted this paper, what knowledge would be lost?"

**Express Mode variation:**
> "What's the one thing you want readers to take away?"

### Checkpoint

**User must articulate contribution before proceeding.**

This is a BLOCKING checkpoint. If user cannot articulate contribution:
- Re-read sources together
- Identify what makes this work unique
- Distinguish between "summary" and "synthesis"

### Mode-Specific Variations

**Full Mode:**
- Deep read of all notes
- Comprehensive tension analysis
- Extensive contribution articulation

**Express Mode:**
- Quick scan for main points
- Skip deep tension analysis
- Simple contribution test

### Outputs
- Internal understanding of source material
- Identified knowns, gaps, and claims
- User-articulated contribution statement

---

## Phase 2: Argument Structuring

### Objective
Transform source understanding into argumentative structure.

### Framework: Known → Gap → Contribution

**Structure:**
1. **Known** - What's established (from sources)
2. **Gap** - What's missing (from analysis)
3. **Contribution** - What this work adds (from user)

### Process Steps

**Step 1: Map Consensus**

Questions to answer:
- What do ALL your notes agree on?
- What's the established "state of the art"?
- Where is there convergence in findings?

**Output:** Consensus statements

---

**Step 2: Identify Tensions**

**Critical rule:** Don't smooth over disagreements

Questions to answer:
- Where do your notes disagree?
- What contradictions exist?
- What alternative explanations are offered?

**Tensions are research opportunities:**
- Unresolved tensions = gaps
- Your contribution may adjudicate tensions
- Highlighting tensions strengthens argument

**Output:** Tension statements

---

**Step 3: Scaffold Outline**

Create `manuscript-outline.md` using template.

**Outline Structure:**
```markdown
# Manuscript Outline

## 1. Introduction
**Argument:** Establish problem space and significance
**Key claim:** [What reader believes after intro]

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

**Each section must:**
- Advance the argument (not just present info)
- Have explicit key claim
- Build on previous section
- Set up next section

### Mode-Specific Variations

**Full Mode:**
- Complete consensus mapping
- Detailed tension identification and analysis
- Full outline scaffolding with section-level claims

**Express Mode:**
- Quick consensus mapping
- Outline without deep tension analysis
- Focus on main argument flow

### Outputs
- `manuscript-outline.md` with section-level arguments

---

## Phase 3: Interactive Drafting

### Objective
Transform outline into manuscript prose while maintaining quality.

### Core Pattern: Challenge-Before-Assist

**Workflow:**
1. User requests help with section
2. Present alternative framings or clarifying challenge
3. User adjudicates or responds
4. Assist with drafting based on user's position
5. Continue challenging assumptions as needed

### Drafting Logic

**Section-by-Section Approach:**
- Draft one section at a time
- Create `[section]-draft.md` for each
- Require user input on argumentation
- Verify claims trace to sources

**Alternative Framing Presentation:**

When multiple framings possible, present options:
- Identify 2-3 alternative framings
- Explain implications of each
- Require user to choose

**Example:**
> "Looking at your notes, I see two possible framings:
> 1. Efficiency framing: Current systems waste X resources
> 2. Access framing: Current systems exclude Y populations
>
> Which story do you want to tell? Each leads to different 'gaps' and 'contributions.'"

### Tension Adjudication Requirement

**When sources disagree:**
- Highlight the tension explicitly
- DO NOT smooth over disagreement
- Require user to take a position

**Example:**
> "Note 1 says [A], Note 3 says [not-A]. Your manuscript needs to adjudicate. Which stance are you taking?"

### Source Traceability

**Every claim must trace to input sources:**
- Verify claims during drafting
- Flag untraceable claims immediately
- Warn on outside sources

### Mode-Specific Variations

**Full Mode:**
- Continuous challenge and provocation
- Deep assumption surfacing
- Multiple alternative framings presented
- Thorough adjudication required

**Express Mode:**
- 1-2 key challenges per section (not continuous)
- Focus on: (1) Key claim accuracy, (2) Evidence support
- Skip deep assumption surfacing
- Faster iteration

### Outputs
- `[section]-draft.md` for each section
- `manuscript-draft.md` (complete manuscript)

---

## Phase 4: Quality Gates

### Objective
Verify manuscript meets quality standards before validation.

### Citation Check

**Rules:**
1. **Stick to sources in input notes**
   - Every claim must trace to provided sources
   - Flag claims without source support

2. **Warn on outside sources**
   - If user introduces claim not in input notes
   - Require explicit acknowledgment

3. **Flag untraceable claims**
   - Any claim that cannot be traced to a source
   - Must be removed or source must be added

**Process:**
- Review manuscript-draft.md line by line
- Cross-reference each claim with input notes
- Create citation-check.md with findings

---

### Consistency Check

**Rules:**
1. **Conclusion matches Introduction**
   - Conclusion addresses problems raised in intro
   - Promised contributions are delivered
   - Framing is consistent

2. **Gap matches Contribution**
   - Identified gap aligns with proposed contribution
   - Contribution logically addresses the gap
   - No gap-invention to fit contribution

3. **Terminology consistency**
   - Same terms used uniformly throughout
   - Key concepts defined once, used consistently
   - No unexplained terminology shifts

**Process:**
- Compare introduction and conclusion
- Verify gap-contribution alignment
- Check terminology usage
- Update citation-check.md with consistency findings

---

### Quality Checklist Verification

**Before Writing:**
- [x] User articulated single most important contribution
- [x] Tensions in sources identified
- [x] User adjudicated contradictions (not ignored)

**During Writing:**
- [x] Every claim traces to source in input notes
- [x] User actively thinking (not just accepting)
- [x] Argument advances in each section

**After Writing:**
- [x] Conclusion matches Introduction
- [x] Contribution addresses stated Gap
- [x] No hallucinated citations
- [x] Limitations acknowledged

### Outputs
- `citation-check.md` (verification report)
- Quality gate pass/fail status

---

## Phase 5: Validation Handoff

### Objective
Auto-invoke comprehensive validation suite for deeper analysis.

### Handoff Logic

**Trigger:**
After Phase 4 quality gates pass, auto-offer validation.

**Validation Options:**

**Option 1: Full Validation (Recommended)**
- Run complete validate-manuscript skill
- 4-skill validation sequence
- ~5 minutes
- Consolidated report

**Option 2: Quick Validation**
- Citations + consistency only
- ~2 minutes
- Lighter report

**Option 3: Skip Validation**
- Export as-is
- Not recommended for publication

### Pre-Population

**Files automatically passed to validate-manuscript:**
- `manuscript-draft.md` (from Phase 3)
- `synthesis-notes.md` (from LRA or input)
- `manuscript-outline.md` (from Phase 2)

### Validation Execution

**validate-manuscript runs 4 skills in sequence:**
1. Citation validation
2. Evidence checking
3. Contribution validation
4. Consistency verification

### Results Interpretation

**Overall Score:** X/100

**Status Categories:**
- **PASS** - Ready for submission
- **NEEDS ATTENTION** - Review validation-report.md, address issues
- **FAIL** - Critical issues, do not proceed to submission

### Next Steps Logic

**If PASS:**
- Manuscript ready for submission
- Proceed to export (DOCX, PDF, LaTeX)

**If NEEDS ATTENTION:**
- Review `validation-report.md`
- Address flagged issues
- Re-run validation (can loop)

**If FAIL:**
- Address critical issues before proceeding
- Review detailed sub-reports in `validation/`
- Fix issues and re-validate
- Do not submit until PASS

### Outputs
- `validation-report.md` (consolidated score and findings)
- `validation/*.md` (detailed sub-reports)
- Pass/Fail/Needs-Attention status

---

## Cross-Phase Dependencies

### Phase Flow
```
Phase 1 (Source Synthesis)
  ↓ [Contribution statement]
Phase 2 (Argument Structuring)
  ↓ [manuscript-outline.md]
Phase 3 (Interactive Drafting)
  ↓ [manuscript-draft.md]
Phase 4 (Quality Gates)
  ↓ [citation-check.md + pass status]
Phase 5 (Validation Handoff)
  ↓ [validation-report.md]
```

### Blocking Checkpoints

**Phase 1 → Phase 2:**
- User MUST articulate contribution before proceeding

**Phase 2 → Phase 3:**
- Outline MUST be created (manuscript-outline.md)

**Phase 3 → Phase 4:**
- Complete draft MUST exist (manuscript-draft.md)

**Phase 4 → Phase 5:**
- Quality gates MUST pass (citation + consistency checks)

---

## Error Handling

### Common Issues

**Issue: User cannot articulate contribution (Phase 1)**
- Re-read sources together
- Identify unique aspects of this work
- Distinguish summary from synthesis
- Loop until contribution clear

**Issue: Tensions not adjudicated (Phase 2)**
- Highlight specific tensions
- Require user to take position
- DO NOT proceed until adjudicated

**Issue: Untraceable claims (Phase 4)**
- Flag specific claims
- Require source or removal
- DO NOT proceed to validation until resolved

**Issue: Quality gates fail (Phase 4)**
- Identify specific failures
- Require fixes before Phase 5
- Can loop back to Phase 3 if needed

---

## Version History

### v1.1 - 2026-01-18
- Express Mode introduced
- Lighter provocation in Express Mode
- Maintained quality gates across both modes
