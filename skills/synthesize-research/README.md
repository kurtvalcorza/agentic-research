# Synthesize Research

End-to-end research synthesis orchestrator that coordinates specialist agents to transform a corpus of research papers into publication-ready manuscripts.

## What This Does

Manages the complete research synthesis pipeline. By default it starts from a corpus you already have (bring-your-own-PDFs). Optionally, when you start from a research question with no corpus, it can build one first.

**Phase −1 (optional): Review Protocol Design**
Only for registrable / publishable reviews. `design-review-protocol` pre-specifies the review *before* searching — it selects the review TYPE (systematic / scoping / rapid / umbrella / narrative), frames the question with the right structured framework (PICO / PEO / SPIDER / PCC), and produces a registrable, PRISMA-P-aligned `protocol.md` (eligibility, search plan, screening/extraction/RoB/synthesis methods, amendments). Its eligibility feeds screening, its search plan feeds acquisition, and its appraisal plan feeds the risk-of-bias step. Skip this for ad-hoc syntheses; single-pass quick synthesis remains the default.

**Phase 0 (optional): Corpus Acquisition**
Only when starting from a question without a corpus. `acquire-corpus` searches bibliographic databases (OpenAlex keyless primary; CrossRef/PubMed/arXiv; scite MCP optional) and snowballs from seed papers, writing a PRISMA-S search log; `dedupe-records` then removes record-level duplicates (DOI-exact + fuzzy-title + preprint↔published) before screening and emits the duplicates-removed count. Skip this entirely if you already have a `corpus/`.

**Phase 1: Literature Screening**
Evaluates papers against inclusion criteria, identifies relevant studies. Single-pass is the quick default; for rigor it **supports DUAL mode** — two independent screening passes (different model/prompt) plus conflict adjudication, with inter-rater agreement measured by Cohen's kappa (`screen-literature/scripts/kappa.py`, with a `--min-kappa` gate). Dual independent screening is the gold standard; the LLM analogue is two independent passes plus adjudication.

**Phase 2: Data Extraction & Synthesis**
Extracts structured evidence, identifies cross-cutting themes. Single-pass is the quick default; for rigor it **supports DUAL mode** — two independent extraction passes plus reconciliation, kappa-checked the same way as screening.

**Phase 2b (optional): Risk-of-Bias Appraisal (HUMAN-GATED)**
For systematic reviews that grade certainty of evidence. `appraise-risk-of-bias` appraises each included study with the design-appropriate validated instrument (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2). It is **HUMAN-GATED by design**: RoB appraisal is the weakest link for LLMs (~0.62 accuracy), so the agent extracts the signaling-question evidence and proposes a PROVISIONAL rating, and a human confirms or overrides before it is final. The confirmed overall ratings feed the **risk-of-bias domain of GRADE** in `validate-evidence`. Runs after extraction, before drafting. Skip for ad-hoc syntheses that do not grade evidence.

**Phase 3: Section Drafting**
Writes manuscript sections using extracted evidence

**Phase 4: Citation Validation (two gates)**
- *4a — internal:* `validate-citations` verifies every draft citation traces to the extraction matrix.
- *4b — external:* `verify-sources` resolves every citation against bibliographic databases (scite MCP preferred, else CrossRef / OpenAlex) to confirm the source is **real, not retracted, and faithfully represented**. A verify-sources **FAIL blocks completion** — the run is not "complete" until it PASSES, in addition to validate-citations. The two are different layers; both run.
- *4c — verified end-state (optional):* for a submission-ready synthesis, `verify-review` takes the passing Phase 4 snapshot as its cycle 0 and drives the review to a *verified end-state* on a bounded self-correcting loop — repairing one defect at a time until every in-scope defect is 0, then handing off to the human gates (`VERIFIED` / `BLOCKED_ON_HUMAN`). On a quick draft the snapshot alone is enough.

**Phase 5: AI Provenance & Disclosure**
Each phase's automated decisions are provenance-stamped (model / version / prompt) in the execution log, and the run emits an `ai-disclosure.md` artifact (PRISMA-trAIce aligned) per `.agent/steering/ai-research-provenance.md`.

**Phase 6: PRISMA Flow (Reporting)**
`prisma-flow` assembles the real PRISMA 2020 flow diagram (Mermaid) from the actual counts produced by this run — identification (Phase 0 acquire-corpus, if run), duplicates removed (Phase 0 dedupe-records, if run), and records screened / excluded with reasons / included (Phase 1 screen-literature) — and **fails if the arithmetic does not reconcile**. If Phase 0 was skipped, identification is reported as a pre-collected corpus rather than a documented database search; no identification or duplicate numbers are invented.

## Synthesis Method

This pipeline produces a **narrative / thematic synthesis**, not a meta-analysis. It is reported per **SWiM** ("Synthesis Without Meta-analysis", Campbell et al. 2020, BMJ): grouping of studies, the standardized metric / effect-direction used, the synthesis method, how results are presented, a structured findings summary, and synthesis limitations. **Quantitative pooling is out of scope** — if statistical pooling is needed, a human should use a dedicated meta-analysis tool.

## When to Use

