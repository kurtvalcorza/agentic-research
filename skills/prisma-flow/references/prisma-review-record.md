# Canonical PRISMA systematic-review reporting record

This contract is the structured source from which a systematic-review manuscript can render PRISMA-relevant reporting and from which the evidence-bearing checklist can record its manuscript mapping. It is **not a methodological-quality score**.

The contract is intentionally broader than the legacy location-only checklist. The checklist asks *where* an item is reported; this record carries *what the pipeline knows must be reported*.

## Top-level shape

```json
{
  "schema_version": "1.0",
  "review_identity": {},
  "abstract": {},
  "introduction": {},
  "methods": {},
  "results": {},
  "discussion": {},
  "other_information": {},
  "prisma_mapping": {
    "main_checklist": [],
    "abstract_checklist": []
  }
}
```

Unknown or review-specific extensions should be versioned rather than silently inserted into a `1.0` record.

## Required structured fields

### `review_identity`

- `title`
- `review_type` (`systematic` for this contract)
- `objective`
- `question_framework` and structured question (for example PICO where applicable)

Supports PRISMA main items 1 and 4 and abstract identification/objective reporting.

### `abstract`

- `identifies_as_systematic_review`
- `objective`
- `eligibility_summary`
- `information_sources` and `last_search_dates`
- `risk_of_bias_method_summary`
- `synthesis_method_summary`
- `included_studies_summary`
- `main_results`
- `evidence_limitations`
- `interpretation`
- `funding`
- `registration`

These are the 12 PRISMA 2020 for Abstracts reporting topics consumed by `prisma_abstract_checklist.py`.

### `introduction`

- `rationale`
- `objectives`

Supports main items 3–4.

### `methods`

- `eligibility_criteria`
  - inclusion criteria
  - exclusion criteria
  - synthesis-grouping rules
- `information_sources[]`
  - source/database/register/website/organisation
  - interface/platform where relevant
  - last searched/consulted date
- `search_strategies[]`
  - source
  - complete strategy
  - filters
  - limits
- `selection_process`
  - number/type of reviewers
  - independence
  - disagreement resolution
  - automation details where applicable
- `data_collection_process`
  - number/type of extractors
  - independence
  - investigator-contact/confirmation process
  - automation details where applicable
- `outcomes[]`
  - outcome name/definition
  - measures/time points/analyses sought
  - selection rule when not all compatible results were sought
- `other_variables[]`
  - name/definition
  - missing/unclear-information assumptions
- `risk_of_bias_method`
  - instruments
  - result/study target
  - reviewers and independence
  - automation/human-gate details
- `effect_measures[]`
  - outcome
  - effect measure
- `synthesis_methods`
  - study eligibility per synthesis
  - data preparation/conversion
  - tabular/visual display methods
  - synthesis method and rationale
  - heterogeneity exploration
  - sensitivity analyses
  - software/models where meta-analysis is performed
- `reporting_bias_method`
- `certainty_method`

Supports main items 5–15, including 10a/10b and 13a–13f.

### `results`

- `study_selection`
  - identification/screening/inclusion counts
  - flow artifact reference
  - near-miss/excluded reports and reasons
- `study_characteristics[]`
- `risk_of_bias_results[]`
- `individual_results[]`
  - study/result ID
  - outcome
  - group summary statistics where applicable
  - effect estimate
  - precision/interval where applicable
- `syntheses[]`
  - contributing study characteristics/risk of bias
  - synthesis estimate/precision where applicable
  - heterogeneity results
  - heterogeneity exploration
  - sensitivity-analysis results
- `reporting_bias_results[]`
- `certainty_results[]`

Supports main items 16a–22, including the individual-study information required by item 19 and synthesis sub-items 20a–20d.

### `discussion`

- `general_interpretation`
- `evidence_limitations`
- `review_process_limitations`
- `implications_for_practice_policy_research`

Supports main items 23a–23d.

### `other_information`

- `registration`
  - registry
  - identifier
  - link/reference where applicable
- `protocol`
  - citation/location/access
- `amendments[]`
  - change
  - rationale
- `support`
  - financial/non-financial support
  - sponsor/funder role
- `competing_interests[]`
- `availability`
  - data extraction forms
  - extracted/analyzed data
  - analysis code
  - other materials

Supports main items 24a–27.

## PRISMA mappings

The record does not self-certify. After manuscript rendering, `prisma_mapping.main_checklist` supplies the evidence-bearing 42-row records consumed by `prisma_compliance.py`:

```json
{
  "number": "7",
  "location": "Methods > Search strategy",
  "evidence": "Complete source-specific strategies, filters and limits are rendered from methods.search_strategies.",
  "human_confirmed": true
}
```

`prisma_mapping.abstract_checklist` supplies the 12 abstract records consumed by `prisma_abstract_checklist.py` in `verification: compliance` mode.

The mapping is intentionally downstream of structured data and manuscript rendering: **structured field present** is not the same predicate as **reporting requirement adequately expressed in the finished report**.

## Updated reviews

For an updated systematic review, `results.study_selection.flow` points to a `prisma_updated_flow.py` record. That record carries:

- studies/reports included in the previous review;
- newly identified and newly included evidence;
- new studies/reports included;
- total updated studies/reports included;
- an explicit databases/registers-only or databases/registers-plus-other-methods variant.

## Verification states

A run may report these states independently:

1. **PRISMA-aligned workflow** — standards-aware review pipeline used.
2. **PRISMA reporting checks passed** — applicable machine-checkable addressability/flow invariants passed.
3. **PRISMA compliance-verified record** — all 42 main rows and 12 abstract topics are evidence-bearing and human-confirmed under their respective check contracts.

State 3 still does not mean that PRISMA has certified the review or that the methods are high quality; it means the repository has an auditable reporting-compliance record with the required human gates.
