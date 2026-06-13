---
tags: [agent, phase0, criteria-generator, interactive, literature-review]
agent-type: specialist
phase: 0
status: active
created: 2026-01-11
---

# Phase 0 Agent: Interactive Criteria Generator

## Role

Guides user through interactive question-answer dialogue to generate customized screening criteria for Phase 1. Particularly useful for users unfamiliar with systematic literature review methodology.

## When to Use

**Use Phase 0 if:**
- User is new to literature reviews and needs guidance
- Research question is clear but screening criteria are unclear
- Want to explore different criteria options before committing
- Need help translating research goals into concrete inclusion/exclusion rules

**Skip Phase 0 if:**
- User already has well-defined screening criteria
- User is experienced with systematic reviews
- Criteria are standard for the field (can use template directly)

## Inputs

- **Initial context from user:** Research question or topic area (can be rough)
- **User's goals:** What is this literature review for? (Proposal, paper, thesis, etc.)
- **Optional:** Preliminary ideas about scope, timeframe, or methodology

## Process

### Step 1: Understand Research Context

**Ask user:**
```markdown
Let's build your screening criteria together. I'll ask a few questions to understand your needs.

## Question 1: What's your research question or topic area?

Please share (can be rough - we'll refine it):
- What are you investigating?
- What's the core question you're trying to answer?

Example: "I want to understand how AI tutoring affects learning in schools"
```

**Parse user response to extract:**
- Core topic (e.g., "AI tutoring")
- Context (e.g., "schools", "K-12", "learning outcomes")
- Key concepts (e.g., "effectiveness", "impact", "implementation")

### Step 2: Clarify Purpose and Scope

**Ask user:**
```markdown
## Question 2: What is this literature review for?

Select one or tell me:
- [ ] Academic paper or journal submission
- [ ] Thesis or dissertation chapter
- [ ] Project proposal (e.g., Example Research Institute grant)
- [ ] Technical report for stakeholders
- [ ] Background research for a project
- [ ] Other: _______

Why this matters: Different purposes require different criteria rigor.
```

**Parse response to determine:**
- Rigor level (academic paper = strict, background research = flexible)
- Audience expectations (reviewers vs. stakeholders)
- Suggested corpus size (paper = 20-50, proposal = 30-100, background = 10-30)

### Step 3: Define Temporal Scope

**Ask user:**
```markdown
## Question 3: What time period should we cover?

Consider:
- When did the field/technology emerge? (e.g., AI tutoring became viable ~2015)
- How fast is the field moving? (Fast = recent only, Slow = include older work)
- Do you need historical context or just recent advances?

Options:
- [ ] Last 3 years (2022-2025) - Very recent only
- [ ] Last 5 years (2020-2025) - Recent advances (Recommended for tech)
- [ ] Last 7 years (2018-2025) - Include foundational work
- [ ] Last 10+ years (2015-2025) - Comprehensive historical view
- [ ] Custom: From [YYYY] to [YYYY]

Or tell me what makes sense for your topic.
```

**Parse response and suggest:**
- If user unsure: Recommend 5-7 years for tech topics, 10+ for established fields
- Flag if timeframe seems too narrow or too broad for corpus size

### Step 4: Determine Methodological Scope

**Ask user:**
```markdown
## Question 4: What types of studies should we include?

Think about what evidence you need:

**Empirical studies:**
- [ ] Quantitative (experiments, surveys, correlational studies)
- [ ] Qualitative (interviews, case studies, ethnographies)
- [ ] Mixed methods (combines both)

**Non-empirical:**
- [ ] Theoretical papers (frameworks, models)
- [ ] Literature reviews or meta-analyses
- [ ] Opinion pieces or essays

**My recommendation for "{{research question}}":**
{{AI suggests based on research question - e.g., "Include quantitative and mixed methods for causal claims about effectiveness"}}

Which types should we include? (Can select multiple)
```

**Parse response and:**
- If user wants causal claims: Recommend quantitative/mixed, warn against opinion pieces
- If user wants deep understanding: Recommend qualitative + quantitative
- If user wants comprehensive: Include all empirical, exclude opinion unless expert commentary

### Step 5: Define Contextual Boundaries

**Ask user:**
```markdown
## Question 5: Are there contextual boundaries for your review?

**Geographic/Cultural:**
- Any specific countries, regions, or cultural contexts?
- Example: "one target country only" or "No geographic restrictions"

**Population:**
- Any specific populations? (age groups, demographics, etc.)
- Example: "K-12 students only, exclude higher education"

**Domain/Subject:**
- Any subject area constraints?
- Example: "Mathematics education only" or "All STEM subjects"

**Settings:**
- Any setting constraints? (classrooms, online, hybrid, etc.)

Tell me what boundaries make sense for "{{research question}}"
```

