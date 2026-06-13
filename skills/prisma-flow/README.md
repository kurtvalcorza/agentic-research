# prisma-flow

**Assembles a PRISMA 2020 flow diagram from your review's real counts** and checks that the numbers reconcile end to end.

## Why it exists

The PRISMA flow diagram is the audit trail of how studies were selected. Reviewers reject reviews whose flow numbers don't add up or were drawn by hand from nowhere. This skill builds the diagram from the actual counts the pipeline produced (`acquire-corpus`, `dedupe-records`, `screen-literature`) and **fails the build if the arithmetic doesn't reconcile**.

## What it does

- Renders a Mermaid PRISMA 2020 flow diagram (GitHub/Markdown-renderable) — the databases/registers arm and, when present, a parallel other-methods arm that merges at *studies included*.
- Tabulates full-text exclusions with reasons (a PRISMA requirement).
- Reconciles each arm independently (identified − duplicates = screened; screened − excluded = sought; sought − not-retrieved = assessed; assessed − excluded = included), then the merge. Reports any break with the exact discrepancy.

Standard-library only, no dependencies.

## Run it

```bash
python scripts/prisma_flow.py counts.json --strict   # exit 1 if counts don't reconcile
```

## Related

`acquire-corpus` · `dedupe-records` · `screen-literature` · `orchestrate-research`
