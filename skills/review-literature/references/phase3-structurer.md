---
tags: [agent, phase3, structurer, argument, literature-review]
agent-type: specialist
phase: 3
status: active
created: 2026-01-11
---

# Phase 3 Agent: Argument Structurer

## Role

Builds a logical argument outline from synthesis matrix using the "Known → Unknown → Contribution" framework to create a scaffold for user's Phase 4 writing.

## Inputs

- **Synthesis Matrix:** `outputs/phase2-synthesis-matrix_project.md` with themes, claims, gaps
- **Research Question:** `settings/research-question.md` for contribution framing
- **Screening Report:** `outputs/phase1-screening-report_project.md` for corpus context

## Process

### Step 1: Extract "Known" (Consensus)

From Phase 2 synthesis matrix, identify what the field agrees on:

**Criteria for "Known":**
- 3+ papers support the claim
- Evidence is strong (RCTs, meta-analyses, replications)
- Consensus is recent (within last 5-7 years unless foundational)

**Structure:**
```
## Known (Consensus in the field)

### Theme 1: [Name]
- Finding: [Consensus statement]
  - Supporting papers: [Smith2023, Jones2022, Lee2024]
  - Evidence: [Methodological basis]
  - Strength: [Strong/Moderate]

### Theme 2: [Name]
[Repeat]
```

### Step 2: Extract "Unknown" (Research Gaps)

From Phase 2 gap analysis, identify what remains unanswered:

**Criteria for "Unknown":**
- Gap is defensible (not just "no one studied X" but "X matters because...")
- Gap relates to research question
- Gap can plausibly be addressed by research

**Structure:**
```
## Unknown (Research gaps)

### Gap 1: [Name]
- **What's missing:** [Description]
- **Why it matters:** [Significance for field or practice]
- **Related to known:** [How this gap connects to consensus areas]

### Gap 2: [Name]
[Repeat]
```

### Step 3: Map "Known → Unknown" Logical Flow

Ensure logical connection:

1. **Known establishes foundation:** "We know X (from Theme 1)"
2. **Unknown identifies limit:** "But we don't know Y (Gap 1)"
3. **Connection is explicit:** "Understanding Y is critical because [reason]"

**Check:**
- Does the gap actually follow from what's known?
- Or is the gap unrelated to consensus areas?
- If unrelated, can we reframe to create connection?

### Step 4: Frame "Your Contribution"

Based on research question + gaps, propose how user's work fills the gap:

**Framing options:**
1. **Supportive:** Extends existing work (builds on consensus)
2. **Challenging:** Questions assumptions (addresses contradictions)
3. **Extending:** Applies to new context (geographic, temporal, domain)

**Structure:**
```
## Contribution (Your work)

### Proposed Contribution
[One-sentence summary of what this literature review accomplishes]

### How It Fills the Gap
- **Addresses:** [Specific gap from "Unknown"]
- **Method:** [How your review synthesizes evidence]
- **Value:** [What the field gains from this contribution]

### Framing
[Preliminary framing - will be refined in Phase 6]
- Option A: Supportive (extends Theme X)
- Option B: Challenging (reconciles Contradiction Y)
- Option C: Extending (applies to context Z)
```

### Step 5: Generate Argument Outline

Create `outputs/phase3-argument-outline_project.md`:

