# Literature Review: Detailed Examples & Limitations

## Usage Examples

### Scenario
Writing a literature review for an Example Research Institute Project Atlas project proposal on "AI-powered tutoring systems in K-12 education."

**Sample Input:**
- **Research Question:** How do AI-powered tutoring systems impact student learning outcomes in K-12 mathematics education?
- **Corpus:** 50 PDFs in `corpus/candidates/`

**Sample Output (Phase 1 Screening):**
```markdown
## Summary
- Total papers reviewed: 50
- Approved: 23
- Rejected: 27

## Approved Papers
| Paper | Score | Justification |
|-------|-------|---------------|
| Smith2023_AI_Tutors.pdf | 9 | RCT, K-12 math, learning outcomes measured |
```

**Sample Output (Phase 3 Outline):**
```markdown
## Known (Consensus)
- AI tutoring systems improve math test scores (Smith, Jones, Lee)
- Personalization features correlate with effectiveness (Chen, Park)

## Unknown (Gap)
- Little research on long-term retention beyond immediate post-tests
- Unclear which specific AI features drive learning vs. engagement
```

## Edge Cases & Limitations

### Handles Well
- Large corpora (50-500 papers) via context isolation per phase
- **Mixed formats** (PDFs + Markdown files in same corpus)
- **Obsidian notes** with WikiLinks and frontmatter metadata
- Multilingual papers (if specified)
- Contradictory findings (surfaces tensions in Phase 2)

### Known Limitations
- **PDF Quality:** Corrupted or image-only PDFs may fail extraction.
- **Citation Formats:** Non-standard citations may require manual validation.
- **Domain Knowledge:** AI may miss field-specific nuances.

### Does Not Handle
- **Meta-analysis:** Statistical pooling across studies.
- **Grounded Theory:** Emergent coding from qualitative data.
- **Non-text Sources:** Videos, audio recordings.
- **Books:** Full-length books (extract relevant chapters as PDF/MD first).

## Hybrid Workflow Philosophy: Why Hybrid?
This skill reconciles two paradigms:
1. **Automation-First:** Fast, thorough corpus processing.
2. **Enhance Writing (Cognition):** Deep understanding through provocation.

The handoff point (Phase 3→4) ensures you automate tedious tasks while preserving intellectual ownership where it matters most. **You must read the papers yourself.** AI synthesis notes are lenses for reading, not replacements for reading.
