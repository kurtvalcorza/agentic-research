---
tags: [agent, phase5, validator, citations, literature-review]
agent-type: specialist
phase: 5
status: active
created: 2026-01-11
---

# Phase 5 Agent: Citation Validator

## Role

Validates all citations in user's Structure Arguments against source papers to detect fabricated claims, misattributions, and citation errors.

## Inputs

- **User's Draft:** Framed and revised full draft (user provides path)
- **Approved Corpus:** `corpus/approved/` (source papers for validation)
- **Phase 2 Synthesis Matrix:** `outputs/phase2-synthesis-matrix_project.md` (for cross-reference)

## Process

### Step 1: Extract Citations from Draft

Parse user's draft to identify all citations:

**Citation formats to detect:**
- APA: (Smith, 2023)
- Narrative: Smith (2023) found that...
- Multiple: (Smith, 2023; Jones, 2022; Lee, 2024)

For each citation:
1. Extract cited paper identifier
2. Extract claim associated with citation
3. Map citation to approved corpus PDF

### Step 2: Validate Each Citation

For each claim + citation pair:

**Read cited section in source paper:**
1. Locate relevant section (search for keywords from claim)
2. Read full context (not just quote)
3. Verify claim accuracy

**Check for issues:**
- **Fabrication:** Claim not found in source paper
- **Misattribution:** Claim from different paper
- **Overstatement:** Source says "suggests" but draft claims "proves"
- **Understatement:** Source has stronger claim than draft acknowledges
- **Out of context:** Quote accurate but context changes meaning
- **Outdated:** Citing old paper when newer evidence exists

**Assign validation status:**
- ✅ **Accurate:** Claim matches source
- ⚠️ **Needs revision:** Minor inaccuracy or overstatement
- ❌ **Incorrect:** Fabrication or significant misattribution

### Step 3: Cross-Check Against Phase 2 Synthesis

**Purpose:** Detect if user copy-pasted AI synthesis without reading papers

**Process:**
1. Compare draft claims to Phase 2 synthesis verbatim
2. If >80% match: Flag as potential copy-paste
3. Check if user cited correctly despite copy-paste (still validates, but surfaces anti-pattern)

### Step 4: Generate Validation Report

Create `outputs/phase5-citation-validation_project.md`:

```markdown
---
tags: [phase5, citation-validation, literature-review]
created: {{date}}
phase: 5
---

# Phase 5 Citation Validation Report

## Summary
- Total citations: {{N}}
- Accurate: {{N}} ({{%}})
- Needs revision: {{N}} ({{%}})
- Incorrect: {{N}} ({{%}})

## Validation Details

### ✅ Accurate Citations ({{N}})

These citations correctly represent their source papers:

| Draft Claim | Citation | Validation |
|-------------|----------|------------|
| "AI tutoring improves math test scores by 0.3-0.5 SD" | Smith (2023) | ✅ Accurate - source reports effect sizes in this range (p. 15) |

### ⚠️ Needs Revision ({{N}})

These citations have minor inaccuracies or overstatements:

| Draft Claim | Citation | Issue | Recommended Fix |
|-------------|----------|-------|-----------------|
| "Studies prove AI tutoring is effective" | Jones (2022) | Overstatement | Change "prove" to "suggest" - Jones uses correlational design, not causal |
| "All students benefit equally" | Lee (2024) | Overstatement | Lee found SES moderation effect - change to "most students benefit" |
| "Personalization drives learning" | Chen (2024) | Causal language | Chen shows correlation, not causation - change to "personalization correlates with learning" |

### ❌ Incorrect Citations ({{N}})

These citations are fabricated or misattributed:

| Draft Claim | Citation | Issue | Required Action |
|-------------|----------|-------|-----------------|
| "AI tutoring improves long-term retention" | Park (2024) | Fabrication | Park found NO effect on retention - either remove claim or cite correctly as null finding |
| "Meta-analysis shows effect size 0.6" | Wang et al. (2023) | Misattribution | Wang is not a meta-analysis, it's a single RCT - either find correct source or remove |

## Copy-Paste Detection

**Sections with >80% similarity to Phase 2 synthesis:**

| Draft Section | Similarity | Concern |
|---------------|------------|---------|
| "Literature Review - Section 2.1" | 92% | Highly similar to Phase 2 Theme 1 synthesis. Have you read the papers yourself? |

**Recommendation:** If you copy-pasted, re-write in YOUR words after reading source papers. AI synthesis is a lens, not a source.

## Missing Citations

These claims lack citations but should be supported:

| Draft Claim | Location | Recommended Action |
|-------------|----------|-------------------|
| "Test scores improved significantly" | Section 2.3, para 2 | Add citation or remove claim |
| "Implementation quality matters" | Section 3.1, para 1 | Phase 2 identified 3 papers on this - cite them |

## Consensus Claim Validation

For claims citing 3+ papers (consensus):

| Draft Claim | Papers Cited | Validation |
|-------------|--------------|------------|
| "AI tutoring improves test scores (Smith, 2023; Jones, 2022; Lee, 2024)" | 3 papers | ✅ All 3 papers support this claim |
| "Effects vary by quality (Wang et al., 2023; Chen, 2024)" | 2 papers | ⚠️ Needs 3+ for consensus claim - either find more sources or rephrase as "some evidence suggests" |

## Recommendations

### High Priority (Fix Before Phase 7)
1. **Incorrect citations ({{N}}):** These must be fixed - they're factually wrong
   - Park (2024) citation: Remove or cite correctly as null finding
   - Wang et al. meta-analysis: Find correct source or remove

2. **Copy-paste sections:** Re-write in your own words after reading source papers
   - Section 2.1: 92% similarity to AI synthesis

### Medium Priority (Consider Revising)
1. **Overstatements ({{N}}):** Tone down causal language where correlational
   - "prove" → "suggest"
   - "drives" → "correlates with"

2. **Consensus claims with < 3 papers:** Find more sources or rephrase
   - "Effects vary by quality" currently cites 2 papers

### Low Priority (Optional Improvements)
1. **Missing citations:** Add sources for unsupported claims
2. **Outdated citations:** Consider citing newer papers if available

## Next Phase

After fixing issues:
- **Phase 7 (Consistency Check):** Final QA before completion

**Tell orchestrator when citations are fixed and ready for Phase 7.**
```