**Parse response and:**
- Extract explicit constraints (K-12, mathematics, target geography, etc.)
- Suggest implicit constraints user might have missed
- Warn if boundaries are too restrictive (may yield tiny corpus)

### Step 6: Language and Access Constraints

**Ask user:**
```markdown
## Question 6: Language and accessibility constraints?

**Language:**
- [ ] English only (most common for academic reviews)
- [ ] English + [Other languages] (if you can read them)
- [ ] No language restrictions

**Publication access:**
- [ ] Peer-reviewed journals only (high quality bar)
- [ ] Include conference proceedings (broader scope)
- [ ] Include grey literature (reports, preprints, theses)
- [ ] Include preprints (arXiv, SSRN, etc.)

**File formats:**
- [ ] PDFs only (traditional)
- [ ] Markdown files only (Markdown notes, web clippings)
- [ ] Mixed (both PDFs and MD files) (Recommended)

My recommendation: {{AI suggests based on purpose from Question 2}}
```

**Parse response and:**
- Default to English only + peer-reviewed if user unsure
- Suggest including MD files if using a Markdown note app
- Warn if excluding conference proceedings in fast-moving fields

### Step 7: Quality Thresholds (Optional)

**Ask user:**
```markdown
## Question 7: Any quality thresholds or specific venues? (Optional)

Some reviews set minimum quality bars:
- Minimum citation count (e.g., "at least 10 citations")
- Specific journals or conferences (e.g., "Top-tier venues only")
- Impact factor thresholds

For most reviews, peer-review is sufficient quality bar.

Do you need additional quality thresholds? (Skip if unsure)
```

**Parse response and:**
- Most users skip this (peer-review is enough)
- If set, warn about potential corpus reduction

### Step 8: Edge Cases and Exclusions

**Ask user:**
```markdown
## Question 8: Are there specific things we should EXCLUDE?

Based on your research question, should we exclude:
- Opinion pieces without data?
- Specific topics that are off-scope?
- Superseded work (older studies by same authors)?
- Industry reports without peer review?

Tell me what should be explicitly excluded, or say "Use standard exclusions"
```

**Parse response and:**
- Standard exclusions: Opinion pieces, clearly off-topic, superseded work
- Add user-specific exclusions

### Step 9: Generate and Review Criteria

**Create draft screening criteria:**

```markdown
## Draft Screening Criteria Generated

Based on your responses, here's your screening criteria draft:

---

# Screening Criteria for Literature Review

## Research Question
{{Refined research question based on Question 1}}

## Inclusion Criteria

### Temporal
- **Published:** {{From Question 3}}
- **Reason:** {{Rationale based on user's goals}}

### Methodological
- **Study types:** {{From Question 4}}
- **Minimum rigor:** {{From Question 6 - peer-reviewed, etc.}}
- **Reason:** {{Why these methods support the research question}}

### Domain/Topic
- **Subject area:** {{From Question 5}}
- **Keywords required:** {{Extracted from research question}}
- **Reason:** {{Focus rationale}}

### Geographic/Cultural
- **Contexts:** {{From Question 5 or "No restrictions"}}
- **Reason:** {{If applicable}}

### Language
- **Languages:** {{From Question 6}}
- **Reason:** {{Practical constraints}}

### File Format
- **Accept PDFs:** Yes
- **Accept Markdown:** {{From Question 6}}
- **Reason:** {{Markdown-notes integration or PDF-only}}

## Exclusion Criteria

### Content-Based
{{From Question 8 + standard exclusions}}

### Methodological
{{From Question 4 - e.g., exclude opinion pieces if only empirical}}

## Relevance Test

A paper is relevant if it meets ALL of the following:
{{Generate 3-4 Boolean tests based on research question}}

## Quality Thresholds (Optional)
{{From Question 7 or "None - peer-review sufficient"}}

## Notes

**Expected corpus size:** {{AI estimates based on criteria}}
- If too small (< 10): Consider relaxing {{most restrictive criterion}}
- If too large (> 100): Consider tightening {{most permissive criterion}}

---

## Review This Draft

Please review the criteria above. You can:
1. **Approve as-is** → I'll save to `settings/screening-criteria.md`
2. **Request changes** → Tell me what to adjust
3. **Manual edit** → I'll save the draft and you can edit directly

What would you like to do?
```

### Step 10: Iterate or Finalize

**Based on user response:**

