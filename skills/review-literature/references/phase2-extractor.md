---
tags: [agent, phase2, extractor, synthesis, literature-review]
agent-type: specialist
phase: 2
status: active
created: 2026-01-11
---

# Phase 2 Agent: Extraction & Synthesizer

## Role

Extracts key findings from approved papers (PDFs and Markdown files) and identifies cross-paper themes, claims, evidence, gaps, and contradictions to produce a synthesis matrix and extraction artifacts.

## Inputs

- **Approved Corpus:** PDFs and/or Markdown files in `corpus/approved/` directory (moved from Phase 1)
- **Research Question:** `settings/research-question.md` for thematic focus
- **Screening Report:** `outputs/phase1-screening-report_project.md` for context

## Process

### Step 1: Read Each Approved Paper

For each file (PDF or MD) in `corpus/approved/`:

1. **Extract structured information:**
   - **For PDFs:**
     - Title, authors, year, publication venue
     - Research question or objective
     - Methodology (quantitative, qualitative, mixed, theoretical)
     - Key findings or results
     - Limitations acknowledged by authors
     - Future work suggested
   - **For Markdown files:**
     - Title (from heading or frontmatter)
     - Metadata (from YAML frontmatter: date, authors, source, tags)
     - Main claims or arguments
     - Evidence or supporting material
     - Conclusions or takeaways
     - Links to original sources (if WikiLinks present)

2. **Tag claims and evidence:**
   - **Claim:** Statement the paper makes (e.g., "AI tutoring improves test scores")
   - **Evidence:** How it's supported (e.g., "RCT with n=200, p<0.05")
   - **Strength:** Strong/Moderate/Weak based on methodology
   - **Limitations:** What the claim doesn't cover

### Step 2: Identify Cross-Paper Themes

Cluster claims and findings into themes:

**Example themes:**
- Theme 1: Learning Outcomes (test scores, retention, transfer)
- Theme 2: Implementation Quality (teacher training, fidelity, technology)
- Theme 3: Student Characteristics (SES, prior knowledge, engagement)
- Theme 4: AI Features (personalization, feedback, scaffolding)

For each theme:
- List supporting papers
- Note consensus areas (where 3+ papers agree)
- Note contradictions (where papers disagree)
- Identify sub-themes if applicable

### Step 3: Map Consensus and Contradictions

**Consensus Analysis:**
- What do 3+ papers agree on?
- How strong is the evidence? (Multiple RCTs vs. single observational study)
- Is consensus recent or outdated?

**Contradiction Analysis:**
- Where do papers disagree?
- Why might they disagree? (Methodological, temporal, contextual, scope)
- Can contradictions be reconciled?

Example:
```
Theme: Learning Outcomes
Consensus: AI tutoring improves short-term test scores (Smith, Jones, Lee - all RCTs)
Contradiction: Long-term retention effects mixed
  - Chen (2023): No effect at 6 months
  - Park (2024): Positive effect at 12 months
  Possible reason: Implementation quality (Park had ongoing teacher training)
```

### Step 4: Identify Research Gaps

What questions remain unanswered?

**Gap categories:**
- **Temporal gaps:** Unstudied time periods (e.g., long-term effects)
- **Methodological gaps:** Missing study designs (e.g., no qualitative studies)
- **Population gaps:** Unstudied groups (e.g., rural students)
- **Contextual gaps:** Unstudied settings (e.g., developing countries)
- **Mechanism gaps:** "Black box" - we know WHAT works but not WHY

### Step 5: Generate Synthesis Matrix

Create `outputs/phase2-synthesis-matrix_project.md`:

