---
tags: [reference, handoff, phase3-to-phase4, enhance-writing, literature-review]
created: 2026-01-11
---

# Phase 3→4 Handoff Guide

## Critical Transition Point

**This is the most important moment in the hybrid workflow.** Phase 3 (automated structuring) hands off to Phase 4 (human-led writing). Get this wrong, and you'll copy-paste AI output instead of doing intellectual work.

## What You Receive at Handoff

After Checkpoint 2 (approving Phase 3 outline), you receive:

### 1. Approved Corpus
**Location:** `corpus/approved/` ({{N}} papers)

**What it is:** PDFs that passed Phase 1 screening

**What it's NOT:** A summary you can cite without reading

**Your job:** READ THESE PAPERS YOURSELF
- Minimum per paper: Abstract + Conclusion + Sections you'll cite
- Use Phase 2 synthesis matrix as LENSES, not replacements
- Take your own notes: Claim, Evidence, Limitation, Connection

### 2. Synthesis Matrix
**Location:** `outputs/phase2-synthesis-matrix_project.md`

**What it is:** AI-extracted themes, claims, contradictions, gaps

**What it's NOT:** Your literature review (don't copy-paste)

**Your job:** Use as READING LENSES
- **Methodological lens:** What limitations did AI identify?
- **Consensus lens:** Where do papers agree/diverge?
- **Gap lens:** What questions remain?
- **Relevance lens:** How does each paper relate to MY question?

**Test:** Can you explain each theme without looking at synthesis matrix? If no, read papers yourself.

### 3. Argument Outline
**Location:** `outputs/phase3-argument-outline_project.md`

**What it is:** Logical structure (Known → Unknown → Contribution)

**What it's NOT:** A script to follow verbatim

**Your job:** CHALLENGE THIS OUTLINE
- Do you agree with "Known" consensus claims?
- Are "Unknown" gaps defensible based on YOUR reading?
- Does "Contribution" logically follow?
- Revise outline as your understanding deepens

**Test:** Would you defend this outline to a skeptical reviewer? If no, revise it.

## Before You Write: Critical Provocations

### Provocation 1: Understanding Check

**"Can I explain why each of the {{N}} papers matters for MY argument?"**

**How to test:**
1. Close all AI outputs
2. List papers from memory
3. For each paper, explain in 2-3 sentences:
   - What it claims
   - How it supports or challenges your argument
   - What its limitations are

**If you can't do this:** You haven't read the papers. Go back and read them.

**Why this matters:** If you can't explain papers without AI notes, you don't understand the corpus. You're plagiarizing AI, not synthesizing literature.

### Provocation 2: Gap Validation

**"Is the AI-identified gap actually a gap, or am I missing context?"**

**Phase 3 identified these gaps:**
- {{Gap 1 from outline}}
- {{Gap 2 from outline}}
- {{Gap 3 from outline}}

**How to test each gap:**
1. **Evidence check:** Do 0-2 papers address this? (= gap) Or do 5+ papers address it? (= not a gap)
2. **Significance check:** Why does this gap matter? Can you defend its importance?
3. **Domain expertise check:** Does your field knowledge reveal nuances AI missed?

**If AI's gap doesn't hold up:** Revise outline. You have domain expertise AI lacks.

**Why this matters:** AI can misidentify gaps by missing field-specific context. YOUR expertise is critical here.

### Provocation 3: Contribution Test

**"Does my proposed contribution logically follow from the evidence?"**

**Phase 3 proposed:**
"{{Contribution statement from outline}}"

**How to test:**
1. **Known → Gap logic:** Does the gap actually follow from what's known?
2. **Gap → Contribution logic:** Does my work actually address the gap?
3. **Skeptical reviewer test:** What would a critic say? Can I defend this?

**If contribution doesn't hold:**
- Revise contribution statement
- OR revise how you frame the gap
- OR choose different gap to address

**Why this matters:** Weak Known→Unknown→Contribution logic undermines your entire review.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Copy-Paste Synthesis

**What it looks like:**
```markdown
# My Literature Review Section 2

Theme 1: Learning Outcomes
AI tutoring systems improve short-term test scores. Smith (2023), Jones (2022), and Lee (2024) all found effect sizes of 0.3-0.5 SD in RCTs. However, effects vary by implementation quality, with teacher training mediating effectiveness (Wang et al., 2023; Chen, 2024).
```

**Why it's wrong:**
- This is verbatim from Phase 2 synthesis matrix
- You didn't add any analysis, interpretation, or YOUR voice
- A plagiarism detector would flag this as AI-generated

**How to fix:**
1. Read the papers yourself (Smith, Jones, Lee, Wang, Chen)
2. Synthesize in YOUR words based on YOUR reading
3. Add interpretation: "These findings suggest...", "A critical tension emerges..."
4. Challenge AI's framing if you disagree

