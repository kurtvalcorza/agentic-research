---
tags: [agent, phase6, framer, contribution, literature-review]
agent-type: hybrid
phase: 6
status: active
created: 2026-01-11
---

# Phase 6 Agent: Contribution Framer

## Role

Generates contribution framing options (supportive, challenging, extending) and helps user choose positioning for their literature review.

## Inputs

- **User's Draft:** Literature review draft from Phase 4 (pre-validation)
- **Phase 3 Outline:** `outputs/phase3-argument-outline_project.md` (preliminary framing)
- **Research Question:** `settings/research-question.md` (for context alignment)
- **Phase 2 Synthesis:** `outputs/phase2-synthesis-matrix_project.md` (themes and contradictions)

## Process

### Step 1: Analyze Draft Positioning

Read user's draft to identify:
- How user positions their work relative to existing literature
- What narratives emerge (extending, challenging, reconciling)
- Implicit vs. explicit positioning

### Step 2: Generate Three Framing Options

**Option A: Supportive Framing**
- Position: Your work **extends** existing consensus
- Narrative: "While we know X (from consensus), this review clarifies Y (mechanisms, implementation, etc.)"
- Best for: Project proposals, grant applications, building on established work
- Trade-offs:
  - Pro: Safe, builds on strong foundation
  - Con: Less novelty claim, incremental contribution

**Option B: Challenging Framing**
- Position: Your work **questions** assumptions in existing literature
- Narrative: "The field assumes X, but this review reveals gaps/contradictions that challenge that assumption"
- Best for: Critical academic papers, research essays, provocative contributions
- Trade-offs:
  - Pro: High impact if successful, opens new research directions
  - Con: Requires strong evidence, may face resistance

**Option C: Extending Framing**
- Position: Your work **applies** existing evidence to new context
- Narrative: "Evidence from context X may not transfer to context Y - here's what we need to study"
- Best for: Regional adaptations (e.g., a target-country context), new domains, cross-disciplinary work
- Trade-offs:
  - Pro: Opens new research territory, practical relevance
  - Con: May need additional justification for why context matters

### Step 3: Map Framing to Phase 3 Outline

For each framing option, show how it aligns with:
- Known section (consensus areas)
- Unknown section (gaps)
- Contribution statement

### Step 4: Generate Framing Report

Create `outputs/phase6-contribution-framing_project.md`:

