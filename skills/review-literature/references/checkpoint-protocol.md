---
tags: [reference, checkpoints, user-approval, literature-review]
created: 2026-01-11
---

# Checkpoint Protocol

Human approval points in the 7-phase workflow to ensure quality and alignment.

## Checkpoint Philosophy

**Why checkpoints?**
- Prevent AI from running unchecked
- Give user control at critical decision points
- Ensure user ownership of intellectual work
- Catch errors early before they cascade

**When to use checkpoints:**
- After phases that make critical decisions (corpus selection, outline structure)
- Before major transitions (automation → human-led)
- When user input determines next steps (framing choice)
- Final QA before completion

## 5 Checkpoints in Workflow

| Checkpoint | After Phase | Type | Purpose | Required Action |
|------------|-------------|------|---------|-----------------|
| **1** | Phase 1 (Screening) | Quality Gate | Approve corpus | Review report, move PDFs |
| **2** | Phase 3 (Structuring) | **HANDOFF** | Approve outline, transition to human-led | Challenge outline, read papers |
| **3** | Phase 4 (Drafting) | Continuous | Writing support | Engage with provocations |
| **4** | Phase 6 (Framing) | Choice Point | Choose positioning | Select framing option |
| **5** | Phase 7 (Consistency) | Final Review | Approve completion | Address issues, finalize |

---

## Checkpoint 1: Corpus Approval (After Phase 1)

### When
After Phase 1 screening report is generated.

### What You Receive
`outputs/phase1-screening-report_project.md` with:
- Summary statistics (total/approved/rejected/uncertain)
- Approved papers table with scores and justifications
- Rejected papers table with reasons
- Uncertain papers (edge cases) flagged

### Your Responsibilities

