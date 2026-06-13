---
name: verify-sources
description: Verify that every citation in a research draft is REAL, not retracted, and faithfully represented — by resolving each reference against external bibliographic databases (DOI resolution, retraction/correction/concern check, claim-vs-source fidelity). Use before submitting or trusting any AI-assisted manuscript, literature review, or synthesis, or whenever an LLM has drafted prose containing citations. This is the external-truth gate that complements validate-citations (which only checks internal draft-vs-matrix consistency).
---

# verify-sources

## Purpose

LLM-assisted writing fabricates or corrupts citations at rates reported from ~14% to over 90% depending on model and domain. `validate-citations` catches whether a citation in the draft exists in your *own* extraction matrix — but it cannot tell you whether that reference is **real**, **retracted**, or **faithfully represented**. This skill is the external-truth gate: it checks every citation against the bibliographic record of the world.

**This is the single most important guardrail for any AI-assisted research output.** Run it before a draft is trusted or submitted.

## When to use

- Before submitting or sharing any manuscript, literature review, or research synthesis that contains citations.
- Whenever an LLM has drafted, expanded, or "filled in" prose that contains references.
- As a hard quality gate in `validate-manuscript` and `orchestrate-research` (Phase 5+).
- Ad hoc: "verify the citations in this draft", "check these references are real", "did the model hallucinate any sources?".

## What it checks (three layers)

| Layer | Question | Fail condition |
|:------|:---------|:---------------|
| **1. Existence** | Does this DOI/title resolve to a real publication with matching authors/year/title? | No resolvable record, or metadata mismatch (wrong authors/year/title) → **UNVERIFIED** |
| **2. Integrity** | Has the source been retracted, corrected, or flagged with an editorial concern? | Retraction notice present → **RETRACTED**; correction/concern → **FLAGGED** |
| **3. Fidelity** | Does the draft's claim faithfully represent what the source says (not over/mis-stated)? | Draft asserts support but source contradicts, or claim absent from source → **MISMATCH** |

## Required capabilities

This skill calls **external bibliographic services through a swappable backend** — it does not hardcode one provider, so it works for any agent. Use whichever is available, in this preference order:

1. **scite MCP** (`mcp__scite__search_literature`) — *preferred*. Pass `dois: [...]` (no `term`) to resolve metadata; the response includes `retraction_notices`, `tally` (supporting/contrasting/mentioning Smart Citations), and a `RETRACTED:` title prefix. One call covers existence + integrity + a fidelity signal. Filters `has_retraction`/`has_correction`/`has_concern` also exist.
2. **CrossRef REST API** (`https://api.crossref.org/works/{doi}`) — free, no key. Resolves DOI → title/authors/year/container; `update-to` with `type: retraction` flags retractions. Use via a `command-exec` HTTP call (curl/Python `requests`).
3. **OpenAlex API** (`https://api.openalex.org/works/doi:{doi}`) — free, no key. Metadata + `is_retracted` boolean. Good fallback and good for title→DOI reverse lookup when a citation has no DOI.
4. **Last resort** (no DOI, no API): `web-fetch` the title + authors and confirm a matching record exists on a publisher/Google Scholar page. Mark such citations **UNVERIFIED (manual)** — never silently pass them.

### Backend availability & graceful degradation

**scite is a paid subscription and is often toggled off.** Do not assume it is present. At the start of a run, check whether the `mcp__scite__*` tools are actually available:

- **scite tools present** → use scite (richest: existence + integrity + Smart-Citation fidelity in one call).
- **scite tools absent** → do **not** error, wait, or ask the user to enable it. Fall straight to the **keyless** backend `scripts/resolve_citation.py` (OpenAlex + CrossRef) — it needs no subscription and **fully covers Layers 1 (existence) and 2 (retraction/integrity)**. This is the always-available default.

**What you lose without scite:** the Smart-Citation *fidelity* signal (Layer 3). Existence and retraction checking are unaffected. When scite is off, check fidelity by **abstract only**, and **default borderline/ambiguous claims to MISMATCH (review)** rather than auto-passing — a weaker fidelity backend should make the skill *more* cautious, not silently lenient.

**Always record the backend in the report header** (provenance requirement): a `scite` run and a `keyless` run differ in fidelity depth, so the verification's strength is only interpretable if the reader knows which ran.