**Correct version:**
```markdown
# My Literature Review Section 2

Recent experimental evidence consistently demonstrates that AI-powered tutoring systems produce moderate learning gains in K-12 mathematics (Smith, 2023; Jones, 2022; Lee, 2024). Effect sizes across these RCTs ranged from 0.3 to 0.5 standard deviations - comparable to traditional one-on-one human tutoring (Smith, 2023). However, this consensus masks significant implementation variability. Wang et al. (2023) found that teacher training explained more variance in outcomes than the AI system itself, suggesting that technology alone is insufficient. This aligns with Chen's (2024) observation that...
```

**Notice the difference:**
- Written in YOUR voice
- Adds interpretation ("this consensus masks...")
- Connects ideas ("This aligns with...")
- Shows you READ the papers, not just copied AI notes

### Anti-Pattern 2: Citing Without Reading

**What it looks like:**
> "Studies show that AI tutoring is effective (Smith, 2023; Jones, 2022; Lee, 2024; Brown, 2021; Garcia, 2023; Wilson, 2022; Park, 2024; Chen, 2024)."

**Why it's wrong:**
- Did you read all 8 papers? Or did you copy citations from Phase 2?
- Can you explain what each paper actually claims?
- This is academically dishonest

**How to test:**
Close Phase 2 synthesis matrix. For each citation, answer:
1. What specific claim does this paper make?
2. What evidence supports that claim (methodology, sample size, findings)?
3. What are its limitations?

**If you can't answer these:** You cited a paper you didn't read. Remove citation or read paper.

**Correct approach:**
Only cite papers you've actually read. If Phase 2 identified 8 relevant papers but you've only read 5, cite the 5. Quality > quantity.

### Anti-Pattern 3: Accepting AI's Framing

**What it looks like:**
Using Phase 3 outline structure verbatim without challenging it:
- Section 1: "Known" (exactly as AI wrote)
- Section 2: "Unknown" (exactly as AI wrote)
- Section 3: "Contribution" (exactly as AI wrote)

**Why it's wrong:**
- AI's framing may not be YOUR framing
- Your understanding will deepen as you read - outline should evolve
- You're letting AI make rhetorical choices for you

**How to fix:**
1. **Read papers first**
2. **Then revisit Phase 3 outline**
3. **Ask:** Do I agree with how AI framed this?
   - Would I structure "Known" differently?
   - Did AI miss a more important gap?
   - Is there a better contribution framing?
4. **Revise outline** based on YOUR reading

**Example revision:**
```markdown
Phase 3 AI Outline:
Known → Test scores improve
Unknown → Long-term retention unclear
Contribution → Synthesize evidence on retention

Your Revised Outline (after reading):
Known → Test scores improve SHORT-TERM
Unknown → Measurement problem (test scores ≠ learning)
Contribution → Reframe outcomes (what should we measure?)
```

**Notice:** You challenged AI's framing and proposed a stronger argument based on YOUR reading.

## What to Do Instead

### Do This 1: Use AI Synthesis to Organize YOUR Thinking

**Phase 2 says:** "Theme 1: Test scores improve"

**You do:**
1. Read all papers tagged under Theme 1
2. Organize YOUR notes using this theme as a lens
3. Add YOUR interpretation:
   - Do I agree these papers form a coherent theme?
   - Is there a sub-theme AI missed?
   - How would I frame this theme differently?

**Result:** AI gave you a starting point, but YOU did the intellectual work.

### Do This 2: Read Papers Through AI-Identified Lenses

**Phase 2 provides lenses:**
- Methodological lens
- Consensus lens
- Gap lens
- Relevance lens

**You use them:**
1. Read Smith (2023) through **methodological lens:** "What are limitations?"
   - You note: RCT but only 3-month follow-up
2. Read Jones (2022) through **consensus lens:** "Does this agree with Smith?"
   - You note: Yes, similar effect size, different population
3. Read Lee (2024) through **gap lens:** "Does this address long-term retention?"
   - You note: No, another short-term study

**Result:** AI's lenses guided your reading, but YOU extracted insights.

### Do This 3: Write YOUR Argument, Informed by Structure

**Phase 3 provides scaffold:**
```
Known: X
Unknown: Y
Contribution: Z
```

**You write:**
1. Draft Section 1 (Known) in YOUR voice
2. Revise Section 1 as understanding deepens
3. Challenge AI's "Known" if you disagree
4. Draft Section 2 (Unknown) based on YOUR gap analysis
5. Draft Section 3 (Contribution) aligned with YOUR goals

**Result:** You used AI's structure as a scaffold, not a script.

## Engaging Enhance Writing (Phase 4)

Now that you've read papers and challenged the outline, engage [[../../enhance-writing/references/academic-writing|Academic Writing Protocol]]:

### 1. Literature Engagement (Enhance Writing Phase 1)

**Your corpus is pre-screened, but YOU must read papers.**

- Use Phase 2 synthesis as lenses, not summaries
- Take synthesis-ready notes:
  - **Claim:** What does this paper argue?
  - **Evidence:** How is it supported?
  - **Limitation:** What doesn't it cover?
  - **Connection:** How does it relate to other papers?

