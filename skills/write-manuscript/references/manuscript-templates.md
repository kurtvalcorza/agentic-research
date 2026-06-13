# Manuscript Templates

Standard templates and formats for academic manuscript synthesis.

---

## Manuscript Outline Template

**Framework:** Known → Gap → Contribution

```markdown
# Manuscript Outline

## 1. Introduction
**Argument:** Establish the problem space and significance
**Key claim:** [What reader should believe after intro]

## 2. Background / Literature Review
**Argument:** Show what's known and what's missing
**Consensus:** [List agreed-upon findings]
**Tensions:** [List disagreements/contradictions]
**Gap:** [The specific gap your work addresses]

## 3. Methodology / Approach
**Argument:** Justify your method for addressing the gap
**Why this method:** [Reasoning]

## 4. Results / Findings
**Argument:** Present evidence for your contribution
**Key evidence:** [List main findings]

## 5. Discussion
**Argument:** Interpret findings in context of the gap
**Implications:** [What this means]
**Limitations:** [What this doesn't address]

## 6. Conclusion
**Argument:** Restate contribution and future directions
**Take-away:** [One sentence summary]
```

---

## Argument Framework

### Structure: Known → Gap → Contribution

**1. Known (Background)**
- What do all sources agree on?
- What's the established "state of the art"?
- Map consensus across research notes

**2. Gap (Problem)**
- Where do sources disagree?
- What remains unaddressed?
- What specific question needs answering?

**3. Contribution (Solution)**
- How does this work address the gap?
- What new knowledge is created?
- What changes in the field if this is right?

---

## Section Structure Guidelines

### Each Section Should:
1. **Advance the argument** - Not just present information
2. **Have a clear claim** - What reader should believe after this section
3. **Build on previous sections** - Progressive argumentation
4. **Set up next section** - Logical flow

### Section-Level Checklist
- [ ] Opening sentence states section's purpose
- [ ] Key claim is explicit
- [ ] Evidence supports the claim
- [ ] Transitions to next section

---

## Output Files

Standard file naming and purposes.

| File | Purpose | Created In | Format |
|------|---------|------------|--------|
| `manuscript-outline.md` | Argument structure scaffold | Phase 2 | Markdown with section-level claims |
| `[section]-draft.md` | Individual section drafts | Phase 3 | Markdown prose |
| `manuscript-draft.md` | Complete manuscript draft | Phase 3 completion | Full Markdown document |
| `citation-check.md` | Source verification report | Phase 4 | Checklist format |
| `validation-report.md` | Consolidated validation results | Phase 5 | Structured report |
| `validation/*.md` | Detailed validation sub-reports | Phase 5 | Individual skill outputs |

---

## File Organization

### Recommended Directory Structure

```
project/
├── inputs/
│   ├── research-note-1.md
│   ├── research-note-2.md
│   └── synthesis-matrix.md (from LRA)
├── outputs/
│   ├── manuscript-outline.md
│   ├── manuscript-draft.md
│   ├── citation-check.md
│   └── validation/
│       └── validation-report.md
└── sections/
    ├── introduction-draft.md
    ├── background-draft.md
    └── conclusion-draft.md
```

### File Naming Conventions
- **Drafts:** `{section-name}-draft.md`
- **Finals:** `manuscript-{type}.md` (e.g., `manuscript-draft.md`, `manuscript-final.md`)
- **Reports:** `{check-type}-check.md` or `{validation-type}-report.md`

---

## Integration with Other Skills

This template structure is designed for seamless handoff to:
- **validate-manuscript** - Uses `manuscript-draft.md` and `manuscript-outline.md`
- **recursive-lit-review** - Provides `meta-themes.md` for structuring
- **review-literature** - Provides `argument-outline.md` and `synthesis-notes.md`

See: [[integration-protocols|Integration Protocols]]