**1. Review Approved Papers**
- Are they actually relevant to your research question?
- Did AI apply screening criteria correctly?
- Any false positives (included but shouldn't be)?

**2. Check Rejected Papers (Sample)**
- Review 5-10 rejected papers
- Any false negatives (excluded but should be included)?
- If many false negatives, revise screening criteria and re-run

**3. Address Edge Cases**
- AI flagged uncertain papers for manual review
- For each: Include or Exclude based on your judgment
- Document decision for audit trail

**4. Move Approved PDFs**
From: `corpus/candidates/`
To: `corpus/approved/`

### Approval Criteria

✅ **Approve if:**
- Approved corpus size is manageable (5-100 papers)
- Screening criteria were applied consistently
- False positive/negative rate is acceptable (< 10%)
- Edge cases have been addressed

⚠️ **Revise if:**
- Corpus too small (< 5 papers): Relax screening criteria
- Corpus too large (> 100 papers): Tighten screening criteria
- Many false positives/negatives: Clarify screening criteria

❌ **Reject and re-run if:**
- AI completely misunderstood screening criteria
- > 20% of papers are incorrectly classified

### Proceeding to Phase 2

**Tell orchestrator:** "Approved. Proceed to Phase 2 (Extraction)."

---

## Checkpoint 2: Outline Approval (After Phase 3) **[CRITICAL HANDOFF]**

### When
After Phase 3 argument outline is generated.

**THIS IS THE MOST IMPORTANT CHECKPOINT** - marks transition from automated to human-led.

### What You Receive
`outputs/phase3-argument-outline_project.md` with:
- Research question
- Known section (consensus from Phase 2)
- Unknown section (gaps from Phase 2)
- Contribution statement
- Framing options for Phase 6
- Logical flow check

### Your Responsibilities

**1. Validate "Known" Section**
- Does it accurately reflect consensus?
- Are claims supported by 3+ papers?
- Any overstatements or misinterpretations?
- Would you defend these claims to a reviewer?

**2. Challenge "Unknown" Section**
- Are identified gaps defensible?
- Do they matter for your research direction?
- Any gaps AI missed due to lack of domain expertise?
- Are gaps actually connected to "Known" or arbitrary?

**3. Test Contribution Logic**
- Does Known → Unknown flow logically?
- Does your contribution actually address the gap?
- Is the framing aligned with your goals?
- Would a skeptical reviewer accept this structure?

**4. Revise Outline (If Needed)**
You are EXPECTED to revise the outline based on your domain expertise. This is a scaffold, not a script.

**Common revisions:**
- Reframe "Known" with different emphasis
- Add gaps AI missed
- Remove gaps that don't hold up
- Adjust contribution statement
- Change framing preference

### Approval Criteria

✅ **Approve if:**
- You agree with Known/Unknown/Contribution structure
- You can defend the outline to a skeptical reviewer
- Logical flow is sound (Known → Unknown → Contribution)
- You're ready to read papers and write based on this structure

⚠️ **Revise if:**
- Outline is mostly right but needs tweaks
- AI missed your domain-specific knowledge
- Framing doesn't match your goals

❌ **Major revision needed if:**
- AI fundamentally misunderstood the literature
- "Known" section has consensus claims not supported by evidence
- Gaps are not defensible
- Contribution doesn't follow from gaps

### Proceeding to Phase 4 (HANDOFF)

**Tell orchestrator:** "Approved (with revisions if applicable). Create handoff document."

**You then receive `outputs/phase4-handoff-document_project.md`** with:
- What you have (corpus, synthesis, outline)
- Critical provocations before writing
- Anti-patterns to avoid
- Enhance Writing protocol

**CRITICAL NEXT STEP:** Read [[handoff-guide|Phase 3→4 Handoff Guide]] before writing.

---

## Checkpoint 3: Drafting Support (During Phase 4)

### When
Throughout Phase 4 writing process (continuous, not discrete checkpoint).

### What You Receive
AI provocations in response to your writing progress:
- Challenges to claims
- Questions about citations
- Prompts to deepen thinking
- Alternatives without choosing for you

### Your Responsibilities

**1. Read Papers Yourself**
- Minimum per paper: Abstract + Conclusion + Cited sections
- Use Phase 2 synthesis as lenses, not replacements
- Can you explain each paper without AI notes?

**2. Write in YOUR Voice**
- Don't copy-paste Phase 2 synthesis
- Add YOUR interpretation and analysis
- Connect ideas in ways that reflect YOUR understanding

**3. Challenge Phase 3 Outline**
- Revise structure as your understanding deepens
- Don't treat outline as script
- Make it yours

**4. Engage with Provocations**
When AI asks: "Have you read this paper yourself?"
- If no: Read it before citing
- If yes: Explain claim without looking at AI notes

### This is NOT a Formal Checkpoint
No approval needed. You control the pace of Phase 4.

**When done drafting, tell orchestrator:** "Draft complete. Run Phase 6 (Contribution Framing)."

---

## Checkpoint 4: Framing Choice (After Phase 6)

### When
After Phase 6 contribution framing options are generated.

### What You Receive
`outputs/phase6-contribution-framing_project.md` with:
- 3 framing options (Supportive, Challenging, Extending)
- Trade-off analysis for each
- Decision matrix
- Recommendation

### Your Responsibilities

**1. Review Framing Options**
- **Option A (Supportive):** Extends existing work
  - Pros: Safe, builds on consensus
  - Cons: Less novelty
- **Option B (Challenging):** Questions assumptions
  - Pros: High impact if successful
  - Cons: Requires strong evidence
- **Option C (Extending):** Applies to new context
  - Pros: Practical relevance
  - Cons: Needs justification

**2. Consider Your Goals**
- **For Example Research Institute proposals:** Supportive or Extending likely best
- **For critical academic papers:** Challenging may be appropriate
- **For technical reports:** Supportive (evidence synthesis)

**3. Choose Framing**
Select option that aligns with:
- Your research goals
- Strength of your evidence
- Audience expectations
- Project context (proposal vs. paper vs. report)

**4. Revise Draft to Align**
Ensure intro and conclusion reflect chosen framing.

### Approval Criteria

✅ **Choose and proceed if:**
- Framing aligns with your goals
- You can defend the choice
- Draft is consistent with chosen framing

⚠️ **Revise draft if:**
- Current draft doesn't match chosen framing
- Need to adjust emphasis or tone

### Proceeding to Phase 5

**Tell orchestrator:** "I choose [Option A/B/C]. Proceed to Phase 5 (Citation Validation)."

---

## Checkpoint 5: Final Review (After Phase 7)

### When
After Phase 7 consistency report is generated.

### What You Receive
`outputs/phase7-consistency-report_project.md` with:
- Overall consistency score (0-100%, target ≥75%)
- Introduction ↔ Conclusion alignment analysis
- Claims ↔ Evidence alignment validation
- Argument flow assessment
- Critical/moderate/minor issues flagged
- Recommendations

### Your Responsibilities

**1. Review Consistency Score**
- **Score ≥ 75%:** Ready for finalization
- **Score < 75%:** Address flagged issues

**2. Address Critical Issues**
Must fix before finalizing:
- Unsupported claims
- Citation errors from Phase 5
- Introduction ↔ conclusion misalignments
- Logical gaps in argument flow

**3. Consider Moderate Issues**
Recommended but optional:
- Minor overstatements
- Underdeveloped sections
- Out-of-place paragraphs

**4. Optionally Address Minor Issues**
For polish:
- Wording improvements
- Transition smoothness
- Stylistic consistency

### Approval Criteria

✅ **Approve and finalize if:**
- Consistency score ≥ 75%
- All critical issues addressed
- You're satisfied with the draft

⚠️ **Fix and re-run Phase 7 if:**
- Score < 75%
- Critical issues remain
- Want validation after fixes

❌ **Major revision needed if:**
- Score < 50%
- Fundamental structural issues
- May need to revisit Phase 3 outline

### Completion

**Tell orchestrator:** "Approved. Literature review complete."

**All 7 phases are now finished.**

---

## Checkpoint Best Practices

### Do's
- ✅ Take time to review thoroughly (don't rush approvals)
- ✅ Challenge AI's analysis with your domain expertise
- ✅ Revise outputs (outline, framing) as needed
- ✅ Document your decisions (especially for edge cases)
- ✅ Ask clarifying questions if unsure

### Don'ts
- ❌ Rubber-stamp approvals without reviewing
- ❌ Accept AI's framing uncritically
- ❌ Skip reading papers during Checkpoint 2 handoff
- ❌ Ignore edge cases flagged by AI
- ❌ Proceed with low consistency score (< 75%)

### Resumption After Interruption

If you interrupt workflow mid-phase:

**To resume:**
1. Tell orchestrator: "Continue my literature review"
2. Orchestrator reads `outputs/execution-log.json`
3. Identifies last completed phase and pending checkpoint
4. Presents status: "Phase X complete, awaiting your approval at Checkpoint Y"
5. You review outputs and approve/revise
6. Workflow continues from next incomplete phase

---

## Version History

### v1.0 - 2026-01-11
- Initial checkpoint protocol documentation
- 5 checkpoints defined
- Approval criteria for each
- Best practices

## Related

- [[../SKILL|Main Skill Definition]]
- [[orchestrator|Orchestrator Agent]]
- [[workflow-phases|Detailed Phase Descriptions]]
- [[handoff-guide|Phase 3→4 Handoff Guide]]
- [[../INTEGRATION|Hybrid Workflow Philosophy]]