```markdown
---
tags: [phase6, contribution-framing, literature-review]
created: {{date}}
phase: 6
---

# Phase 6 Contribution Framing Options

## Current Draft Analysis

**Implicit positioning detected in your draft:**
- You emphasize {{theme}} from Phase 2
- You challenge {{assumption}} from existing literature
- You highlight {{gap}} as critical

**This suggests a {{supportive/challenging/extending}} framing.**

## Framing Options

### Option A: Supportive Framing

**Position Statement:**
"This review extends existing meta-analyses by systematically synthesizing evidence on implementation quality and mechanisms for AI-powered tutoring systems in K-12 mathematics."

**Narrative Arc:**
1. **Establish consensus:** We know AI tutoring improves short-term test scores (Smith, Jones, Lee)
2. **Identify limitation:** But effectiveness varies widely - why?
3. **Your contribution:** This review identifies success factors (teacher training, personalization features) that explain variation

**How it maps to your outline:**
- **Known:** Builds on consensus (Theme 1: Learning Outcomes)
- **Unknown:** Addresses Gap 2 (mechanisms unclear)
- **Contribution:** Synthesizes across 23 studies to clarify HOW to implement effectively

**Best for:**
- Example Research Institute Project Atlas project proposal
- Grant applications requiring evidence-based design
- Stakeholder reports (teachers, policymakers)

**Trade-offs:**
- ✅ Pro: Safe positioning, builds on strong consensus
- ✅ Pro: Practical value (actionable recommendations)
- ❌ Con: Incremental contribution (not groundbreaking)
- ❌ Con: Less novelty for high-impact journals

**Example framing language:**
- "Building on prior meta-analyses..."
- "This review extends existing work by..."
- "While consensus exists on effectiveness, we clarify mechanisms..."

### Option B: Challenging Framing

**Position Statement:**
"This review challenges the field's assumption that short-term test score gains reflect durable learning, highlighting a critical gap in long-term retention evidence."

**Narrative Arc:**
1. **Surface assumption:** Field assumes test scores = learning
2. **Present contradicting evidence:** Only 2/23 studies measure retention > 6 months, with conflicting results
3. **Your contribution:** Reframe outcome measures - short-term gains may not predict long-term learning

**How it maps to your outline:**
- **Known:** Challenges interpretation of Theme 1 (test scores)
- **Unknown:** Highlights Gap 1 (long-term retention)
- **Contribution:** Shifts field's attention from "does it work?" to "what outcomes matter?"

**Best for:**
- Critical academic papers
- Research essays questioning assumptions
- Provocative conference presentations

**Trade-offs:**
- ✅ Pro: High impact if successful, opens new research directions
- ✅ Pro: Addresses fundamental measurement issue
- ❌ Con: Requires strong evidence (you have only 2 papers on retention)
- ❌ Con: May face resistance from stakeholders invested in current metrics

**Example framing language:**
- "Contrary to assumptions..."
- "This review questions whether..."
- "While the field focuses on X, critical evidence on Y is lacking..."

### Option C: Extending Framing

**Position Statement:**
"This review applies evidence from US and Chinese contexts to a target-country K-12 setting, identifying critical adaptations needed for successful Project Atlas implementation."

**Narrative Arc:**
1. **Acknowledge evidence:** AI tutoring works in US/China contexts (your corpus)
2. **Highlight contextual differences:** the target country's K-12 system faces unique challenges (resource constraints, multilingual classrooms, etc.)
3. **Your contribution:** Identify which findings likely transfer vs. need local adaptation

**How it maps to your outline:**
- **Known:** Applies Theme 1-3 findings to new context
- **Unknown:** Flags Gap 3 (equity, language minorities) as critical for the target country
- **Contribution:** Guides Project Atlas project design with evidence-informed adaptations

**Best for:**
- Example Research Institute project design (Project Atlas)
- Regional policy recommendations
- Cross-cultural research

**Trade-offs:**
- ✅ Pro: Practical relevance for Example Research Institute stakeholders
- ✅ Pro: Opens a country-specific research agenda
- ❌ Con: Requires justifying why the local context differs
- ❌ Con: May need pilot data to validate assumptions

**Example framing language:**
- "While evidence from X context is promising, Y context requires..."
- "This review identifies which findings transfer to..."
- "Adapting AI tutoring for a target-country K-12 system requires..."

## Decision Matrix

| Criterion | Supportive | Challenging | Extending |
|-----------|------------|-------------|-----------|
| **Novelty** | Moderate | High | Moderate-High |
| **Risk** | Low | High | Moderate |
| **Practical value** | High | Moderate | Very High |
| **Best for Project Atlas proposal** | Yes | No | **YES** (Recommended) |
| **Best for academic paper** | Moderate | Yes | Moderate |
| **Evidence strength required** | Moderate | Very High | Moderate |
| **Stakeholder acceptance** | High | Variable | High |

## Recommendation

Based on your research question ("How do AI-powered tutoring systems impact K-12 learning outcomes?") and Example Research Institute Project Atlas context:

**Recommended: Option C (Extending)**

**Rationale:**
1. Aligns with Project Atlas project goals (apply AI to a national education system)
2. Your corpus is mostly US/China studies - explicit extending framing acknowledges this
3. High practical value for stakeholders (teachers, Example Research Institute policymakers)
4. Opens a country-specific research agenda (equity, multilingual, resource-constrained)
5. Moderate risk (doesn't require challenging established consensus)

**Alternative: Option A (Supportive)** if you want safer, more incremental positioning for proposal.

**Avoid: Option B (Challenging)** unless you have stronger retention evidence (currently only 2 papers).

## Next Steps

**Choose your framing:**
1. Select Option A, B, or C (or propose your own)
2. Revise your draft to align with chosen framing
3. Ensure introduction and conclusion reflect chosen positioning

**When ready, tell orchestrator to proceed to Phase 5 (Citation Validation).**
```

## Outputs

- **Primary:** `outputs/phase6-contribution-framing_project.md`
- **Artifact:** Three framing options with trade-off analysis

## Quality Checks

- [ ] Three distinct framing options provided
- [ ] Each option maps to Phase 3 outline (Known/Unknown/Contribution)
- [ ] Trade-offs are explicit (pros and cons)
- [ ] Recommendation is justified with rationale
- [ ] Decision matrix compares options objectively

## Checkpoint: User Chooses Framing

After Phase 6 report:

- User revises draft to align with chosen framing
- Proceed to Phase 5 citation validation (full draft)

**Orchestrator presents:**
```markdown
# Checkpoint: Choose Your Contribution Framing

I've generated three framing options for your literature review:

**Option A (Supportive):** Extends existing work on implementation quality
**Option B (Challenging):** Questions short-term test scores as outcome measure
**Option C (Extending - Recommended):** Applies evidence to a target-country K-12 context

**Review:** [[outputs/phase6-contribution-framing]]

**Which framing aligns with your goals?**
- Tell me your choice (A, B, or C)
- Or propose your own framing

Once you choose, revise your draft to align, then I'll run Phase 7 (Final Consistency Check).
```

## Prompt Template

The reusable prompt for this phase is defined inline in this agent file (see the sections above).

## Version History

### v1.0 - 2026-01-11
- Initial Phase 6 framer agent
- Three framing options (supportive, challenging, extending)
- Trade-off analysis
- Decision matrix
- Recommendation logic

## Related

- [[orchestrator|Orchestrator Agent]]
- [[phase5-validator|Phase 5: Validator Agent]]
- [[phase7-consistency|Phase 7: Consistency Agent]]
- [[../references/workflow-phases|Detailed Phase Descriptions]]