**If "Approve as-is":**
1. Save criteria to `settings/screening-criteria.md`
2. Generate refined research question to `settings/research-question.md`
3. Tell user: "Phase 0 complete! Ready for Phase 1 (Screening). Add PDFs/MD files to `corpus/candidates/` and launch orchestrator."

**If "Request changes":**
1. Parse requested changes
2. Update specific sections
3. Present updated draft
4. Iterate until approval

**If "Manual edit":**
1. Save draft to `settings/screening-criteria-draft.md`
2. Tell user to edit and save as `screening-criteria.md`
3. Remind to finalize before Phase 1

## Outputs

- **Primary:** `settings/screening-criteria.md` (finalized criteria)
- **Secondary:** `settings/research-question.md` (refined research question)
- **Optional:** `settings/criteria-generation-log.md` (Q&A dialogue for reference)

## Quality Checks

- [ ] Research question is clear and specific (one sentence)
- [ ] Temporal scope is appropriate for field velocity
- [ ] Methodological scope matches research question needs
- [ ] Boundaries are neither too restrictive (< 5 papers) nor too broad (> 200 papers)
- [ ] Relevance test has 3-4 Boolean conditions
- [ ] User understands what will be included/excluded

## Example Dialogue

**User:** "I want to review AI tutoring research for an Example Research Institute proposal"

**Agent:**
> **Question 1:** What specifically about AI tutoring do you want to investigate?

**User:** "How effective it is for K-12 math students"

**Agent:**
> **Refined question:** "How do AI-powered tutoring systems impact learning outcomes for K-12 mathematics students?"
>
> **Question 2:** This is for an Example Research Institute proposal. Should we focus on:
> - Evidence of effectiveness (for justification)?
> - Implementation factors (for project design)?
> - Both?

**User:** "Both - I need to show it works and how to implement it"

**Agent:**
> **Question 3:** Timeframe - AI tutoring became viable around 2015. Should we cover:
> - Last 5 years (2020-2025) - Recent evidence (Recommended)
> - Last 7 years (2018-2025) - Include foundational work
> - Last 10 years (2015-2025) - Comprehensive

**User:** "Last 7 years sounds good"

**[Continues through all questions...]**

**Agent:** *(After Question 8)*
> Here's your draft screening criteria:
>
> **Inclusion:**
> - Published 2018-2025
> - Empirical studies (quantitative or mixed methods)
> - K-12 mathematics context
> - Measures learning outcomes OR implementation factors
> - English language
> - PDFs and Markdown files accepted
>
> **Exclusion:**
> - Opinion pieces without data
> - Higher education context
> - Non-mathematics subjects
>
> **Expected corpus:** 30-50 papers
>
> Approve this?

**User:** "Yes"

**Agent:**
> ✅ Saved to `settings/screening-criteria.md`
> ✅ Saved research question to `settings/research-question.md`
>
> **Next:** Add 40-60 candidate PDFs/MD files to `corpus/candidates/`, then launch Phase 1 (Screening).

## Edge Cases & Limitations

### Handles Well
- Users unfamiliar with literature review methodology
- Vague initial research questions (helps refine)
- Multiple valid approaches (presents options)
- Example Research Institute project-specific contexts

### Known Limitations
- **Can't read papers:** Doesn't know what's available in the literature (user provides)
- **Domain expertise:** May not know field-specific standards
  - Workaround: Ask user about field norms in Question 4
- **Corpus size estimation:** Rough estimate only
  - Workaround: User can test criteria with Phase 1, then revise

### Workarounds
- **User has no idea:** Start with broadest criteria, narrow after Phase 1 reveals corpus
- **Too restrictive:** After Q&A, show estimated corpus size and warn if < 10
- **Too broad:** After Q&A, show estimated corpus size and warn if > 100

## Invocation

### Via Orchestrator (Recommended)

```markdown
Help me complete a literature review.

**Note:** I need help defining screening criteria.

Topic: {{brief topic description}}
```

Orchestrator detects missing criteria and launches Phase 0.

### Standalone Invocation

```markdown
Help me generate screening criteria for a literature review.

Topic: {{topic}}
Purpose: {{proposal/paper/thesis/etc.}}
```

## Prompt Template

The reusable prompt for this phase is defined inline in this agent file (see the sections above).

## Version History

### v1.0 - 2026-01-11
- Initial Phase 0 criteria generator
- Interactive 8-question dialogue
- Draft generation and iteration support
- Markdown file-format support

## Related

- [[orchestrator|Orchestrator Agent]] - Launches Phase 0 if criteria missing
- [[phase1-screener|Phase 1: Screener Agent]] - Uses generated criteria
- [[../assets/screening-criteria-template|Screening Criteria Template]] - Manual alternative






