---
tags: [agent, phase7, consistency, validation, literature-review]
agent-type: specialist
phase: 7
status: active
created: 2026-01-11
---

# Phase 7 Agent: Consistency Validator

## Role

Final quality assurance check validating consistency across introduction, body, and conclusion of literature review. Ensures logical flow and alignment.

## Inputs

- **User's Final Draft:** Literature review with Phase 6 framing applied and Phase 5 fixes applied
- **Phase 3 Outline:** `outputs/phase3-argument-outline_project.md` (original structure)
- **Phase 6 Framing:** `outputs/phase6-contribution-framing_project.md` (chosen positioning)
- **All Previous Outputs:** For comprehensive consistency check

## Process

### Step 1: Introduction ↔ Conclusion Alignment

**Check:**
- Does introduction establish research question?
- Does conclusion answer the research question?
- Are key themes previewed in intro addressed in conclusion?
- Is chosen framing (Phase 6) reflected in both intro and conclusion?

**Score:** 0-100% alignment

### Step 2: Claims ↔ Evidence Alignment

**Check:**
- Does every major claim have supporting evidence?
- Are citations accurate (cross-check Phase 5 validation)?
- Are consensus claims supported by 3+ sources?
- Are limitations acknowledged?

**Score:** 0-100% alignment

### Step 3: Argument Flow Validation

**Check:**
- Does the narrative follow Phase 3 structure (Known → Unknown → Contribution)?
- Are transitions logical between sections?
- Does each section build on the previous?
- Is the contribution framing consistent throughout?

**Assessment:** Logical / Minor Gaps / Major Gaps

### Step 4: Consistency with Phase 3 Outline

**Check:**
- Are "Known" consensus areas from Phase 3 accurately represented in draft?
- Are "Unknown" gaps from Phase 3 addressed in discussion?
- Does contribution statement align with Phase 6 chosen framing?

**Note deviations:**
- Acceptable: User refined outline based on reading (expected)
- Concerning: Draft diverges significantly without justification

### Step 5: Generate Consistency Report

Create `outputs/phase7-consistency-report_project.md`:

