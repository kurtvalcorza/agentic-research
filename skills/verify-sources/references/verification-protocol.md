# verify-sources — Backend Protocol & Field Mappings

This reference gives per-backend specifics for resolving and checking a citation. The skill is backend-agnostic; use whichever is available (preference order in SKILL.md).

## Backend 1 — scite MCP (preferred, but often off)

> **Availability:** scite is a paid subscription the vault owner toggles on/off. If `mcp__scite__search_literature` is not in the available tool set, skip this backend entirely and use Backend 2/3 (the keyless `scripts/resolve_citation.py`). Never block or prompt to enable it — degrade per the SKILL.md "Backend availability & graceful degradation" section.

**Tool:** `mcp__scite__search_literature`

**Resolve metadata + integrity in one call** — pass `dois` (array), omit `term`:
```
mcp__scite__search_literature(dois: ["10.1016/S0140-6736(97)11096-0"], limit: 1)
```

**Field mapping:**
| Need | scite field |
|:-----|:------------|
| Title | `hits[].title` (a `RETRACTED:` prefix means retracted) |
| Authors | `hits[].authors[].authorName` |
| Year / journal | `hits[].year`, `hits[].journal` |
| **Retraction** | `hits[].retraction_notices` (array of retraction-notice DOIs; present ⇒ retracted) |
| Correction / concern | filters `has_correction: true` / `has_concern: true`, or the notices array |
| **Fidelity signal** | `hits[].tally` → `{supporting, contrasting, mentioning}` Smart Citation counts |
| Abstract (fidelity) | `hits[].abstract` |
| Access link | `hits[].access.url` |

**Worked example (verified 2026-06-13):** resolving the Wakefield 1998 MMR paper
`dois: ["10.1016/S0140-6736(97)11096-0"]` returned:
- `title: "RETRACTED: Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasive developmental disorder in children"`
- `retraction_notices: ["10.1016/s0140-6736(10)60175-4"]`
→ Status: **RETRACTED**. Resolving NumPy (`10.1038/s41586-020-2649-2`) returned full metadata, no `retraction_notices`, `tally.supporting` present → **VERIFIED**.

**Fidelity heuristic with Smart Citations:** call with a `term` (the claim's key concept) + the `dois` to pull `fulltextExcerpts` matching the claim; if empty AND the abstract doesn't cover the claim, flag **MISMATCH (review)**. If the draft frames the source as supporting but `tally.contrasting >> tally.supporting`, flag for review.

## Backend 2 — CrossRef REST API (free, no key)

```
GET https://api.crossref.org/works/{doi}
```
- Existence: HTTP 200 + `message.title`, `message.author`, `message.published.date-parts` (year), `message.container-title`.
- Retraction: `message.update-to[]` where `type == "retraction"` (or `"correction"`). Also `message.relation` may carry `is-retracted-by`.
- Title→DOI reverse lookup: `GET https://api.crossref.org/works?query.bibliographic={title}&query.author={author}&rows=3` then match year.
- Call via `command-exec`: `curl -s "https://api.crossref.org/works/{doi}"` or Python `requests`. Be polite: add a `mailto` param (`?mailto=...`) for the polite pool.

## Backend 3 — OpenAlex API (free, no key)

```
GET https://api.openalex.org/works/doi:{doi}
GET https://api.openalex.org/works/https://doi.org/{doi}
```
- Existence: `title`, `authorships[].author.display_name`, `publication_year`, `primary_location.source.display_name`.
- **Retraction**: `is_retracted` (boolean) — clean and direct.
- Title→DOI reverse lookup: `GET https://api.openalex.org/works?search={title}&per_page=3`, match author + year.
- Abstract: `abstract_inverted_index` (reconstruct) for a fidelity screen.

## Backend 4 — manual (last resort)

No DOI and no API reachable: `web-fetch` `"{title}" {first-author} {year}` and confirm a matching publisher/Scholar record. Mark **UNVERIFIED (manual)** and require human confirmation — never auto-pass.

## Status decision table

| Resolves? | Metadata matches draft? | Retracted? | Fidelity | Status |
|:--|:--|:--|:--|:--|
| No | — | — | — | **UNVERIFIED** (likely fabricated) |
| Yes | No (author/year/title drift) | — | — | **UNVERIFIED** (mis-cited or wrong record) |
| Yes | Yes | Yes | — | **RETRACTED** |
| Yes | Yes | Correction/concern | — | **FLAGGED** |
| Yes | Yes | No | Source contradicts / off-topic | **MISMATCH (review)** |
| Yes | Yes | No | Plausibly supported | **VERIFIED** |

## Rate / batch notes

- scite: batch `dois` arrays; keep `limit` small (you're resolving known DOIs, not searching).
- CrossRef/OpenAlex: one request per DOI; throttle to a few/sec; use the polite pool (mailto). For large bibliographies, write a small Python script that iterates the citation list and emits the report table.
- Cache resolved metadata in the run workspace so re-runs don't re-hit the APIs.
