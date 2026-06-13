---
name: acquire-corpus
description: Build a literature corpus by searching bibliographic databases and citation-chaining (snowballing), with a PRISMA-S-compliant search log — the front end of a systematic/literature review. Use when starting a review from a question rather than a pre-collected pile of PDFs, when you need a documented, reproducible search, or to expand an existing corpus via backward/forward citation chasing. Keyless by default (OpenAlex/CrossRef); scite MCP is optional enrichment.
---

# acquire-corpus

## Purpose

A rigorous review begins with a **documented, reproducible search** — not a folder of PDFs you happened to have. This skill is the missing front end of the research pipeline: it searches bibliographic databases, snowballs from key papers, and logs every query so the search can be reproduced and reported to the **PRISMA-S** standard. Its output feeds `dedupe-records` → `screen-literature`.

## When to use

- "Find the literature on X" / "build a corpus for a review of X".
- Starting a systematic, scoping, or narrative review from a question.
- Expanding a corpus: backward (references of key papers) and forward (papers citing them) snowballing.
- Any time the review must be reproducible or the search reportable (grant proposals, systematic reviews).

## Backends (keyless by default; scite optional)

| Backend | Role | Key? |
|:--------|:-----|:-----|
| **OpenAlex** (`scripts/search_openalex.py`) | Primary — ~250M works, search + filters + citation edges for snowballing | No |
| **CrossRef** | Secondary metadata / DOI coverage | No |
| **PubMed E-utilities** | Biomedical domain | No |
| **arXiv API** | Physics/CS/math preprints | No |
| **scite MCP** | *Optional* enrichment — Smart Citations, retraction flags during acquisition | **Paid — often off.** Never assume present; degrade to OpenAlex. |

> Multi-database search is a PRISMA/Cochrane requirement — no single index is complete. Run OpenAlex always; add domain databases as the topic warrants, and **record each as a separate source** in the search log.

## Procedure

### Step 1 — Build the search strategy
From the research question + screening criteria (see `generate-screening-criteria`), derive search concepts and a **Boolean strategy** (concept blocks joined by AND, synonyms within a block by OR). Write the strategy down verbatim — it must be reproducible and is itself a PRISMA-S reporting item. For a high-stakes review, have the strategy peer-reviewed (PRESS) before running.

### Step 2 — Run the searches (date-stamped)
For each database, run the strategy and **record the exact query, the date run, and the result count**:
```
python scripts/search_openalex.py search --query "<concept query>" \
    --from 2018-01-01 --to <today> --type article --lang en \
    --max 500 --mailto <you> --run-date <today> > corpus/raw/openalex.jsonl
```
Repeat per database/concept query as needed. Keep each source's output separate so per-source counts are auditable.

### Step 3 — Snowball from key papers
From seed DOIs (the most relevant hits, or known landmark papers), chase citations both ways:
```
python scripts/search_openalex.py snowball --seeds <doi1> <doi2> \
    --direction both --max 200 --mailto <you> >> corpus/raw/snowball.jsonl
```
Snowballing recovers papers keyword search misses; it is an expected supplementary method and must be logged. Citation-graph data is bibliometric (no hallucination risk).

### Step 4 — Merge + hand off
Concatenate all raw JSONL into one candidate set. **Do not dedupe here** — hand the merged set to `dedupe-records` (record-level dedup is its own auditable step whose removed-count feeds the PRISMA flow). Then `screen-literature`.

### Step 5 — Write the PRISMA-S search log
Emit `corpus/search-log.md` capturing, per PRISMA-S: each **database + interface**, the **exact query strings**, **date(s) run**, any **filters/limits** (years, language, type), **records per source**, the **snowball seeds + direction + yield**, and **who/what ran it** (this skill + model, per `ai-research-provenance`). This log is what makes the search reproducible and the review reportable.

## Outputs

- `corpus/raw/*.jsonl` — per-source records (kept separate for auditable counts).
- `corpus/candidates.jsonl` — merged candidate set (input to `dedupe-records`).
- `corpus/search-log.md` — PRISMA-S search documentation (databases, queries, dates, counts, snowball).
- Identification counts (per source + snowball) → the PRISMA flow's "identification" row (`prisma-flow`).

## Boundaries

- This skill **acquires and documents**; it does not screen (`screen-literature`) or dedupe (`dedupe-records`). Keeping these separate is what makes each count auditable.
- Search relevance ranking is the backend's (OpenAlex). For exhaustive systematic reviews, run multiple concept queries and validate recall against a known "gold set" of must-find papers before locking the search.
- Full-text PDF retrieval is separate — records carry DOIs/links; downloading gated PDFs is out of scope.

## Related

- `generate-screening-criteria` (upstream: defines the question + criteria the strategy derives from)
- `dedupe-records` (next: record-level dedup) → `screen-literature` (then: screening)
- `prisma-flow` (assembles the flow from identification + dedup + screening counts)
- `verify-sources` (downstream gate on the final draft's citations)
- `.agent/steering/ai-research-provenance.md` (log the search as an AI-assisted step)