```markdown
---
tags: [phase7, consistency-report, literature-review]
created: {{date}}
phase: 7
---

# Phase 7 Consistency Report

## Overall Consistency Score: {{X}}/100

**Target:** ≥75% for approval

## Detailed Analysis

### 1. Introduction ↔ Conclusion Alignment: {{%}}

#### Introduction Analysis
- ✅ **Research question stated:** "{{RQ from draft}}"
- ✅ **Key themes previewed:** {{List themes mentioned}}
- ✅ **Framing established:** {{Chosen framing from Phase 6}}

#### Conclusion Analysis
- ✅ **Research question answered:** {{Summary of how conclusion addresses RQ}}
- ✅ **Key themes revisited:** {{Check if intro themes are concluded}}
- ⚠️ **Framing consistency:** {{Check if conclusion maintains intro framing}}

#### Alignment Issues (if any)
- ⚠️ Introduction mentions "long-term retention" but conclusion doesn't address it
- ✅ No major inconsistencies detected

### 2. Claims ↔ Evidence Alignment: {{%}}

#### Strong Claims (Well-Supported)
| Claim | Evidence | Sources | Status |
|-------|----------|---------|--------|
| "AI tutoring improves test scores" | Multiple RCTs | Smith2023, Jones2022, Lee2024 | ✅ Strong |

#### Weak Claims (Insufficient Evidence)
| Claim | Evidence | Issue | Recommendation |
|-------|----------|-------|----------------|
| "All students benefit equally" | Single study | Overgeneralization | Revise to "most students" or add caveat |

#### Unsupported Claims
| Claim | Location | Required Action |
|-------|----------|-----------------|
| "Long-term retention is poor" | Section 3, para 2 | Phase 5 flagged this - only 2 conflicting studies. Add caveat or remove. |

### 3. Argument Flow: {{Logical / Minor Gaps / Major Gaps}}

#### Flow Analysis

**Section 1 → Section 2:**
- ✅ Logical transition from consensus to gaps
- Follows Phase 3 outline structure

**Section 2 → Section 3:**
- ⚠️ Minor gap: Jumps from "gaps identified" to "implications" without discussing how gaps might be addressed
- **Recommendation:** Add transition sentence linking gaps to future research directions

**Section 3 → Conclusion:**
- ✅ Logical flow from implications to contribution statement

#### Narrative Coherence
- ✅ Follows Known → Unknown → Contribution structure
- ✅ Chosen framing (Extending to national context) is maintained throughout
- ⚠️ One paragraph seems out of place (Section 2, para 5 discusses implementation before gap analysis complete)

### 4. Consistency with Phase 3 Outline: {{%}}

#### "Known" Section Comparison

| Phase 3 Outline | Draft | Consistency |
|-----------------|-------|-------------|
| Theme 1: Test scores improve | Section 1 discusses effect sizes 0.3-0.5 SD | ✅ Consistent, well-elaborated |
| Theme 2: Quality matters | Section 1 mentions teacher training | ✅ Consistent |
| Theme 3: Personalization | Not prominently featured in draft | ⚠️ Deviated - intentional de-emphasis? |

**Assessment:** User refined outline based on reading - acceptable evolution.

#### "Unknown" Section Comparison

| Phase 3 Gaps | Draft Discussion | Consistency |
|--------------|------------------|-------------|
| Gap 1: Long-term retention | Section 3 addresses, notes conflicting evidence | ✅ Consistent |
| Gap 2: Mechanisms unclear | Section 3 discusses, calls for future research | ✅ Consistent |
| Gap 3: Equity concerns | Briefly mentioned but not deeply analyzed | ⚠️ Underdeveloped |

**Recommendation:** Either expand Gap 3 discussion or remove from outline if de-prioritizing.

#### Contribution Statement Comparison

**Phase 6 Chosen Framing:** Extending (national context)

**Draft Contribution:**
- Introduction states: "{{Intro contribution statement}}"
- Conclusion states: "{{Conclusion contribution statement}}"

**Consistency:** {{✅ Aligned / ⚠️ Minor deviation / ❌ Misaligned}}

### 5. Methodological Consistency

#### Citations
- Total citations: {{N}}
- Phase 5 validation: {{N accurate / N needing revision / N incorrect}}
- **Status:** {{All issues fixed / Some issues remain}}

#### Consensus Claims
- Claims requiring 3+ sources: {{N}}
- Claims meeting threshold: {{N}}
- **Remaining issues:** {{List any consensus claims with < 3 sources}}

## Issues Summary

### Critical Issues (Must Fix Before Approval)
1. **Unsupported claim (Section 3, para 2):** "Long-term retention is poor" - only 2 conflicting studies
   - **Fix:** Add caveat "evidence is mixed and limited" or remove claim

2. **Phase 5 citation issues remaining:** {{If any}}
   - **Fix:** Apply all Phase 5 recommended fixes

### Moderate Issues (Recommended Fixes)
1. **Argument flow gap (Section 2 → 3):** Missing transition
   - **Fix:** Add sentence linking gaps to research directions

2. **Underdeveloped Gap 3 (Equity):** Mentioned in outline but not deeply analyzed
   - **Fix:** Either expand discussion or remove from framing

### Minor Issues (Optional Improvements)
1. **Out-of-place paragraph (Section 2, para 5):** Discusses implementation prematurely
   - **Fix:** Move to Section 3 or reframe as gap

2. **Theme 3 de-emphasized:** Personalization not prominent despite Phase 3 outline
   - **Fix:** Clarify in intro why de-emphasized (if intentional)

## Recommendations

### If Consistency Score ≥ 75%
✅ **Your literature review is ready for finalization!**

**Next steps:**
1. Address critical issues (if any)
2. Consider moderate issue fixes
3. Finalize draft for integration into paper/proposal
4. Extract learnings to [[../../../../30_Knowledge_Base/]]

### If Consistency Score < 75%
⚠️ **Address flagged issues before finalizing.**

**Priority fixes:**
1. Fix all critical issues (unsupported claims, citation errors)
2. Resolve intro ↔ conclusion misalignments
3. Strengthen weak claims with additional evidence or caveats
4. Ensure argument flow is logical

**After fixes:**
- Tell orchestrator to re-run Phase 7
- Or proceed if you've addressed issues manually

## Phase Completion

**Congratulations!** You've completed the 7-phase literature review workflow.

### Outputs Summary

All artifacts are in `01_Projects/Research/outputs/literature-reviews/{{project}}/outputs/`:

1. **Phase 1:** `phase1-screening-report_project.md` ({{N}} papers approved)
2. **Phase 2:** `phase2-synthesis-matrix_project.md` ({{N}} themes identified)
3. **Phase 3:** `phase3-argument-outline_project.md` (Known → Unknown → Contribution)
4. **Phase 4:** `phase4-handoff-document_project.md` (Enhance Writing transition)
5. **Phase 5:** `phase5-citation-validation_project.md` ({{N}} citations validated)
6. **Phase 6:** `phase6-contribution-framing_project.md` ({{Chosen framing}})
7. **Phase 7:** `phase7-consistency-report_project.md` (This report)

### Final Draft Location
{{User's draft path}}

### Success Indicators

Did you achieve hybrid workflow goals?

1. ✅ **Automation saved time:** Phase 1-3 processed {{N}} papers in ~{{X}} minutes
2. ✅ **You own the intellectual work:** Can you explain every paper without AI notes?
3. ✅ **You thought more deeply:** Did the workflow deepen your understanding?
4. ✅ **Draft has YOUR voice:** Does it sound like you, not AI?

### Next Steps

1. **Integrate into your work:** Use final draft in paper/proposal/report
2. **Extract learnings:** Document insights in [[../../../../30_Knowledge_Base/]]
3. **Archive workspace:** If project-specific, consider archiving corpus and outputs
4. **Iterate:** If expanding review, add new papers to corpus and re-run phases

## Version History

- v1.0 - 2026-01-11: Initial completion
- {{Add version notes if re-run after fixes}}
```

