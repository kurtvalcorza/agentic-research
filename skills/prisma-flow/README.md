# prisma-flow

PRISMA 2020 reporting support with explicit separation between **workflow alignment**, **machine-checkable reporting invariants**, and **evidence-bearing human-confirmed compliance records**.

## Flow diagrams

`scripts/prisma_flow.py` is the public flow entry point.

- Existing/new-review records continue through the established new-review implementation unchanged.
- Updated reviews must declare one of the explicit variants:
  - `updated_databases_registers`
  - `updated_databases_registers_other_methods`
- Updated-review records carry previous studies/reports, newly included studies/reports, and updated totals. The dispatcher routes them to `scripts/prisma_updated_flow.py` and fails closed on malformed or arithmetically inconsistent records.

The flow diagram is an audit trail of study selection. Reconciliation proves that supplied counts are mutually consistent; it cannot prove that the counts are true.

## Main PRISMA checklist: addressability vs compliance

Two predicates are intentionally separate:

- `scripts/prisma_checklist.py` — the established **addressability** check. It models all 42 addressable PRISMA 2020 rows and verifies that each has a manuscript location or explicit N/A justification.
- `scripts/prisma_compliance.py` — the stronger **evidence-bearing compliance record**. Every located row must carry substantive evidence (a minimum length, and not a verbatim repeat of the location) and every positive/N-A assertion must be human-confirmed. Not-applicable is only accepted for the fixed set of items whose own PRISMA 2020 wording is conditional (`CONDITIONALLY_APPLICABLE`); every other row must be located. A location-only, blanket-N/A, or trivial-evidence record cannot pass this checker.

PRISMA remains a reporting guideline. A clean compliance record is not a methodological-quality score and does not make an expert judgment infallible.

## PRISMA 2020 for Abstracts

`scripts/prisma_abstract_checklist.py` models the separate 12-item PRISMA 2020 for Abstracts checklist. It supports:

- `verification: addressability`
- `verification: compliance`

Compliance mode requires evidence for located items and a human confirmation for every positive or N/A assertion.

## Canonical systematic-review reporting record

`references/prisma-review-record.md` defines the structured reporting contract from which a manuscript can render PRISMA-relevant information and then map the finished text to:

- the 42-row main checklist;
- the 12-item abstract checklist;
- new- or updated-review flow records.

The structured contract covers eligibility, information sources/searches, selection/data collection, outcomes/variables, RoB, effect measures, synthesis, individual-study results, certainty/reporting bias, registration/protocol/amendments, support, competing interests, and data/code/material availability.

## verify-review integration

`../verify-review/scripts/prisma_reporting_checks.py` is the strengthened PRISMA reporting sub-gate. It consumes the JSON envelopes from the abstract and evidence-bearing main-checklist checks and, for updated reviews, the updated-flow checker. When an updated flow is required but not supplied, it reports `U_prisma_updated` as **UNDERIVED** rather than silently treating the missing check as zero.

The generic `VERIFIED` verdict remains a **pipeline-verification predicate**, not PRISMA certification or methodological-quality certification.

## Run

```bash
# New-review flow
python skills/prisma-flow/scripts/prisma_flow.py counts.json --strict

# Updated-review flow (same public entry point; explicit variant in JSON)
python skills/prisma-flow/scripts/prisma_flow.py updated-counts.json --strict

# Legacy/main checklist addressability
python skills/prisma-flow/scripts/prisma_checklist.py checklist.json --strict

# Evidence-bearing main-checklist compliance record
python skills/prisma-flow/scripts/prisma_compliance.py compliance.json --strict

# PRISMA 2020 for Abstracts
python skills/prisma-flow/scripts/prisma_abstract_checklist.py abstract-checklist.json --strict
```

All runnable checks are standard-library only and fail closed on malformed input.

## Standards language

- **aligned** — workflow/material is structured around the standard but no full validator is claimed;
- **enforced** — a runnable checker enforces a defined invariant;
- **human-gated** — a recorded human decision/sign-off is required;
- **compliance-verified record** — all applicable machine-checkable fields and required human confirmations for that reporting contract are present.

None of these terms should be read as endorsement or certification by the PRISMA authors.

## Related

`acquire-corpus` · `dedupe-records` · `screen-literature` · `verify-review` · `orchestrate-research`
