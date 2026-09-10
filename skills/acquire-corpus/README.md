# acquire-corpus

**The front end of a literature review** — builds a documented, reproducible candidate corpus from a keyless OpenAlex baseline, with optional OpenResearch (`orx discover`) enrichment.

The generated search documentation is **PRISMA-S-aligned guidance, not compliance-verified**.

## What it does

1. Runs the guaranteed keyless OpenAlex search path.
2. When `orx` is available, optionally adds alphaXiv full-text keyword retrieval, alphaXiv semantic retrieval, OpenAlex discovery, and bioRxiv discovery.
3. Preserves every source separately, then merges records into `corpus/candidates.jsonl` **without deduplicating**.
4. Generates one canonical `corpus/acquisition-record.json` plus `corpus/search-log.md`.
5. Holds enriched hits out of the candidate set when their authors/year cannot be safely resolved for downstream deduplication.

OpenResearch discovery is optional. No daemon, account, token, or package import is required for the guaranteed path; if `orx` is absent or an enriched source fails, acquisition continues keyless.

## Run the orchestrated acquisition

```bash
python scripts/acquire_corpus.py \
  --query "AI tutoring K-12" \
  --from 2018-01-01 \
  --type article \
  --max 500 \
  --mailto you@example.com \
  --run-date 2026-09-10
```

By default, all supported `orx discover` strategies are attempted when the executable is present. Restrict them by repeating `--orx-source`:

```bash
python scripts/acquire_corpus.py \
  --query "AI tutoring K-12" \
  --orx-source keyword \
  --orx-source embedding
```

Force the guaranteed baseline even if OpenResearch is installed:

```bash
python scripts/acquire_corpus.py \
  --query "AI tutoring K-12" \
  --keyless-only
```

The low-level OpenAlex search/snowball interface remains available unchanged:

```bash
python scripts/search_openalex.py search \
  --query "AI tutoring K-12" --max 500 --mailto you@example.com

python scripts/search_openalex.py snowball \
  --seeds 10.xxxx/yyyy --direction both --max 200 --mailto you@example.com
```

## Outputs

- `corpus/raw/openalex-qNNN.jsonl` — keyless OpenAlex results by query.
- `corpus/raw/orx-<strategy>-qNNN.json` — raw valid JSON returned by OpenResearch.
- `corpus/raw/orx-<strategy>-qNNN.normalized.jsonl` — normalized enriched records before safe admission.
- `corpus/candidates.jsonl` — keyless records plus enriched records that satisfy the safe-admission minimum.
- `corpus/enrichment-unresolved.jsonl` — enriched discoveries withheld because authors/year could not be safely resolved.
- `corpus/acquisition-record.json` — canonical, closed-schema query/provenance/count record.
- `corpus/search-log.md` — human-readable log generated from the acquisition record.

If `enrichment-unresolved.jsonl` is non-empty, review it before treating acquisition as complete. Those records are **not** candidates and must not enter screening until bibliographic resolution provides a usable title, non-empty verified authors, and a verified year.

## Disclosure gate

```bash
python scripts/acquisition_disclosure.py corpus/acquisition-record.json --strict
python scripts/acquisition_disclosure.py corpus/acquisition-record.json --strict --json
```

Exit codes follow the repository-wide gate contract:

- `0` — clean, or issues found without `--strict`
- `1` — disclosure/method violation under `--strict`
- `2` — malformed input

The gate checks disclosure structure and internal consistency. It cannot verify whether provenance is truthful, whether file counts match files on disk, whether metadata resolution is correct, or whether the search achieved adequate recall.

## Safety and reproducibility behavior

Unknown top-level `LitHit` fields fail closed for that enriched response. A hard failure opens that sub-source's circuit for the rest of the run, preventing repeated failed calls. Cumulative enrichment failure waiting is capped at 15 seconds per run.

A successful enriched search records the OpenResearch version and appears in the reproducibility disclosure. A degraded run is explicitly distinguishable in `search-log.md` from a reviewer-selected `--keyless-only` run.

## Related

`generate-screening-criteria` · `dedupe-records` · `screen-literature` · `prisma-flow` · `verify-sources`
