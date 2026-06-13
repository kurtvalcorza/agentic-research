# design-review-protocol

**Plan and pre-specify a review before you search** — pick the review type, frame the question, and write a registrable, PRISMA-P-aligned protocol that the rest of the pipeline derives from.

## Why it exists

Rigorous reviews are pre-specified: review type, question, eligibility, search plan, and analysis methods decided up front. That's the main defense against scope drift and selective reporting, and it determines which reporting guideline and appraisal steps apply. The pipeline jumped straight to criteria/search; this adds the planning step that should come first.

## What it does

1. **Review type** — systematic / scoping / rapid / umbrella / narrative (each has different rigor + reporting rules).
2. **Question framework** — PICO (effectiveness), PEO (observational), SPIDER (qualitative), PCC (scoping).
3. **Protocol** — a PRISMA-P-aligned `protocol.md`: eligibility, search plan, screening/extraction/RoB/synthesis methods, amendments log.
4. **Registration** — ready to paste into PROSPERO (health systematic) / OSF / protocols.io.
5. **AI disclosure planned up front** (PRISMA-trAIce).

The protocol's eligibility feeds `generate-screening-criteria`; its search plan feeds `acquire-corpus`; its appraisal plan feeds `appraise-risk-of-bias`.

## Related

`generate-screening-criteria` · `acquire-corpus` · `appraise-risk-of-bias` · `prisma-flow` · `validate-evidence`
