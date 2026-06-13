# Generate Screening Criteria

Transforms vague research intent into rigorous, operational screening criteria through an interactive research design interview.

## What It Does

Converts statements like "I want to study AI in education" into binary, machine-executable screening rules for literature review.

> **Upstream first (for pre-specified reviews):** In a registrable/reproducible review, eligibility is decided up front by `design-review-protocol` — which sets the review type (systematic / scoping / rapid / umbrella / narrative) and frames the question (PICO / PEO / SPIDER / PCC). When a `protocol.md` exists, this skill **operationalizes its eligibility** into `screening-criteria.md` rather than inventing scope ad hoc; scope-changing tweaks become protocol amendments. When no protocol exists, the interactive interview below still works — but for any registrable review, run `design-review-protocol` first.

## Interview Process

**Three rounds of questions:**

1. **Core Questions**: Research focus, population, intervention/phenomenon, outcomes
2. **Scope Questions**: Time range, geography, study types, theoretical lens
3. **Filter Questions**: Exclusions, edge cases, must-have elements

## Outputs

**`screening-criteria.md`** with:
- **Inclusion Criteria**: Binary yes/no rules
- **Exclusion Criteria**: Explicit rejections
- **Boundary Cases**: How to handle edge cases
- **Operational Definitions**: Clear term definitions

## Why Binary Matters

Screening criteria must be:
- **Operational**: No subjective judgment required
- **Reproducible**: Two reviewers get same result
- **Efficient**: Fast Phase 1 filtering
- **Auditable**: Clear trail of decisions

## Example Transformation

**Before**: "I want to study AI chatbots for mental health support"

**After**:
```markdown
## Inclusion Criteria
- [ ] Technology: Uses conversational AI/chatbot
- [ ] Domain: Mental health, counseling, or psychological support
- [ ] Empirical: Reports outcomes or user data
- [ ] Language: English full-text available

## Exclusion Criteria
- [ ] Opinion pieces without data
- [ ] Non-conversational AI (diagnostic tools only)
- [ ] Animal studies
```

## Related Skills

- `design-review-protocol` - Recommended upstream. Pre-specifies the review type, framed question, and eligibility that these criteria operationalize.
- `screen-literature` - Uses these criteria for Phase 1 screening
- `orchestrate-research` - Full research pipeline orchestrator
- `review-literature` - 7-phase literature review automation

## When to Use

- At the start of any systematic review
- When research question is defined but scope is fuzzy
- Before gathering papers to avoid scope creep
- When team needs aligned understanding of boundaries
