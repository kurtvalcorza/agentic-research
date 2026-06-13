# appraise-risk-of-bias

**Per-study risk-of-bias appraisal with the design-appropriate validated instrument** — RoB 2 (RCTs), ROBINS-I (non-randomized), Newcastle-Ottawa (observational), QUADAS-2 (diagnostic). A **human-gated** step that feeds GRADE.

## Why it exists

A review that includes studies without weighting their internal validity treats strong and weak evidence the same. Risk-of-bias appraisal is what lets GRADE downgrade a body of evidence built on biased studies. The pipeline had GRADE-style grading but no per-study RoB instruments — this adds them.

## Why it's human-gated

The research is clear that risk-of-bias appraisal is the **weakest task for LLMs** (~0.62 accuracy vs ~0.95 for extraction), because it's a judgment about how a study was *conducted*. So this skill assists, it doesn't decide:

1. The agent **extracts the evidence** for each signaling question from the paper.
2. It **proposes a provisional rating** with reasoning, clearly marked provisional.
3. A **human confirms or overrides** every judgment before it's final and feeds GRADE.

## What it produces

A per-study appraisal worksheet (domain ratings + overall + extracted evidence + who confirmed), a traffic-light RoB summary for the manuscript, and the confirmed overall ratings handed to `validate-evidence` (GRADE).

See `references/instruments.md` for the domains and signaling questions of each tool.

## Related

`extract-synthesis` · `validate-evidence` (GRADE) · `screen-literature` · `prisma-flow`