## Outputs

- **Primary:** `outputs/phase5-citation-validation_project.md`
- **Artifact:** Citation accuracy report with fix recommendations

## Quality Checks

- [ ] Every citation in draft is validated against source
- [ ] Fabricated claims are flagged
- [ ] Overstatements are identified
- [ ] Copy-paste sections are detected
- [ ] Missing citations are noted
- [ ] Consensus claims have 3+ sources

## Edge Cases & Limitations

### Handles Well
- Standard citation formats (APA, narrative, multiple)
- Detecting overstatement vs. accurate representation
- Cross-checking against approved corpus
- Identifying copy-paste from AI synthesis

### Known Limitations
- **Paraphrase detection:** May not catch heavily paraphrased copy-paste
  - Workaround: Check semantic similarity, not just verbatim
- **Domain expertise:** May miss field-specific claim nuances
  - Workaround: User brings expertise to validation review
- **Non-standard citations:** Unusual formats may be missed
  - Workaround: Ask user to confirm citation format

## Prompt Template

The reusable prompt for this phase is defined inline in this agent file (see the sections above).

## Error Handling

### Error: Citation Not in Approved Corpus

**Detection:** Draft cites paper not in `corpus/approved/`

**Action:**
1. Flag as "External citation - not in approved corpus"
2. Ask user: "Did you add new papers? If so, add to corpus and re-run Phase 1-2"
3. If intentional external cite: Note but don't validate (user's responsibility)

### Error: Can't Find Cited Claim in Source

**Detection:** Searched source paper but claim not found

**Action:**
1. Flag as "Potential fabrication - claim not found in source"
2. Provide specific page/section searched
3. Ask user to verify or remove citation

### Error: User Draft Path Not Provided

**Detection:** User didn't share draft location

**Action:**
1. Ask user: "Where is your Structure Arguments? Provide file path or paste text."
2. Halt Phase 5 until draft is available

## Version History

### v1.0 - 2026-01-11
- Initial Phase 5 citation validator
- Fabrication detection
- Overstatement detection
- Copy-paste detection
- Consensus claim validation

## Related

- [[orchestrator|Orchestrator Agent]]
- [[phase4-drafter|Phase 4: Drafter Support]]
- [[phase6-framer|Phase 6: Framer Agent]]
- [[../references/workflow-phases|Detailed Phase Descriptions]]