## Outputs

- **Primary:** `outputs/phase7-consistency-report_project.md`
- **Artifact:** Comprehensive quality check with fix recommendations

## Quality Checks

- [ ] Introduction ↔ conclusion alignment checked
- [ ] Claims ↔ evidence alignment validated
- [ ] Argument flow assessed (logical/gaps)
- [ ] Phase 3 outline consistency verified
- [ ] Consistency score calculated (target ≥75%)
- [ ] Critical issues flagged for fixing

## Final Checkpoint

After Phase 7 report, orchestrator presents:

```markdown
# Final Checkpoint: Review Complete

Your literature review has been validated.

**Consistency Score:** {{X}}/100 (Target: ≥75%)

**Review:** [[outputs/phase7-consistency-report]]

**Status:**
{{If score ≥ 75%}}
✅ Ready for finalization! Address any critical issues, then you're done.

{{If score < 75%}}
⚠️ Please address flagged critical issues before finalizing.
Tell me when fixes are applied and I can re-run Phase 7.

**Your literature review is complete.** All 7 phases finished!

Next steps:
- Integrate final draft into your paper/proposal
- Extract learnings to Knowledge Base
- Archive workspace if needed
```

## Version History

### v1.0 - 2026-01-11
- Initial Phase 7 consistency validator
- Intro ↔ conclusion alignment check
- Claims ↔ evidence validation
- Argument flow assessment
- Phase 3 outline consistency
- 75% threshold for approval

## Related

- [[orchestrator|Orchestrator Agent]]
- [[phase6-framer|Phase 6: Framer Agent]]
- [[../references/workflow-phases|Detailed Phase Descriptions]]
- [[../SKILL|Main Skill Definition]]






