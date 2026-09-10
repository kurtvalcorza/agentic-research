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
- **All 16 items pass. The specification is ready for `/speckit-plan`.**

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

### Verified during validation

- **No implementation details**: requirements name behaviours and artifacts, not languages,
  libraries, or command surfaces. The one architectural constraint that does appear (FR-018,
  "consulted as an external program, never imported") is a constitutional requirement under
  Principle II, not a technology choice.
- **Success criteria technology-agnostic**: SC-002 and SC-003 state wall-clock budgets, which are
  user-observable latency rather than system internals.
- **Fail-closed inversion**: FR-007 departs from Principle IV. The departure is bounded and
  justified in Assumptions, and the fail-closed posture is retained where it bears on the review's
  numbers (FR-008, FR-013, SC-009). This warrants explicit review at the Constitution Check gate in
  `/speckit-plan` rather than passing unremarked.