### 2. Argument Construction (Enhance Writing Phase 2)

**Test AI-generated outline against YOUR reading.**

- Map: Known → Unknown → Contribution
- Challenge consensus claims:
  - Do 3+ papers REALLY support this?
  - Or did AI over-interpret?
- Test logical flow:
  - Does Unknown follow from Known?
  - Does Contribution address Unknown?

### 3. Handle Contradictions (Enhance Writing Phase 3)

**Phase 2 surfaced contradictions - don't smooth them over.**

Example from Phase 2:
> "Contradiction: Long-term retention effects mixed
> - Chen (2023): No effect at 6 months
> - Park (2024): Positive effect at 12 months"

**Your job:**
- Explain WHY they disagree (methodological, temporal, contextual)
- Take a position: Which finding is more reliable? Why?
- Or: Frame as unresolved debate requiring future research

### 4. Write Discussion (Enhance Writing Phase 4)

**After drafting literature review, write discussion:**

- **Interpretation:** What do findings mean?
- **Connection:** How do they relate to existing work?
- **Implication:** What should change (practice, policy, research)?
- **Limitation:** What can't I claim based on this evidence?

### 5. Self-Review (Enhance Writing Phase 5)

**Before submitting to Phase 6 (Contribution Framing):**

- **Understanding check:** Can I explain every paper without notes?
- **Argument check:** Does my review flow logically from question to answer?
- **Reviewer check:** Have I addressed obvious criticisms proactively?

After framing revisions, proceed to Phase 5 citation validation (full draft).

## How AI Will Support You (Provocation Mode)

During Phase 4, when you ask for help:

**You ask:** "Help me write the introduction"

**AI responds (Provocation Mode):**
> "Before I help with that—what's the single most important thing you want readers to understand from this introduction? Once you've articulated that, I can help you test different ways to open."

**You share draft section:**

**AI responds:**
> "You wrote 'Studies show AI tutoring is effective.' Which studies? Have you read them yourself, or are you citing from Phase 2 synthesis? Can you explain what each study found without looking at AI notes?"

**You cite a paper:**

**AI responds:**
> "You cite Park (2024) as showing long-term retention effects. But Phase 2 notes say Chen (2023) found NO retention effect. Have you read both papers? How do you reconcile this contradiction?"

**You accept outline uncritically:**

**AI responds:**
> "Phase 3 says the gap is 'long-term retention unclear.' Do YOU agree based on your reading? What would a skeptical reviewer say? Only 2 papers address retention - is that enough to claim a 'gap' or is it just understudied?"

## Success Indicators

### You're Doing It Right If:

1. ✅ You read approved papers yourself (not just AI summaries)
2. ✅ You challenged Phase 3 outline and revised it based on YOUR reading
3. ✅ You can explain any cited paper without AI notes
4. ✅ Your draft has YOUR voice, YOUR framing, YOUR interpretation
5. ✅ AI provocations helped you think deeper, not write faster
6. ✅ You finish having thought MORE deeply about the literature

### You're Misusing This If:

1. ❌ You copy-pasted Phase 2 synthesis into your draft
2. ❌ You cited papers you haven't read (just from Phase 2)
3. ❌ You accepted Phase 3 outline without challenging it
4. ❌ You can't explain papers without AI notes
5. ❌ Your draft reads like concatenated AI output
6. ❌ You asked AI to write sections for you (instead of provoke thinking)

## Test: Do You Own the Intellectual Work?

### Close all AI outputs. Answer these questions:

1. **Corpus understanding:**
   - List 5 key papers from memory
   - For each: What's the main claim? What evidence supports it? What are limitations?

2. **Gap validation:**
   - What's the most important research gap in this literature?
   - Why does it matter?
   - How would you defend its importance to a skeptical reviewer?

3. **Contribution clarity:**
   - What does your literature review contribute?
   - How does it fill the gap you identified?
   - What's your unique framing or insight?

4. **Framing ownership:**
   - How would you structure your literature review differently than Phase 3 outline?
   - What would you emphasize that AI didn't?
   - What did AI emphasize that you'd de-prioritize?

**If you can't answer these without looking at AI outputs:** You haven't done the intellectual work. Go back, read papers, challenge outline, THEN write.

**If you CAN answer these confidently:** You're ready for Phase 4 writing!

## Version History

### v1.0 - 2026-01-11
- Initial Phase 3→4 handoff guide
- Critical provocations before writing
- Anti-patterns and correct approaches
- Enhance Writing integration protocol
- Success indicators and tests

## Related

- [[../SKILL|Main Skill Definition]]
- [[../INTEGRATION|Hybrid Workflow Philosophy]]
- [[../README|Quick Start Guide]]
- [[phase3-structurer|Phase 3: Structurer Agent]]
- [[phase4-drafter|Phase 4: Drafter Support]]
- [[../../enhance-writing/references/academic-writing|Academic Writing Protocol]]
- [[workflow-phases|Detailed Phase Descriptions]]
- [[checkpoint-protocol|Checkpoint Protocol]]






