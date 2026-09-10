---
name: acquire-corpus
description: Build a literature corpus from a review question using a guaranteed keyless OpenAlex baseline, optional OpenResearch discovery enrichment, citation chaining, and PRISMA-S-aligned search documentation. Use when starting a systematic, scoping, rapid, umbrella, or narrative review from a question rather than a pre-collected corpus.
---

# acquire-corpus

## Purpose

A review begins with a documented search, not an arbitrary folder of papers. `acquire-corpus` builds the candidate set, preserves source-level provenance, and hands the merged records to `dedupe-records`.

The guaranteed path is keyless and standard-library-only. OpenResearch (`orx discover`) is optional enrichment. Its absence or failure never blocks the keyless baseline.

> **Standards status:** the skill produces PRISMA-S-aligned search documentation. It does not certify PRISMA-S compliance.

## Backends

| Backend | Role | Requirement |
|:--|:--|:--|
| OpenAlex | Guaranteed baseline search; metadata completion; snowballing | Free, unauthenticated |
| CrossRef / PubMed / arXiv | Topic-dependent secondary sources used by the broader acquisition workflow | Free/public where applicable |
| `orx discover keyword` | Optional alphaXiv full-text keyword enrichment | `orx` executable only |
| `orx discover embedding` | Optional alphaXiv semantic enrichment | `orx` executable only |
| `orx discover openalex` | Optional OpenResearch OpenAlex discovery | `orx` executable only |
| `orx discover biorxiv` | Optional bioRxiv discovery through OpenResearch | `orx` executable only |
| scite MCP | Optional citation-context/retraction enrichment where separately available | Optional authenticated service |

OpenResearch literature discovery uses public endpoints and does not require a local daemon or login. Do not prompt the reviewer to install it merely because it is absent.

## Procedure

### 1. Build the search strategy

Derive concept blocks and exact query strings from the review question and screening criteria. Preserve every submitted query verbatim in the acquisition record.

For high-stakes systematic reviews, peer-review the strategy (for example with PRESS) before executing it.

### 2. Run orchestrated acquisition

```bash
python scripts/acquire_corpus.py \
  --query "<query>" \
  --from <YYYY-MM-DD> \
  --to <YYYY-MM-DD> \
  --type article \
  --lang en \
  --max 500 \
  --mailto <email> \
  --run-date <YYYY-MM-DD>
```

Repeat `--query` for multiple concept queries.

Behavior:

- OpenAlex runs as the guaranteed baseline.
- If `orx` is present, supported discovery strategies run as optional enrichment.
- Use repeated `--orx-source keyword|embedding|openalex|biorxiv` to restrict strategies.
- Use `--keyless-only` to prohibit all enriched discovery even when `orx` is installed.
- Do not deduplicate during acquisition.

### 3. Enriched-response handling

Treat current upstream `LitHit` top-level fields as a version-sensitive external contract.

Supported top-level fields are:

`source`, `id`, `title`, `abstract`, `publicationDate`, `votes`, `citations`, `snippets`.

Unknown top-level fields fail closed for that response. The affected sub-source circuit opens for the rest of the run and the query remains represented by the keyless baseline.

Every enriched hit must have a supported source, stable source identifier, and usable title before normalization. Missing optional bibliographic fields are never fabricated.

### 4. Safe admission

An enriched record may enter `corpus/candidates.jsonl` only after it has:

- a usable title;
- a non-empty **verified** authors list; and
- a **verified** year.

A DOI is preferred but not mandatory. When no DOI resolves, retain the stable enriched `source_id` and mark the admitted record `identifier_less: true`.

Metadata completion may use the skill's keyless bibliographic sources. Do not substitute `authors: []`, year `0`, null placeholders, or invented values merely to satisfy downstream shape.

If the minimum cannot be satisfied, write the hit to `corpus/enrichment-unresolved.jsonl` with its available discovery metadata and a machine-readable reason. Keep it out of `candidates.jsonl`.

When the unresolved count is non-zero, surface the count and path to the reviewer. It is a triage handoff, not an alternate candidate stream. The record must not enter screening until later bibliographic resolution satisfies the safe-admission minimum.

### 5. Failure bounding

Each `orx discover` call has a five-second deadline. Timeout, network/command failure, or unsupported schema opens the affected sub-source circuit for the remainder of the run. Do not automatically retry that sub-source.

Cumulative enrichment failure waiting may not exceed 15 seconds per run. Remaining work continues keyless.

Do not print OpenResearch warnings, errors, installation prompts, or suggestions merely because optional enrichment is absent or unusable. Method-significant degradation is instead recorded in the acquisition artifacts.

### 6. Inspect canonical acquisition artifacts

`corpus/acquisition-record.json` is the structured source of truth. `corpus/search-log.md` is generated from it and must preserve, per query:

- backend and sub-source;
- strategy and submitted query;
- run date;
- outcome (`answered`, `empty`, `failed-and-fell-back`, `skipped-circuit-open`);
- returned, admitted, unresolved, and normalization-drop counts;
- circuit state; and
- OpenResearch version when used.

If enrichment failed or a circuit prevented a later attempt, the generated log must say so at run level. It must be possible to distinguish that degraded run from a reviewer-selected `--keyless-only` run.

When enrichment succeeds, the acquisition record and generated log must state that fully reproducing those search steps requires OpenResearch and identify the affected query/strategy/source/version.

### 7. Run the disclosure gate

```bash
python scripts/acquisition_disclosure.py corpus/acquisition-record.json --strict
```

Use `--json` when a machine-readable shared-envelope result is required.

The gate follows the repository contract: exit `0` clean/non-strict, `1` method violation under strict, `2` malformed input.

It checks only disclosure structure/internal consistency. It cannot establish that:

- provenance or version strings are truthful;
- backend/source attribution is correct;
- candidate/raw artifact counts equal the files on disk;
- metadata resolution is bibliographically correct;
- source ranking is transparent;
- recall is adequate; or
- the search is PRISMA-S compliant.

### 8. Snowball where required

The existing low-level backend remains available:

```bash
python scripts/search_openalex.py snowball \
  --seeds <doi1> <doi2> \
  --direction both \
  --max 200 \
  --mailto <email>
```

Record snowball seeds, direction, date, and yield. Keep these raw records source-separated before merging.

### 9. Hand off to deduplication

`corpus/candidates.jsonl` feeds `dedupe-records`.

Do not perform cross-source deduplication in this skill. The separation keeps identified counts and duplicate-removal counts auditable.

## Outputs

- `corpus/raw/*.jsonl` / `*.json` — source-specific raw and normalized acquisition evidence.
- `corpus/candidates.jsonl` — automatic candidate set.
- `corpus/enrichment-unresolved.jsonl` — enriched evidence requiring reviewer/later resolution.
- `corpus/acquisition-record.json` — canonical structured provenance/count record.
- `corpus/search-log.md` — generated PRISMA-S-aligned human-readable search documentation.
- Per-source identification counts for `prisma-flow`.

## Boundaries

- Acquisition is not screening and is not deduplication.
- This feature does not modify `dedupe-records` or `verify-sources`.
- OpenResearch ranking/truncation can be opaque.
- Discovery enrichment does not establish exhaustive recall.
- Full-text retrieval/reading through `orx paper` is outside this workflow.
- An unresolved discovery is evidence worth triaging, not permission to bypass bibliographic safeguards.
- No gate here upgrades the skill from PRISMA-S alignment/guidance to compliance verification.

## Related

- `generate-screening-criteria`
- `dedupe-records`
- `screen-literature`
- `prisma-flow`
- `verify-sources`
- `steering/ai-research-provenance.md`
