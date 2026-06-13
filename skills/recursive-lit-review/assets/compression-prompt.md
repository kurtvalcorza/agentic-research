# Compression Prompt Template

Use this prompt for extracting atomic claims from a batch of papers.

---

## Extraction Instructions

You are processing **Batch [N]** containing [COUNT] papers for a systematic literature review.

### Papers in This Batch
1. [Filename1] - [Brief identifier if available]
2. [Filename2]
3. ...

### Your Task

For each paper, extract:

1. **Atomic Claims** - Specific, verifiable findings
   - Include page/section reference
   - Quote key phrases when possible
   - Tag with methodology type

2. **Methodological Profile**
   - Study type (RCT, quasi-experimental, qualitative, review, etc.)
   - Sample size and population
   - Key limitations acknowledged

3. **Cross-Paper Connections**
   - Papers that agree on a finding
   - Papers that contradict each other
   - Gaps none of the papers address

### Output Format

```markdown
# Staging Batch [N]

## Papers Processed
| ID | Citation | Type | Sample |
|----|----------|------|--------|
| P1 | [Author2023] | RCT | n=500 |
| P2 | [Author2024] | Qualitative | n=30 |

## Extracted Claims

### Theme: [Emergent Theme Name]

**Consensus:**
- "[Specific finding quoted or paraphrased]" (P1, p.12)
- "[Related finding]" (P2, p.45)

**Tensions:**
- P1 claims [X], but P2 claims [Y]. Context: [Why might they differ?]

### Theme: [Next Theme]
...

## Methodological Notes
- P1 strengths: [...]
- P1 limitations: [...]
- P2 strengths: [...]
- P2 limitations: [...]

## Gaps in This Batch
- None of these papers address [specific gap]
- [Gap 2]

## Cross-References
- P1 cites P2 (if in same batch)
- P1 and P3 share methodology
```

### Quality Checks
- [ ] Every claim has a citation (Paper ID + page)
- [ ] Contradictions explicitly noted
- [ ] Methodology logged for each paper
- [ ] At least one gap identified
