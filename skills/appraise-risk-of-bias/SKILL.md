---
name: appraise-risk-of-bias
description: Appraise the risk of bias of each included study using the design-appropriate validated instrument (RoB 2 for RCTs, ROBINS-I for non-randomized interventions, Newcastle-Ottawa for observational, QUADAS-2 for diagnostic accuracy), as a HUMAN-GATED step — the agent extracts the signaling-question evidence and proposes a provisional rating, the human makes the final judgment. Feeds the risk-of-bias domain of GRADE certainty grading. Use after extraction and before evidence grading in a systematic review.
---

# appraise-risk-of-bias

## Purpose

Including studies without weighting their internal validity treats high- and low-bias evidence identically. A systematic review assesses **risk of bias (RoB) per study** with the **design-appropriate validated instrument**, and that assessment is what feeds the "risk of bias" downgrade in GRADE certainty (`validate-evidence`). This skill runs that appraisal.

## ⚠️ This is a HUMAN-GATED step — by design

The LLM-assisted-review literature is consistent on one point: **risk-of-bias appraisal is where LLMs are weakest** (reported accuracy ~0.62, far below extraction ~0.95), because it requires judgment about how a study was *conducted*. So this skill does **not** auto-rate. It:

1. **Extracts the evidence** for each signaling question from the paper (the agent is good at this).
2. **Proposes a provisional rating** with its reasoning, clearly marked PROVISIONAL.
3. **Requires a human to confirm or override** every domain judgment and the overall rating before the appraisal is "final" and feeds GRADE.

An appraisal with unconfirmed machine ratings is **not** a completed appraisal. Log the human confirmation/override per `.agent/steering/ai-research-provenance.md`.

## Select the instrument by study design

| Study design | Instrument | Judgments |
|:-------------|:-----------|:----------|
| Randomized controlled trial | **RoB 2** (Cochrane) | Low / Some concerns / High — per domain + overall |
| Non-randomized study of an intervention | **ROBINS-I** | Low / Moderate / Serious / Critical / No information |
| Observational (cohort / case-control) | **Newcastle-Ottawa Scale** | Stars (max 9) across Selection / Comparability / Outcome(Exposure) |
| Diagnostic test accuracy | **QUADAS-2** | Risk of bias (Low/High/Unclear) + Applicability, per domain |

> RoB 2 and ROBINS-I assess a **specific result**, not the study as a whole — appraise the result/outcome that feeds your synthesis. See `references/instruments.md` for the domains + signaling questions of each.

## Procedure

### Step 1 — Classify each included study's design
From the extraction matrix (or the paper), determine the design and pick the instrument. Mixed corpora will use more than one instrument — that's expected.

### Step 2 — Extract signaling-question evidence (agent)
For each study, for each domain of the chosen instrument, locate and quote the relevant text (method of randomization, allocation concealment, blinding, attrition, outcome measurement, pre-registration, confounding control, etc.). Cite page/section. Where the paper is silent, record "no information" — do not infer.

### Step 3 — Propose a provisional rating (agent, marked PROVISIONAL)
For each domain, suggest a judgment with one-line reasoning grounded in the extracted evidence. Then a provisional overall rating per the instrument's algorithm (e.g., RoB 2 overall = worst domain, roughly). Mark everything **PROVISIONAL — awaiting human confirmation**.

### Step 4 — Dual appraisal where feasible
Like screening and extraction, RoB is ideally done by **two independent assessors**. If running a second pass (second model/prompt), compare and surface disagreements for the human to resolve. At minimum, the human is the second assessor.

### Step 5 — HUMAN GATE
Present the worksheet. The human confirms or overrides each domain + the overall. **Nothing proceeds to GRADE until this is done.** Record overrides (provenance).

### Step 6 — Emit the appraisal + hand to GRADE
Write `appraisal/risk-of-bias.md`: a per-study table (study → instrument → domain ratings → overall → confirmed-by) + a traffic-light summary. Hand the confirmed overall ratings to `validate-evidence` as the "risk of bias" input to GRADE.

## Output

- `appraisal/risk-of-bias.md` — per-study domain + overall ratings, with extracted evidence and the human confirmation status.
- A RoB summary (traffic-light table) for the manuscript.
- Confirmed overall ratings → `validate-evidence` (GRADE risk-of-bias domain).

## Boundaries

- This appraises **internal validity (risk of bias)** of individual studies. It is not GRADE itself (that's `validate-evidence`, which combines RoB with inconsistency, indirectness, imprecision, publication bias across the body of evidence).
- It does not select studies (`screen-literature`) or extract data (`extract-synthesis`) — it consumes their output.
- The instruments are applied as the official tools intend; `references/instruments.md` summarizes domains but the human assessor should know the full guidance for high-stakes reviews.

## Related

- `extract-synthesis` (upstream: provides study characteristics/design)
- `validate-evidence` (downstream: GRADE certainty, consumes the confirmed RoB ratings)
- `screen-literature`, `acquire-corpus`, `prisma-flow` (the rest of the systematic-review pipeline)
- `.agent/steering/ai-research-provenance.md` (log the appraisal as AI-assisted + the human confirmations)