> See `references/verification-protocol.md` for per-backend field mappings and a worked scite example. The keyless script is `scripts/resolve_citation.py` — run it as the baseline whenever scite is unavailable.

## Procedure

### Step 1 — Extract citations
Read the target draft. Extract every in-text citation and its bibliography entry. For each, capture: the cited authors + year as written, the DOI if present, the title, and **the specific claim the draft attributes to it** (the sentence the citation supports). Build a working list.

### Step 2 — Resolve each citation (existence + integrity)
For each citation, call the available backend:
- With a DOI → resolve directly.
- Without a DOI → reverse-lookup by title + first author + year (OpenAlex/scite title search), then proceed with the resolved DOI. If no confident match, mark **UNVERIFIED**.
- Record: resolved title, authors, year, journal; whether they **match** the draft's citation (flag author/year/title drift); and any **retraction / correction / concern**.

Batch where the backend allows (scite accepts a `dois` array) to limit calls.

### Step 3 — Check fidelity (claim vs source)
For each resolved, non-retracted citation, test whether the draft's claim is faithful:
- **scite Smart Citations**: if the draft cites the source as *supporting* a claim but the source's `tally` is dominated by *contrasting* citations, or the claim's topic does not appear in the source's abstract/excerpts, flag **MISMATCH (review)**.
- **Abstract check**: fetch the source abstract (scite/OpenAlex returns it); confirm the claim's substance is plausibly supported. This is a heuristic screen, not proof — flag suspicious cases for human review rather than auto-failing.
- Do not over-reach: fidelity is the softest layer. Default to **flag for human review**, not hard-fail, unless the source is clearly off-topic.

### Step 4 — Emit the verification report
Write `verification/source-verification.md` (or alongside the draft). One row per citation:

| Citation (as written) | DOI | Status | Resolved as | Notes |
|:---|:---|:---|:---|:---|
| Smith & Jones 2024 | 10.x/… | ✅ VERIFIED | matches | supporting tally 18/2 |
| Lee 2023 | 10.x/… | ⛔ RETRACTED | retraction 10.y/… | remove or replace |
| Garcia 2022 | — | ⚠️ UNVERIFIED | no resolvable record | likely fabricated — investigate |
| Park 2021 | 10.x/… | ⚠️ MISMATCH | resolves, but source contradicts the claim | re-read source |

Summarize: counts per status, and an **overall gate result**.

### Step 5 — Gate
- **PASS** only if: zero RETRACTED, zero UNVERIFIED, and zero un-reviewed MISMATCH.
- **FAIL** otherwise. Present the failures grouped by severity (retracted/fabricated first). Do not soften: a single fabricated or retracted citation can invalidate a review.
- Gate is reportable but **not silently overridable** — if the user chooses to proceed with known issues, that decision must be logged (see `ai-research-provenance` steering).

## Output

- `verification/source-verification.md` — the per-citation report + gate result.
- A one-line summary for the calling skill: `verify-sources: N citations, X verified, Y retracted, Z unverified, W mismatch — GATE: PASS/FAIL`.

## Provenance

Per `.agent/steering/ai-research-provenance.md`, stamp the report header with: which backend was used (scite MCP / CrossRef / OpenAlex / manual), the date verified, and the model performing the check. External bibliographic databases change (retractions are added over time) — a verification is only valid as of its date; record it.

## Boundaries

- This skill verifies **citations against external records**. It does NOT check internal draft-vs-matrix consistency (that's `validate-citations`), grade evidence (`validate-evidence`), or check cross-phase traceability (`validate-consistency`). `validate-manuscript` runs all of these together.
- It cannot resolve paywalled full text for deep fidelity checks — fidelity beyond abstract level is flagged for human review, not asserted.
- A PASS means "the citations are real, not retracted, and not obviously misrepresented as of today" — not "the argument is correct."

## Related

- `validate-citations` — internal draft↔matrix consistency (run both; they are complementary)
- `validate-manuscript` — batch QA gate that should call this skill
- `orchestrate-research`, `synthesize-research`, `review-literature` — pipelines that should gate on this before "complete"
- `.agent/steering/ai-research-provenance.md` — provenance + disclosure convention
