---
name: design-review-protocol
description: Design and pre-specify a review protocol before searching — select the review TYPE (systematic / scoping / rapid / umbrella / narrative), frame the question with the right structured framework (PICO / PEO / SPIDER / PCC), and produce a registrable, PRISMA-P-aligned protocol with pre-specified eligibility, search plan, and synthesis/appraisal methods. Use at the very start of a review, before generate-screening-criteria and acquire-corpus. Outputs a protocol.md ready for PROSPERO / OSF / protocols.io registration.
---

# design-review-protocol

## Purpose

A rigorous review is **pre-specified before it begins** — review type, question, eligibility, search plan, and analysis methods decided up front. This is the primary defense against selective reporting and scope drift, and it determines which reporting guideline and appraisal steps apply downstream. This skill is the true front-of-the-front-end: it produces a **registrable protocol** that everything else derives from. It runs *before* `generate-screening-criteria` (whose criteria operationalize this protocol's eligibility) and `acquire-corpus` (whose search executes this protocol's search plan).

## When to use

- At the very start of a literature/evidence review, before searching.
- "Help me plan / register a systematic review", "what review type should this be?", "write my PROSPERO protocol".
- Any review intended to be reproducible, registrable, or publishable.

## Step 1 — Choose the review type

Match the methodology to the question (each has distinct rigor + reporting rules):

| Type | Use when | Reporting | Certainty rating? |
|:-----|:---------|:----------|:------------------|
| **Systematic** | A focused, answerable effect/association question; exhaustive search + appraisal | PRISMA 2020 | Yes (GRADE) |
| **Scoping** | Map the breadth of evidence / clarify concepts; no effect estimate | PRISMA-ScR | No |
| **Rapid** | Time-sensitive decision; streamlined (fewer databases, single screening) — state the shortcuts | PRISMA 2020 (note deviations) | Sometimes |
| **Umbrella** | Synthesize *existing reviews* on a topic | PRISMA 2020 | Per included reviews |
| **Narrative** | Expert overview without systematic methods | (none formal) | No |

Choosing wrong produces a mislabeled, non-reproducible product — and reviewers reject "systematic" claims without systematic methods.

## Step 2 — Frame the question

Pick the framework that fits the question type:

| Framework | Components | Best for |
|:----------|:-----------|:---------|
| **PICO** | Population, Intervention, Comparator, Outcome | Effectiveness / intervention |
| **PEO** | Population, Exposure, Outcome | Observational / etiology / risk |
| **SPIDER** | Sample, Phenomenon of Interest, Design, Evaluation, Research type | Qualitative / mixed-methods |
| **PCC** | Population, Concept, Context | Scoping reviews |

The framed question deterministically derives the eligibility criteria and the search concepts — fill every component explicitly.

## Step 3 — Pre-specify the protocol (PRISMA-P)

Write `protocol.md` covering the PRISMA-P essentials:
- **Title, review type, question** (framed per Step 2).
- **Eligibility criteria** — population, intervention/exposure, comparator, outcomes, study designs, timeframe, language, setting — each as an explicit include/exclude rule. (These become `generate-screening-criteria`'s input.)
- **Information sources & search plan** — databases to search, the draft Boolean strategy, grey-literature sources, snowballing plan, planned search dates. (These drive `acquire-corpus`.)
- **Screening process** — dual independent? conflict resolution? (→ `screen-literature` dual mode).
- **Data extraction** — what fields; dual extraction? (→ `extract-synthesis`).
- **Risk-of-bias plan** — which instrument(s) for which designs (→ `appraise-risk-of-bias`).
- **Synthesis plan** — narrative/thematic (SWiM) vs meta-analysis, and the criteria for each (→ synthesis skills); certainty assessment (GRADE) if systematic.
- **Amendments** — a versioned change log (protocols evolve; record deviations rather than silently changing).

## Step 4 — Register (or note why not)

- **Systematic reviews of health outcomes** → register on **PROSPERO** (does not accept scoping reviews).
- **Scoping reviews / non-health syntheses** → **OSF Registries** or **protocols.io**.
- Prospective registration is what lets readers detect plan-vs-conduct deviations; it is a PRISMA 2020 item. If not registering, state why in the protocol.

## Step 5 — Declare AI assistance up front

Per `.agent/steering/ai-research-provenance.md` (PRISMA-trAIce), the protocol should state, before the review runs, **which stages will use AI assistance, which model(s), and where humans stay in the loop** — so the eventual `ai-disclosure.md` is planned, not retrofitted.

## Output

- `protocol.md` — the registrable, PRISMA-P-aligned protocol (the source of truth the rest of the pipeline derives from).
- A version/amendment log section (protocols are versioned artifacts).

## Boundaries

- This **plans**; it does not search (`acquire-corpus`), screen (`screen-literature`), or operationalize criteria into a screening file (`generate-screening-criteria` does that from this protocol's eligibility).
- It does not register *for* you on PROSPERO/OSF (those need an account + submission) — it produces the content ready to paste.

## Related

- `generate-screening-criteria` (next: operationalizes this protocol's eligibility into screening-criteria.md)
- `acquire-corpus` (next: executes the search plan) → `dedupe-records` → `screen-literature`
- `appraise-risk-of-bias`, `validate-evidence` (downstream: per the protocol's appraisal/certainty plan)
- `prisma-flow` (downstream: reports the review this protocol defines)
- `.agent/steering/ai-research-provenance.md` (plan the AI disclosure up front)
