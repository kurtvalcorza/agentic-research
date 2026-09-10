# Specification Quality Checklist: orx Discovery Backend for acquire-corpus

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-09
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`
- **All 16 items pass on content.** One governance question is open and recorded in the spec's
  "Open maintainer decision" section. It is not a `[NEEDS CLARIFICATION]` marker because the
  specification is conforming as written; the decision is whether to relax it by amendment.

### Resolved

Both `[NEEDS CLARIFICATION]` markers were answered by the maintainer on 2026-09-10:

- **FR-016** — records lacking a DOI are **admitted and tagged**, not excluded. Chosen for recall.
  The downstream cost is accepted, not avoided: `dedupe-records` matches them on title alone and
  `verify-sources` cannot resolve them. FR-022 and FR-023 were added so the quantity and the cost
  are disclosed at acquisition rather than discovered at the gate that stalls on them.
- **FR-017** — the reproducibility disclosure gets a **runnable gate**, not a guidance note.
  FR-024 through FR-027 were added to bind it to the shared exit-code contract, to keep it silent on
  keyless corpora, to require it to state what it cannot verify, and to stop it being read as a
  PRISMA-S compliance claim.

Both answers grew the feature: 21 functional requirements became 27, and 9 success criteria became
12. The size increase is in the disclosure obligations the answers created, not in new capability.

### Review round 1 — findings at `faeb664`, all five upheld

Verified against primary sources before acting; two of the corrections revise claims this
specification had asserted, and two revise claims made in the review itself.

- **Availability model was stale.** Upstream documents discovery as "No login is required" and
  "exactly one public endpoint request" — there is no local daemon. FR-001, FR-002, Story 2
  scenario 3, SC-003 and the edge cases are rewritten; the service-down latency criterion is gone.
  The corrected premise is *better* for Principle II: enrichment adds an executable, not an
  authentication dependency.
- **Gate contract mismatch.** A gate cannot read JSONL plus Markdown under a contract expecting one
  JSON object. Resolved as the constitution's artifact-generation rule already required: new FR-028
  makes a structured acquisition record the source of truth, FR-029 generates the Markdown log from
  it, and FR-024 has the gate read one closed-schema JSON object.
- **FR-007 vs Principle IV.** Deferring to the Constitution Check did not resolve it. FR-007 is
  rewritten in a conforming form and the underlying governance question is recorded as an **open
  maintainer decision** rather than assumed. See the spec's closing section.
- **Corpus shape — upheld and understated.** Upstream guarantees only source, id, title, abstract
  and publication date; authors, DOI, venue and type are not guaranteed, while `dedupe_records.py`
  documents its minimum as doi/title/year/authors. The consequence is sharper than "a weaker guard":
  the guards are written `author_ok = (not sn or not csn) or sn == csn`, so absent fields make them
  **vacuously true**. They degrade *open*, not closed — such records match on title similarity alone
  and can be **falsely merged** with a distinct same-titled paper, deflating records-screened and
  dropping a study. FR-006 now demands an explicit per-field mapping; FR-022 requires the exposure
  to be counted and disclosed.
- **FR-023 overstated `verify-sources` — and the correction needed one more step.** The reviewer is
  right that `resolve_citation.py` offers `--title/--author/--year` reverse lookup. But its candidate
  filter is `(not author or author.lower() in wa)`, so the *same* missing author field weakens that
  path too, yielding its "review manually" outcome more often. FR-023 now says these records cannot
  be resolved *directly by DOI*, that reverse lookup remains available but weakened, and that a
  higher proportion will stay UNVERIFIED.

Net: 27 functional requirements became 30, 12 success criteria became 13.

### Verified during validation

- **No implementation details**: requirements name behaviours and artifacts, not languages,
  libraries, or command surfaces. The one architectural constraint that does appear (FR-018,
  "consulted as an external program, never imported") is a constitutional requirement under
  Principle II, not a technology choice.
- **Success criteria technology-agnostic**: SC-002 and SC-003 state wall-clock budgets, which are
  user-observable latency rather than system internals.
- **Fail-closed scope**: FR-007 no longer claims an exemption from Principle IV. It reads a declared
  field mapping, derives no verdict from the payload, and leaves every artifact the feature
  *produces* closed-schema and fail-closed (FR-028, FR-024). The residual question is one of
  principle scope, not of this feature's conformance, and is recorded in the spec.
