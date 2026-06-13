# dedupe-records

**Record-level deduplication for a merged literature corpus**, run after searching/snowballing and before screening. Emits the duplicates-removed count the PRISMA flow needs.

## Why it exists

Searching several databases (plus snowballing) surfaces the same paper many times — and as a preprint *and* its published version. Plain "same DOI" dedup misses these. Bad dedup inflates the screening workload and corrupts the PRISMA numbers, so it's its own auditable step.

## What it does

Three steps, in order (after Bramer et al.):
1. **Exact DOI** match.
2. **Fuzzy title** match (similarity ≥ 0.92) guarded by year (±1) and shared first-author surname.
3. **Preprint ↔ published reconciliation** — keeps the published record over the preprint.

Standard-library only (`difflib`), no dependencies. Each kept record records which ids it absorbed.

## Run it

```bash
python scripts/dedupe_records.py corpus/candidates.jsonl > corpus/deduped.jsonl
python scripts/dedupe_records.py corpus/candidates.jsonl --report   # counts for PRISMA
```

## Related

`acquire-corpus` · `screen-literature` · `prisma-flow`