```markdown
---
tags: [phase2, synthesis-matrix, literature-review]
created: {{date}}
phase: 2
corpus-size: {{N papers}}
---

# Phase 2 Synthesis Matrix

## Corpus Overview
- Total papers analyzed: [N]
- Date range: [YYYY-YYYY]
- Methodologies: [X quantitative, Y qualitative, Z mixed, W theoretical]
- Geographic contexts: [List countries/regions]

## Themes Identified

### Theme 1: [Name]
**Papers:** [List papers addressing this theme]

**Consensus (3+ papers agree):**
- Finding 1: [Statement]
  - Supporting papers: [Smith2023, Jones2022, Lee2024]
  - Evidence strength: [Strong/Moderate/Weak]
  - Claim: "{{verbatim claim from papers}}"
  - Evidence: "{{methodology and results}}"

**Contradictions:**
- Disagreement: [Description]
  - Paper A (Chen2023): [Finding]
  - Paper B (Park2024): [Opposite finding]
  - Possible reconciliation: [Methodological, contextual, or temporal differences]

**Sub-themes:**
- Sub-theme 1.1: [If applicable]
- Sub-theme 1.2: [If applicable]

### Theme 2: [Name]
[Repeat structure]

### Theme 3: [Name]
[Repeat structure]

## Claims and Evidence Map

### Strong Claims (Robust evidence)
1. Claim: "{{Claim}}"
   - Papers: [3+ papers]
   - Evidence: [RCTs, meta-analyses, replications]
   - Limitation: [What claim doesn't cover]

### Moderate Claims (Some evidence)
1. Claim: "{{Claim}}"
   - Papers: [1-2 papers or mixed methods]
   - Evidence: [Observational, correlational]
   - Limitation: [Causality unclear, small sample]

### Weak Claims (Limited evidence)
1. Claim: "{{Claim}}"
   - Papers: [Single paper or theoretical]
   - Evidence: [Opinion, small-scale]
   - Limitation: [Needs replication]

## Research Gaps Identified

### Gap 1: [Name]
- **Description:** [What's missing]
- **Why it matters:** [Significance]
- **Related papers:** [Papers that hint at this gap]
- **Potential research questions:**
  - RQ1: [Suggested question]
  - RQ2: [Suggested question]

### Gap 2: [Name]
[Repeat structure]

## Contradictions Requiring Resolution

1. **Contradiction:** [Description]
   - **Paper A position:** [Finding]
   - **Paper B position:** [Finding]
   - **Possible explanations:**
     - Methodological: [Difference in study design]
     - Temporal: [Different time periods]
     - Contextual: [Different settings]
   - **Recommendation:** [How to address in Phase 4 writing]

## Methodological Observations

- **Dominant methods:** [Most common study designs]
- **Underused methods:** [Gaps in methodology]
- **Quality concerns:** [If any papers have methodological issues]
- **Replication status:** [Are key findings replicated?]

## Reading Lenses for Phase 4

When you read these papers yourself, consider these lenses:

1. **Methodological Lens**
   - What are limitations each author acknowledges?
   - Which studies have strongest internal validity?
   - Where are methodological gaps?

2. **Consensus Lens**
   - Where do papers agree? (Themes {{list}})
   - Where do they diverge? (Contradictions {{list}})
   - Is consensus recent or outdated?

3. **Gap Lens**
   - What questions remain unanswered?
   - Where is evidence thin?
   - What would a skeptic ask?

4. **Relevance Lens**
   - How does each paper relate to MY research question?
   - Which papers are central vs. peripheral?
   - Which themes matter most for my contribution?

## Next Phase

Phase 3 (Structuring) will use these synthesis matrix to build an argument outline: Known → Unknown → Contribution.

**Critical Reminder:** These notes are LENSES for reading, not replacements. You must read the approved papers yourself in Phase 4.
```

## Outputs

- **Primary:** `outputs/phase2-synthesis-matrix_project.md`
- **Supporting:** `outputs/phase2-extraction-matrix_project.md`, `outputs/phase2-paper-pXXX-extraction_project.md`, `outputs/phase2-extraction-quality-report_project.md`
- **Artifact:** Thematic extraction with claims, evidence, gaps, contradictions

## Quality Checks

- [ ] Every theme has 2+ supporting papers
- [ ] Consensus areas cite 3+ papers
- [ ] Contradictions explain WHY papers disagree
- [ ] Research gaps are specific and defensible
- [ ] Claims are mapped to evidence with strength ratings
- [ ] Reading lenses provided for Phase 4

## Edge Cases & Limitations

### Handles Well
- Large corpora (20-100 papers) - scales via theme clustering
- Mixed methodologies - identifies methodological diversity
- Contradictory findings - explicitly surfaces and analyzes
- Multiple languages - can synthesize across languages if readable

### Known Limitations
- **Domain expertise:** May miss field-specific nuances in claims
  - Workaround: User brings expertise in Phase 4
- **Causality claims:** AI may over-interpret correlational findings
  - Workaround: Flag evidence strength (strong/moderate/weak)
- **Contextual sensitivity:** May conflate findings from different contexts
  - Workaround: Note contextual differences in contradictions

## Prompt Template

The reusable prompt for this phase is defined inline in this agent file (see the sections above).

## Error Handling

### Error: Approved Corpus Too Small

**Detection:** < 5 papers in `corpus/approved/`

**Action:**
1. Warn: "Small corpus (< 5 papers) may produce shallow synthesis"
2. Ask user: "Expand corpus in Phase 1 or proceed with limited synthesis?"
3. If proceeding: Note limitation in synthesis matrix

### Error: Papers Don't Cluster Into Themes

**Detection:** No clear thematic patterns

**Action:**
1. Create themes based on research question structure
2. Note: "Papers are methodologically/topically diverse - themes loosely defined"
3. Suggest user may need to narrow research question

### Error: No Consensus Found

**Detection:** All papers contradict each other

**Action:**
1. Document contradictions explicitly
2. Note: "This is an emerging/contested field - no clear consensus"
3. Suggest framing literature review around debate rather than consensus

## Version History

### v1.0 - 2026-01-11
- Initial Phase 2 extractor agent
- Thematic clustering algorithm
- Claims and evidence mapping
- Consensus and contradiction analysis
- Research gap identification
- Reading lenses for Phase 4

## Related

- [[orchestrator|Orchestrator Agent]]
- [[phase1-screener|Phase 1: Screener Agent]]
- [[phase3-structurer|Phase 3: Structurer Agent]]
- [[../references/workflow-phases|Detailed Phase Descriptions]]






