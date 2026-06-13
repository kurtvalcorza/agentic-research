# Quality Gates

Quality assurance rules and anti-patterns for manuscript synthesis.

---

## Citation Checks (Phase 4)

### Rules
1. **Source Traceability**
   - Every claim must trace to a source in input notes
   - Flag any claim that cannot be traced to provided sources
   - No hallucinated citations allowed

2. **Outside Source Warning**
   - Warn if user introduces claims without evidence
   - Require explicit acknowledgment when adding outside sources
   - Maintain citation integrity

3. **Citation Verification**
   - Cross-reference claims against source notes
   - Verify interpretation matches source content
   - Check for citation misrepresentation

---

## Consistency Checks (Phase 4)

### Rules
1. **Introduction-Conclusion Alignment**
   - Verify conclusion addresses problems raised in introduction
   - Check that promised contributions are delivered
   - Ensure framing is consistent throughout

2. **Gap-Contribution Matching**
   - Verify identified gap matches proposed contribution
   - Check that contribution logically addresses the gap
   - Ensure gap is not invented to fit contribution

3. **Terminology Consistency**
   - Same terms used consistently throughout manuscript
   - Key concepts defined once and used uniformly
   - No unexplained shifts in terminology

---

## Anti-Patterns

What NOT to do when synthesizing manuscripts.

| Anti-Pattern | Why It's Bad | Mitigation |
|--------------|--------------|------------|
| **Copy-Pasting** | Concatenating summaries ≠ synthesis | Force integration and argumentation |
| **Ghostwriting** | Writing sections without user input on the point | Require user to articulate argument first |
| **Hallucinated Citations** | Inventing sources not in input notes | Strict source traceability checks |
| **Smoothing Tensions** | Resolving contradictions user hasn't adjudicated | Highlight tensions, require user decision |
| **Accepting Uncritically** | Letting user accept AI framing without examination | Challenge framing choices |

---

## Quality Checklists

### Before Writing
- [ ] User has articulated single most important contribution
- [ ] Tensions in sources have been identified
- [ ] User has adjudicated (not ignored) contradictions

### During Writing
- [ ] Every claim traces to a source in input notes
- [ ] User is actively thinking, not just accepting suggestions
- [ ] Argument advances in each section

### After Writing
- [ ] Conclusion matches Introduction
- [ ] Contribution addresses the stated Gap
- [ ] No hallucinated citations
- [ ] Limitations acknowledged

---

## Validation Integration

After Phase 4 quality gates pass, manuscripts should proceed to comprehensive validation using the validate-manuscript skill for deeper analysis.

See: [[integration-protocols#validate-manuscript|Validation Handoff Protocol]]