```markdown
---
tags: [phase3, argument-outline, literature-review]
created: {{date}}
phase: 3
---

# Phase 3 Argument Outline

## Research Question
{{User's research question from settings/research-question.md}}

## Argument Structure: Known → Unknown → Contribution

### Known (Consensus in the field)

#### Theme 1: Learning Outcomes
- **Finding:** AI tutoring systems improve short-term test scores in mathematics
  - Supporting papers: Smith (2023), Jones (2022), Lee (2024), Wang et al. (2023)
  - Evidence: Multiple RCTs with effect sizes 0.3-0.5 SD
  - Strength: Strong (replicated across contexts)

- **Finding:** Effects vary by implementation quality
  - Supporting papers: Wang et al. (2023), Chen (2024), Park (2022)
  - Evidence: Quasi-experimental studies show teacher training mediates effectiveness
  - Strength: Moderate (correlational, needs experimental validation)

#### Theme 2: AI Features
- **Finding:** Personalization features correlate with student engagement
  - Supporting papers: Chen (2024), Park (2022), Garcia (2023)
  - Evidence: Mixed methods showing adaptive scaffolding increases time-on-task
  - Strength: Moderate (engagement ≠ learning)

#### Theme 3: Student Characteristics
- **Finding:** Prior knowledge moderates AI tutoring effectiveness
  - Supporting papers: Lee (2024), Wilson (2023)
  - Evidence: Regression analyses show interaction effects
  - Strength: Weak (only 2 studies, needs replication)

### Unknown (Research gaps)

#### Gap 1: Long-term Retention
- **What's missing:** Most studies measure outcomes < 6 months post-intervention
- **Why it matters:** Short-term test score gains may not reflect durable learning
- **Evidence of gap:**
  - Only 2/23 papers measured retention beyond 6 months
  - Chen (2023): No effect at 6 months
  - Park (2024): Positive effect at 12 months (conflicting)
- **Related to known:** Contradicts assumption that test score improvements = learning

#### Gap 2: Mechanisms Unclear
- **What's missing:** "Black box" problem - we know WHAT works but not WHY
- **Why it matters:** Without mechanisms, can't optimize design or predict failures
- **Evidence of gap:**
  - Personalization correlates with engagement (Theme 2)
  - But which features drive learning vs. engagement?
  - No studies decompose "AI tutoring" into feature components
- **Related to known:** Limits ability to scale effective implementations (Theme 1)

#### Gap 3: Equity Concerns
- **What's missing:** Limited evidence on SES or language minority students
- **Why it matters:** AI tutoring may exacerbate or ameliorate achievement gaps
- **Evidence of gap:**
  - Only 3/23 papers report SES breakdowns
  - No papers on English language learners
  - Equity implications untested
- **Related to known:** Effectiveness may not generalize across populations

### Contribution (Your work)

#### Proposed Contribution
This review synthesizes 23 empirical studies to identify success factors for AI-powered tutoring systems in K-12 mathematics education and highlight critical research gaps for future work.

#### How It Fills the Gap
- **Addresses:** All three gaps (retention, mechanisms, equity)
- **Method:** Systematic synthesis across 23 studies (2018-2025)
- **Value:**
  - Clarifies what's known (short-term effectiveness) vs. what's assumed (long-term learning)
  - Surfaces "black box" problem to guide future research
  - Flags equity concerns for policymakers and researchers

#### Framing Options (To Refine in Phase 6)

**Option A: Supportive (Recommended)**
- Position: This review **extends** existing meta-analyses by focusing on implementation quality and mechanisms
- Narrative: "While we know AI tutoring works, this review identifies HOW to make it work better"
- Best for: Project proposals (Example Research Institute Project Atlas), grant applications

**Option B: Challenging**
- Position: This review **questions** assumptions about AI tutoring effectiveness by highlighting gaps in long-term evidence
- Narrative: "Short-term test scores ≠ durable learning - the field needs to rethink outcome measures"
- Best for: Critical academic papers, research essays

**Option C: Extending**
- Position: This review **applies** AI tutoring evidence to a target-country K-12 context, identifying local adaptation needs
- Narrative: "Evidence from US/China contexts may not transfer - here's what we need to study locally"
- Best for: Example Research Institute project design, regional policy recommendations

## Logical Flow Check

1. **Known → Unknown Connection:**
   - ✅ Gap 1 (retention) challenges Known Theme 1 (test scores)
   - ✅ Gap 2 (mechanisms) limits scaling Known Theme 1 (implementation quality)
   - ✅ Gap 3 (equity) questions generalizability of Known across populations

2. **Unknown → Contribution Connection:**
   - ✅ Contribution addresses all 3 gaps through systematic synthesis
   - ✅ Value proposition is clear (clarify assumptions, guide future research)
   - ✅ Framing aligns with user's likely goals (Example Research Institute project)

3. **Consistency with Research Question:**
   - ✅ Research question asks "How do AI systems impact learning?"
   - ✅ Known answers short-term impacts
   - ✅ Unknown highlights long-term / mechanisms / equity unanswered
   - ✅ Contribution synthesizes evidence to inform Project Atlas project design

## Next Steps (Phase 4 Handoff)

**CRITICAL:** This outline is a SCAFFOLD, not a SCRIPT.

Before writing:
1. **Challenge this outline:** Do you agree with the Known/Unknown/Contribution structure?
2. **Read papers yourself:** Don't rely solely on Phase 2 synthesis matrix
3. **Revise as needed:** Your understanding will deepen as you read
4. **Use Enhance Writing:** Engage academic writing protocol for Phase 4

The handoff document will guide you through this transition.
```