- Writing literature reviews or systematic reviews
- Synthesizing research for grant proposals or white papers
- Consolidating findings from multiple studies
- Creating evidence-based manuscripts with proper citations
- Managing large research corpora (10+ papers)

## What You Need

**Required Inputs** (either provide a corpus, or a question + run Phase 0):
- Research papers in `corpus/` directory (PDF, markdown, or text) — **OR** a research question, in which case Phase 0 (`acquire-corpus` → `dedupe-records`) builds the corpus for you.
- Screening criteria in `screening-criteria.md`
- Target sections list in `sections.md`

**Optional**:
- Phase −1 protocol front-end (`design-review-protocol`) for registrable / publishable reviews — pre-specifies type, question, eligibility, search, and appraisal in a `protocol.md`
- Phase 0 acquisition front-end (`acquire-corpus` → `dedupe-records`) when starting from a question rather than a pre-collected corpus
- DUAL mode for screening (Phase 1) and extraction (Phase 2) — two independent passes + adjudication, kappa-checked — for rigor
- Phase 2b risk-of-bias appraisal (`appraise-risk-of-bias`, HUMAN-GATED) when the synthesis grades certainty of evidence (GRADE)
- Custom extraction fields
- Manuscript outline
- Specific formatting requirements

## What You Get

A complete synthesis workspace in `.agent/outputs/synthesis-YYYY-MM-DD/`:

- **(Phase −1, if run) protocol.md**: Registrable, PRISMA-P-aligned review protocol (type, framed question, eligibility, search plan, screening/extraction/RoB/synthesis methods) ready for PROSPERO / OSF / protocols.io
- **(Phase 0, if run) corpus/candidates.jsonl · corpus/search-log.md · corpus/deduped.jsonl · corpus/dedup-report.md**: Acquired candidate records, the PRISMA-S search log, and the deduped record set with duplicates-removed count
- **phase1-report.md**: Screening decisions (Include/Exclude/Uncertain) — DUAL mode adds a kappa agreement report + disagreement list
- **phase2-matrix.md**: Structured extraction table — DUAL mode adds a reconciliation/agreement report
- **phase2-synthesis.md**: Thematic analysis
- **(Phase 2b, if run) phase2b-risk-of-bias.md**: Per-study risk-of-bias appraisal (design-appropriate instrument) with human-confirmed overall ratings feeding GRADE
- **phase3-draft.md**: Full manuscript draft with citations
- **phase4-validation.md**: Internal citation accuracy report (validate-citations)
- **verification/source-verification.md**: External citation verification report with per-citation status (VERIFIED / RETRACTED / UNVERIFIED / FLAGGED / MISMATCH) and a PASS/FAIL gate (verify-sources)
- **ai-disclosure.md**: AI-assistance disclosure artifact (PRISMA-trAIce aligned)
- **prisma-flow.md**: Real PRISMA 2020 flow diagram (Mermaid) assembled from actual identification / duplicates-removed / screening counts, with a reconciliation check that fails if the arithmetic does not balance (prisma-flow)
- **dashboard.md**: Real-time progress tracking

## How to Trigger

Say: **"Synthesize research"** or **"Let's synthesize this corpus"**

The orchestrator will guide you through setup, then coordinate all specialist agents automatically.

## Key Features

- **Specialist Coordination**: Each phase handled by purpose-built agent
- **State Recovery**: Resume interrupted synthesis sessions
- **Dashboard Tracking**: Real-time visibility into progress
- **Citation Integrity**: Only uses citations from validated extraction matrix (internal), and verifies each citation against external bibliographic records via verify-sources (real / not retracted / faithful)
- **Quality Controls**: Built-in validation and consistency checks
- **AI Provenance & Disclosure**: Per-decision provenance stamping + a PRISMA-trAIce `ai-disclosure.md` artifact

## Related

- `design-review-protocol` — optional protocol front-end (Phase −1): selects review type, frames the question (PICO/PEO/SPIDER/PCC), writes a registrable PRISMA-P `protocol.md`; run before criteria/search for registrable reviews
- `appraise-risk-of-bias` — per-study risk-of-bias appraisal (Phase 2b, HUMAN-GATED) with the design-appropriate instrument (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2); confirmed ratings feed the GRADE risk-of-bias domain in `validate-evidence`
- `acquire-corpus` — optional acquisition front-end (Phase 0): database search + snowballing + PRISMA-S search log
- `dedupe-records` — record-level dedup (Phase 0b) after acquisition, before screening; emits the duplicates-removed count
- `prisma-flow` — reporting step (Phase 6): real PRISMA 2020 flow from identification + duplicates-removed + screening counts; fails if counts do not reconcile
- `verify-sources` — external citation verification gate (Phase 4b); blocks completion on FAIL
- `validate-citations` — internal draft↔matrix consistency gate (Phase 4a); complementary (run both)
- `verify-review` — optional verified-end-state loop (Phase 4c) after the snapshot; drives the review to `VERIFIED`/`BLOCKED_ON_HUMAN` for a submission-ready synthesis
- `.agent/steering/ai-research-provenance.md` — provenance stamping + the `ai-disclosure.md` artifact convention
