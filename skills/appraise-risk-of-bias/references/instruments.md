# Risk-of-Bias Instruments — Domains & Signaling Questions

Summaries to drive evidence extraction. For high-stakes reviews, consult the full official guidance (linked per tool). The agent extracts evidence for each domain; the **human makes the judgment**.

## Machine-readable domain keys

These are the exact keys and values the appraisal record uses, and the appraisal check enforces
them. **This table and the check must agree** — if you change one, change the other, or the
guidance and the schema drift apart and the prose stops describing what actually runs.

| Design | `instrument` | `domains` keys | Legal values |
|:--|:--|:--|:--|
| `rct` | `rob2` | `randomization`, `deviations`, `missing_data`, `measurement`, `selection_of_result` | `low`, `some_concerns`, `high` |
| `nrsi` | `robins_i` | `confounding`, `participant_selection`, `intervention_classification`, `deviations`, `missing_data`, `outcome_measurement`, `selection_of_result` | `low`, `moderate`, `serious`, `critical`, `no_information` |
| `observational` | `nos` | `selection` (max 4), `comparability` (max 2), `outcome_or_exposure` (max 3) | integer stars within each block's maximum |
| `dta` | `quadas2` | `patient_selection`, `index_test`, `reference_standard`, `flow_and_timing` | `low`, `high`, `unclear` — risk of bias for all four; applicability for the first three |

**Overall judgment** uses the same vocabulary as the domains, except Newcastle-Ottawa, where the
overall band derives from the 9-star total: `low` at 7–9, `moderate` at 4–6, `high` at 0–3. Those
thresholds are conventional rather than definitional, so a recorded justification may override the
band.

Every study also carries `confirmed_by` and `confirmed_at`. The check verifies these are
**present**; it cannot verify that a human wrote them, or which human.

## RoB 2 — Randomized trials (Cochrane, Sterne et al. 2019)
Assesses a **specific result**. Five domains, each with signaling questions → domain judgment (**Low / Some concerns / High**); overall ≈ the worst domain.

1. **Bias arising from the randomization process** — was the allocation sequence random? concealed? baseline imbalances suggesting a problem?
2. **Bias due to deviations from intended interventions** — were participants/carers blind? were there deviations from the intended intervention that affected the outcome? appropriate analysis (ITT)?
3. **Bias due to missing outcome data** — outcome data available for ~all participants? evidence the result was not biased by missingness?
4. **Bias in measurement of the outcome** — method appropriate? outcome assessors blind? assessment likely influenced by knowledge of intervention?
5. **Bias in selection of the reported result** — analysis per a pre-specified plan? result selected from multiple outcome measurements / analyses?

## ROBINS-I — Non-randomized studies of interventions (Sterne et al. 2016; ROBINS-I V2, 2024–25)
Compares to a hypothetical target trial. Seven domains → **Low / Moderate / Serious / Critical / No information**. Pre-intervention domains carry confounding, which is central.

1. **Confounding** — were important confounding domains controlled (design or analysis)?
2. **Selection of participants** into the study — related to intervention and outcome?
3. **Classification of interventions** — defined/recorded without knowledge of the outcome?
4. **Deviations from intended interventions** — that arose because of the study context?
5. **Missing data** — outcomes/interventions/confounders reasonably complete?
6. **Measurement of outcomes** — could it differ between intervention groups? assessor blind?
7. **Selection of the reported result** — from multiple outcomes/analyses/subgroups?

## Newcastle-Ottawa Scale (NOS) — Cohort & case-control
Star system, **max 9**. Award stars across three blocks:

- **Selection** (max 4): representativeness of the exposed/cases; selection of the non-exposed/controls; ascertainment of exposure; (cohort) outcome not present at start.
- **Comparability** (max 2): comparability of cohorts/groups on design or analysis (control for the most important factor; and for additional factors).
- **Outcome (cohort) / Exposure (case-control)** (max 3): assessment of outcome/exposure; adequacy/length of follow-up; adequacy of follow-up completeness.

Common thresholds (study-dependent): good ≈ 7–9, fair ≈ 4–6, poor ≈ 0–3.

## QUADAS-2 — Diagnostic test accuracy
Four domains, each rated for **risk of bias** (Low/High/Unclear); the first three also for **applicability**.

1. **Patient selection** — consecutive/random sample? case-control design avoided? inappropriate exclusions avoided?
2. **Index test** — interpreted without knowledge of the reference standard? threshold pre-specified?
3. **Reference standard** — likely to correctly classify the target condition? interpreted without knowledge of the index test?
4. **Flow and timing** — appropriate interval between index test and reference standard? all patients got a reference standard (the same one)? all included in the analysis?

## How this feeds GRADE
The per-study overall RoB ratings (confirmed by a human) are aggregated by outcome and become the **risk-of-bias** downgrade domain in GRADE certainty (`validate-evidence`): a body of evidence dominated by high-RoB studies is downgraded. GRADE's other domains (inconsistency, indirectness, imprecision, publication bias) are assessed separately there.
