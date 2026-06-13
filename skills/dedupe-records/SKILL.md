---
name: dedupe-records
description: Deduplicate a merged literature corpus at the record level before screening — DOI-exact, fuzzy-title, and preprint-vs-published reconciliation — and emit the duplicates-removed count for the PRISMA flow. Use after acquire-corpus (or any multi-database/snowball search) and before screen-literature. Standard-library only, no dependencies.
---

# dedupe-records

## Purpose

Cross-database searching and snowballing produce heavy duplication: the same paper from OpenAlex + CrossRef + a snowball edge, or a preprint and its published version. Naive "same DOI" matching misses near-duplicates (missing DOIs, formatting variants, preprint↔published). This skill removes duplicates with a stepwise, validated method and reports the **duplicates-removed count** — a required input to the PRISMA 2020 flow diagram. Bad dedup inflates screening load and corrupts the PRISMA numbers.

## When to use

- After `acquire-corpus` (or any multi-source search), before `screen-literature`.
- Any time you merge record sets from multiple databases or snowball passes.

## Method (after Bramer et al.)

`scripts/dedupe_records.py` applies three steps in order:

1. **Exact DOI** match (normalized — case, `https://doi.org/` prefix stripped).
2. **Fuzzy title** match: normalized-title similarity ≥ threshold (default 0.92) **AND** year within ±1 **AND** shared first-author surname (the author/year guard prevents same-title-different-paper collisions).
3. **Preprint ↔ published reconciliation**: when a duplicate group contains both a preprint (arXiv/bioRxiv/SSRN/preprint DOI or type) and a published record, the **published** record is kept as canonical; among remaining candidates, prefer one with a DOI, then the most-cited.

Each surviving record keeps a `duplicate_of` list of the dropped ids, so the merge is auditable.

## Procedure

```
# JSONL in (from acquire-corpus), deduped JSONL out:
python scripts/dedupe_records.py corpus/candidates.jsonl > corpus/deduped.jsonl

# Human-readable count report (for the PRISMA flow + your records):
python scripts/dedupe_records.py corpus/candidates.jsonl --report > corpus/dedup-report.md
```

Tune `--threshold` (0–1) only with care: lower catches more near-duplicates but risks false merges; the author+year guard makes 0.92 safe for most corpora. Spot-check the `groups_merged` against a sample.

## Output

- `corpus/deduped.jsonl` — the unique record set (input to `screen-literature`).
- `corpus/dedup-report.md` — identified / duplicates-removed / after-dedup counts.
- The three counts feed `prisma-flow` (identification → records after duplicates removed).

## Boundaries

- This is **record-level** dedup of incoming bibliographic records — distinct from the theme/claim-level dedup that happens later during synthesis (`recursive-lit-review` merge gates).
- It does not screen for relevance (`screen-literature`) — a unique record can still be excluded at screening.
- Fuzzy matching is a heuristic; the author+year guard makes it conservative, but a human should sanity-check merged groups on a large or high-stakes corpus.

## Related

- `acquire-corpus` (upstream: produces the merged candidate set)
- `screen-literature` (next: relevance screening of the deduped set)
- `prisma-flow` (consumes the duplicates-removed count)