## Outputs

- **Primary:** `outputs/phase3-argument-outline_project.md`
- **Artifact:** Logical argument structure (Known → Unknown → Contribution)

## Quality Checks

- [ ] "Known" section cites 3+ papers per consensus claim
- [ ] "Unknown" gaps are defensible and significant
- [ ] Logical flow: Known → Unknown connection is explicit
- [ ] Logical flow: Unknown → Contribution connection is clear
- [ ] Contribution aligns with research question
- [ ] Framing options provided for Phase 6
- [ ] Outline structure is clear and scannable

## Edge Cases & Limitations

### Handles Well
- Multiple themes (organizes logically)
- Contradictions (can frame as gap to be resolved)
- Unclear gaps (provides multiple gap options for user to choose)

### Known Limitations
- **Framing bias:** AI may favor one framing over others based on corpus
  - Workaround: Provide 3 framing options, user chooses in Phase 6
- **Logical leaps:** AI may claim Known → Unknown connection that doesn't hold
  - Workaround: User challenges outline in Checkpoint 2
- **Missing user context:** AI doesn't know user's actual goals (proposal vs. paper vs. thesis)
  - Workaround: Framing options allow user to align with their goals

## Prompt Template

The reusable prompt for this phase is defined inline in this agent file (see the sections above).

## Error Handling

### Error: Can't Identify Clear Gap

**Detection:** Phase 2 synthesis matrix don't reveal obvious gaps

**Action:**
1. Present multiple possible gaps in Unknown section
2. Ask user: "Which gap aligns with your research direction?"
3. User selects gap or provides their own

### Error: Known Section Too Thin

**Detection:** < 3 consensus areas identified

**Action:**
1. Note limitation: "Corpus shows little consensus - field may be emerging"
2. Adjust structure: Shift from "Known → Unknown" to "Debated → Contribution"
3. Frame contribution as "synthesizing contested evidence"

### Error: Contribution Doesn't Follow from Gap

**Detection:** Logical flow check fails

**Action:**
1. Flag inconsistency in outline
2. Provide alternative contribution framings
3. Ask user to clarify how their work addresses the gap

## Version History

### v1.0 - 2026-01-11
- Initial Phase 3 structurer agent
- Known → Unknown → Contribution framework
- Logical flow validation
- Framing options for Phase 6
- Scaffold vs. script distinction

## Related

- [[orchestrator|Orchestrator Agent]]
- [[phase2-extractor|Phase 2: Extractor Agent]]
- [[phase4-drafter|Phase 4: Drafter Support]]
- [[../references/workflow-phases|Detailed Phase Descriptions]]
- [[../references/handoff-guide|Phase 3→4 Handoff Guide]]






