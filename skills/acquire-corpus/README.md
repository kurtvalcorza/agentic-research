# acquire-corpus

**The front end of a literature review** — searches bibliographic databases and snowballs from key papers to build a documented, reproducible corpus, with a PRISMA-S-compliant search log.

## Why it exists

A review's credibility starts with the search. "Here are some PDFs I had" is not a search; a systematic/literature review needs a documented, multi-database, reproducible strategy. This skill provides that front end (the pipeline previously assumed you'd already collected the corpus by hand).

## What it does

1. Builds a Boolean search strategy from your question + criteria.
2. Searches databases (OpenAlex primary — keyless; CrossRef/PubMed/arXiv as the topic needs).
3. Snowballs: backward (references of key papers) and forward (papers that cite them).
4. Writes a PRISMA-S search log (databases, exact queries, dates run, per-source counts, snowball yield).

Output feeds `dedupe-records` → `screen-literature`, and the identification counts feed the real PRISMA flow diagram.

## Keyless by default

The `search_openalex.py` script needs no API key and no subscription — OpenAlex covers ~250M works and carries the citation edges used for snowballing. The scite MCP is optional enrichment (Smart Citations / retraction flags) and is skipped automatically when off.

## Run it

```bash
# Search
python scripts/search_openalex.py search --query "AI tutoring K-12" \
    --from 2018-01-01 --type article --max 500 --mailto you@example.com --run-date 2026-06-13

# Snowball from seed DOIs
python scripts/search_openalex.py snowball --seeds 10.xxxx/yyyy --direction both --max 200 --mailto you@example.com
```

## Related

`generate-screening-criteria` · `dedupe-records` · `screen-literature` · `prisma-flow` · `verify-sources`
