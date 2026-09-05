# SKILLS-REGISTRY

Decision trees and the skill index for the agentic-research pipeline. Agents: consult this to route a request to the right skill. For a live inventory, list `skills/` — each `SKILL.md` frontmatter carries its `name` + `description`.

---

## Decision tree — running a review

```
Start: "review the literature on [topic]" / "I need a systematic review"
│
├─ Need routing help / a full end-to-end run?
│  ├─ orchestrate-research (master router, auto-config)
│  ├─ synthesize-research (screen → extract → draft → validate pipeline)
│  └─ review-literature (8-phase hybrid human+AI pipeline)
│
├─ Registrable / systematic review? → PROTOCOL FIRST
│  └─ design-review-protocol (review type: systematic/scoping/rapid/umbrella/
│     narrative; frame PICO/PEO/SPIDER/PCC; registrable PRISMA-P protocol.md)
│        ├─ generate-screening-criteria (operationalize the protocol's eligibility)
│        └─ optional strict intervention profile → cochrane-intervention
│
├─ Have a corpus yet?
│  ├─ NO (start from a question) → acquire-corpus (multi-DB search + snowball +
│  │     PRISMA-S log) → dedupe-records (DOI/fuzzy/preprint dedup)
│  └─ YES (PDFs/records in hand) → straight to screening
│
├─ Screening
│  ├─ Quick → screen-literature (single pass)
│  └─ Systematic → screen-literature DUAL mode (two independent passes +
│     Cohen's kappa via kappa.py + conflict adjudication)
│
├─ Extraction → extract-synthesis (single, or DUAL + reconcile + human numeric check)
│
├─ Appraisal (systematic) → appraise-risk-of-bias (RoB2/ROBINS-I/NOS/QUADAS-2,
│     HUMAN-GATED) → feeds validate-evidence
│
├─ Synthesis & certainty
│  ├─ structure-arguments / recursive-lit-review (theme-driven synthesis, SWiM)
│  └─ validate-evidence (legacy GRADE compatibility or current/full GRADE profile;
│     risk-of-bias domain from appraisal)
│
├─ Drafting → draft-section → write-manuscript (with enhance-writing, tools-for-thought,
│     frame-contributions for contribution framing)
│
├─ Validation (before submission)
│  ├─ Want a SNAPSHOT (single pass)?
│  │  ├─ validate-citations (INTERNAL: draft ↔ extraction matrix)
│  │  ├─ verify-sources (EXTERNAL: DOI resolution + retraction + claim fidelity — the
│  │  │     hard gate against fabricated/retracted sources)
│  │  ├─ validate-consistency (cross-phase traceability)
│  │  └─ validate-manuscript (batch: citations + evidence + consistency)
│  └─ Want a VERIFIED END-STATE (loop until clean, then hand off to humans)?
│     └─ verify-review (units-remaining loop over the checks above; weights citation
│        integrity ×3; profile-aware registration for Cochrane/current GRADE;
│        stops at VERIFIED | BLOCKED_ON_HUMAN | PLATEAU | CEILING;
│        runnable backend review_units.py)
│
└─ Reporting → prisma-flow (PRISMA 2020 flow from REAL counts, reconciliation-gated)
```

## Decision tree — citation checking

```
"check these citations" / "did the model hallucinate sources?"
│
├─ Against my own extraction matrix (internal consistency) → validate-citations
└─ Against the real bibliographic record (real? retracted? faithful?) → verify-sources
   (run BOTH — they are complementary layers)
```

## Provenance (always)

Any run that screens, extracts, appraises, drafts, or verifies follows
`steering/ai-research-provenance.md`: per-decision model/version/prompt stamping
and a mandatory `ai-disclosure.md` artifact (PRISMA-trAIce; ICMJE — disclose
substantive AI assistance, never list AI as an author). Gate overrides are logged.

## Keyless vs scite

All runnable backends use free APIs (OpenAlex, CrossRef) + Python stdlib. The
scite MCP (paid) is optional enrichment for citation fidelity; skills detect its
absence and fall back to the keyless scripts automatically.

## Skill index

| Skill | Stage | Script |
|:------|:------|:-------|
| design-review-protocol | protocol | — |
| generate-screening-criteria | protocol | — |
| cochrane-intervention | systematic-review profile (MECIR-oriented) | cochrane_profile.py |
| acquire-corpus | search | search_openalex.py |
| dedupe-records | dedup | dedupe_records.py |
| screen-literature | screening | kappa.py |
| extract-synthesis | extraction | — |
| appraise-risk-of-bias | appraisal (human-gated) | rob_appraisal.py |
| validate-evidence | grading (GRADE) | grade_profile.py, grade_profile_current.py |
| structure-arguments | synthesis/drafting | — |
| recursive-lit-review | large-corpus synthesis | — |
| synthesize-research | orchestrator | — |
| draft-section | drafting | — |
| write-manuscript | drafting | — |
| frame-contributions | drafting | — |
| enhance-writing | drafting (support) | — |
| tools-for-thought | drafting (support) | — |
| validate-citations | validation (internal) | — |
| verify-sources | validation (external) | resolve_citation.py |
| validate-consistency | validation | — |
| validate-manuscript | validation (batch) | — |
| verify-review | validation (loop → verified end-state) | review_units.py, prisma_reporting_checks.py |
| prisma-flow | reporting | prisma_flow.py, prisma_checklist.py, prisma_compliance.py, prisma_abstract_checklist.py, prisma_updated_flow.py |
| orchestrate-research | orchestration | — |
| review-literature | orchestration | rlm_corpus_loader.py |

### verify-review methodology registrations

The profile integration layer registers `cochrane_profile → U_cochrane` and
`grade_profile_current → U_grade_current`. Declaring
`profile: cochrane_intervention` automatically puts `U_cochrane` in frozen scope;
current/full GRADE remains explicit because the legacy certainty contract is still
supported. See `skills/verify-review/references/research-profile-integration.md`.

---

**License:** MIT. **Version:** 1.0.
