# Tasks: Standards Enforcement Parity

**Feature**: `001-standards-enforcement-parity` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: Explicitly requested in the specification and required by constitution v1.0.0's workflow
rules. Test tasks are therefore mandatory, not optional, and are written **before** the
implementation they cover within each phase.

**Path conventions**: Repository root is `agentic-research/`. Checks live under
`skills/<skill>/scripts/`; all tests live under `tests/` at the root.

---

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create `tests/` directory and write `tests/_load.py` — an `importlib.util.spec_from_file_location` loader taking a repo-relative script path and returning the loaded module, so scripts in non-importable directories such as `skills/appraise-risk-of-bias/` can be tested without `__init__.py` files (research.md D-011)
- [x] T002 [P] Create `.github/workflows/tests.yml` running `python -m unittest discover -s tests -v` on push and pull_request, matrix Python 3.11 and 3.12, checkout + setup-python only with no install step (research.md D-017)
- [x] T003 [P] Create `tests/fixtures/` and add a `README.md` stating that fixtures are JSON records exercising one rule each, named `<record>.<defect>.json`, with valid records named `<record>.valid.json`

**Checkpoint**: CI runs green against an empty suite; the loader is importable.

---

## Phase 2: Foundational (Blocking Prerequisites)

⚠️ **Blocks every user story.** The guidance corrections must land before any check is written —
a check built against the current guidance would encode the aggregate-certainty and
per-paper-grading errors into executable form, which is harder to reverse than prose (plan.md
Phase Sequencing).

- [x] T004 [P] Correct `skills/validate-evidence/references/DETAILS.md`: delete the weighted-average "Overall Evidence Profile" section that averages certainty across themes; delete per-paper certainty grading including the "Grade Contribution" column from all study-design tables and the "HIGH quality evidence: N papers" distribution in the executive summary; replace the `IF any(d == "RCT") → starting_grade = 4` rule with derivation from the predominant design; repair the self-referential `[Details](references/DETAILS.md)` link at end of file (FR-031, FR-034)
- [x] T005 [P] Reconcile `skills/validate-evidence/references/grade-framework.md`: demote the "Total events <300 / Total sample <400" imprecision indicators to an explicitly-labelled fallback used only when confidence interval and optimal-information-size data are unavailable, matching DETAILS.md rather than contradicting it, so no two guidance documents give conflicting rules for the same judgment (FR-032, SC-010, research.md D-014)
- [x] T006 [P] Add machine-readable domain keys and value vocabularies for all four instruments to `skills/appraise-risk-of-bias/references/instruments.md`, transcribed from [contracts/risk-of-bias.md](./contracts/risk-of-bias.md) so guidance and schema cannot drift (FR-012)
- [x] T007 Write `tests/test_prisma_flow.py` covering the existing script: both flow templates, each arm's reconciliation break, the merge mismatch, boolean/negative/non-integral rejection, `--strict` exit codes, and the malformed-JSON path — plus a case asserting the numeric string `"3"` is **rejected**, which fails against current behaviour (FR-037, research.md D-019)
- [x] T008 Align `_int()` in `skills/prisma-flow/scripts/prisma_flow.py` to reject numeric strings rather than coercing them via `int(str(v).strip())`, making T007 pass — a behavioural change to shipped code that must be called out separately in the pull request, not absorbed into the feature (research.md D-019)
- [x] T009 Record the coercion rules as the shared contract in [contracts/cli-contract.md](./contracts/cli-contract.md) and verify `prisma_flow.py` and `review_units.py` now agree on the full input table

**Checkpoint**: guidance no longer contradicts the frameworks; the two existing scripts agree on
what malformed input means; first existing script under test.

---

## Phase 3: User Story 1 - Certainty grading that cannot be incomplete or illegal (Priority: P1) 🎯 MVP

**Goal**: Recording certainty judgments produces a checked evidence profile and summary of
findings, and no incomplete or framework-illegal grading can pass.

**Independent test**: Run the check against records containing a missing domain, broken
arithmetic, an illegal upgrade, and an aggregate certainty key; each fails for its own reason
while a sound record passes and emits both tables.

### Tests for User Story 1 (write first, ensure they FAIL)

- [x] T010 [P] [US1] Write valid and defective fixtures in `tests/fixtures/`: `grade-profile.valid.json`, `.missing-domain.json`, `.bad-arithmetic.json`, `.illegal-upgrade.json`, `.aggregate-certainty.json`, `.typo-domain.json`, `.no-version.json`, `.quoted-count.json`, `.minority-rct.json`, `.empty-results.json`
- [x] T011 [P] [US1] Write `tests/test_grade_profile.py` asserting rules 1–9, 13 and 14 of [contracts/grade-profile.md](./contracts/grade-profile.md), each with a passing and a failing case, and asserting the exit code for each defect class — specifically that a misspelled domain key exits 2 as malformed input rather than being reported as a missing domain
- [x] T012 [P] [US1] Add a golden test pinning the generated evidence profile and summary-of-findings Markdown for the valid fixture (FR-038)

### Implementation for User Story 1

- [x] T013 [US1] Create `skills/validate-evidence/scripts/grade_profile.py` with argparse CLI, stdin/path input, `--strict`, UTF-8 stdout reconfiguration, and the exit-code contract 0/1/2 (FR-027)
- [x] T014 [US1] Implement record loading: `schema_version` required and recognised, unknown keys rejected at every level, `results` non-empty, `results[].id` and `study_ids` unique, coercion per the shared table (FR-028, FR-029, FR-042, FR-044)
- [x] T015 [US1] Implement domain completeness and vocabulary: exactly five keys required, each `rating` ∈ {0, −1, −2}, missing key reported by name, misspelled key rejected as malformed (FR-001, FR-002)
- [x] T016 [US1] Implement the certainty arithmetic check `clamp(index(start) + Σdomains + Σupgrades, 1, 4) == index(final)`, reporting both sides and the difference in the style of the existing reconciliation output (FR-003)
- [x] T017 [US1] Implement starting-level consistency against the predominant `design_mix` entry, permitting deviation only with `starting_level_justification` (FR-004, research.md D-015)
- [x] T018 [US1] Implement upgrade legality: non-zero only when the body is non-randomized and every domain rating is 0, with keys restricted to the three permitted reasons so any other is malformed (FR-005, FR-006)
- [x] T019 [US1] Implement rejection of `overall_certainty` and any cross-result aggregate key, making the averaging error unrepresentable rather than merely undocumented (FR-007, research.md D-016)
- [x] T020 [US1] Implement `basis` handling: `confirmed_rob` or `heuristic`; heuristic stamps output PROVISIONAL, fails `--strict` for systematic and umbrella, and is permitted for rapid only when `streamlined_method_disclosed` is present (FR-009, research.md D-009)
- [x] T021 [US1] Implement the evidence profile and summary-of-findings generators, both headed with the declared `synthesis_mode` and carrying a provenance line naming the check and source record, generated from the same record without re-entry of data (FR-008, FR-010, SC-005)
- [x] T022 [US1] Update `skills/validate-evidence/SKILL.md`: output contract becomes record-as-source with generated artifacts, add script usage, and state what the check cannot verify — that a domain judgment is present, legal and consistent, never that it was the right call (FR-030, FR-033)

**Checkpoint**: certainty grading is verifiable end to end and independently valuable, even with
appraisal input still unverified.

---

## Phase 4: User Story 2 - Risk-of-bias appraisal, verifiably complete and human-confirmed (Priority: P2)

**Goal**: Appraisals use the right instrument, carry every domain, and reach certainty grading
only when a human has confirmed them.

**Independent test**: Run against appraisals containing a design/instrument mismatch, a missing
domain, an out-of-vocabulary value and an unconfirmed study; each is reported, and `H_rob` counts
the unconfirmed.

### Tests for User Story 2 (write first, ensure they FAIL)

- [x] T023 [P] [US2] Write fixtures: `risk-of-bias.valid.json` covering all four instruments, plus `.wrong-instrument.json`, `.missing-domain.json`, `.bad-vocabulary.json`, `.overall-too-favourable.json`, `.unconfirmed.json`, `.duplicate-id.json`, `.empty-studies.json`, `.mostly-high.json`
- [x] T024 [P] [US2] Write `tests/test_rob_appraisal.py` asserting rules 1–8 of [contracts/risk-of-bias.md](./contracts/risk-of-bias.md), including each instrument's exact domain set and vocabulary, plus a golden test for the generated tables
- [x] T025 [P] [US2] Extend `tests/test_grade_profile.py` with traceability and coherence cases: unresolved reference, case-mismatched identifier rejected rather than matched, `confirmed_rob` without `--rob`, and a body-level rating contradicted by the per-study distribution both with and without justification

### Implementation for User Story 2

- [x] T026 [US2] Create `skills/appraise-risk-of-bias/scripts/rob_appraisal.py` with the same CLI shape, exit-code contract, loading and coercion behaviour as the certainty check (FR-027, FR-028, FR-029, FR-044)
- [x] T027 [US2] Implement instrument/design correspondence: `rct`→`rob2`, `nrsi`→`robins_i`, `observational`→`nos`, `dta`→`quadas2` (FR-011)
- [x] T028 [US2] Implement per-instrument domain completeness and vocabularies for all four instruments, including QUADAS-2's separate risk-of-bias and applicability judgments and the Newcastle-Ottawa star maxima per block (FR-012)
- [x] T029 [US2] Implement overall-judgment consistency, flagging an overall more favourable than the worst domain unless `overall_justification` is recorded, and deriving the Newcastle-Ottawa band from the star total (FR-013)
- [x] T030 [US2] Implement the human-confirmation gate: `confirmed_by` and `confirmed_at` non-empty, emitting the `H_rob` count of unconfirmed studies (FR-014)
- [x] T031 [US2] Implement the per-study table and traffic-light summary generators, encoding each judgment with both a symbol and a text label rather than colour alone so the artifact stays legible in print and to screen readers, both carrying a provenance line naming the check and source record as the certainty and checklist artifacts do (FR-016, constitution Principle VII)
- [x] T032 [US2] Add the verbatim statement to the check's output and skill that it establishes a confirmation record is present, not that a human made the judgment or who they were (FR-015)
- [x] T033 [US2] Implement `--rob` traceability in `grade_profile.py`: resolve every `study_ids` entry by exact match against confirmed appraisals, report unresolved references, and fail `--strict` when `confirmed_rob` is claimed without the path (FR-017, FR-018, FR-019, FR-042)
- [x] T034 [US2] Implement the coherence check in `grade_profile.py`: flag a `risk_of_bias` rating of 0 while more than half the resolved studies are high risk, or −2 while all are low risk, permitted with `coherence_justification`; flag only the clearly-contradictory ends and leave the middle to judgement (FR-043, research.md D-008)
- [x] T035 [US2] Update `skills/appraise-risk-of-bias/SKILL.md`: record-as-source output contract, script usage, the presence-not-authenticity limitation, and the unchanged human-gate requirement (FR-030, FR-033)

**Checkpoint**: appraisal is verifiable and its confirmed ratings demonstrably back the certainty
grading that cites them.

---

## Phase 5: User Story 3 - Reporting completeness that can be demonstrated (Priority: P3)

**Goal**: A submission-ready reporting checklist is generated from recorded data, with every
unaddressed row named.

**Independent test**: Run against a record addressing all 27 top-level numbers but omitting
sub-items; the check must still fail and name them.

### Tests for User Story 3 (write first, ensure they FAIL)

- [x] T036 [P] [US3] Write fixtures: `checklist.valid.json` covering all 42 rows, `.partial.json`, `.subitems-omitted.json` (all 27 numbers present, sub-items missing), `.both-fields.json`, `.unknown-number.json`, `.empty-justification.json`
- [x] T037 [P] [US3] Write `tests/test_prisma_checklist.py` asserting rules 1–7 of [contracts/prisma-checklist.md](./contracts/prisma-checklist.md), with an explicit test that completeness is evaluated over 42 rows and not 27 numbers, plus a golden test for the generated checklist

### Implementation for User Story 3

- [x] T038 [US3] Transcribe the PRISMA 2020 item table — 27 numbered items expanded to 42 addressable rows including 10a–10b, 13a–13f, 16a–16b, 20a–20d, 23a–23d and 24a–24c — into `prisma_checklist.py` as section, number and short topic label, citing the source and reproducing no official item wording (research.md D-013)
- [x] T039 [US3] Transcribe the PRISMA-ScR item table from the published checklist and cross-check it against the source. **Do not reconstruct it from memory**: an approximated table makes every completeness verdict wrong while looking authoritative. If transcription cannot be completed, do not ship the variant — instead add an explicit non-enforcement note to the README standards table (plan.md post-design re-evaluation)
- [x] T040 [US3] Create `skills/prisma-flow/scripts/prisma_checklist.py` with the shared CLI shape, exit-code contract, loading and coercion behaviour, and variant selection (FR-022, FR-027)
- [x] T041 [US3] Implement completeness: every row the variant defines present, exactly one of `location` or `not_applicable` per row, non-empty justification, unknown or duplicate numbers rejected (FR-020)
- [x] T042 [US3] Implement the checklist generator, listing unaddressed rows with a count **above** the table so they are not lost among 42 rows, linking the source for authoritative wording and carrying a provenance line (FR-021)
- [x] T043 [US3] Update `skills/prisma-flow/SKILL.md` to document the checklist check alongside the flow check, including what it cannot verify — that a cited location genuinely addresses the item (FR-030)

**Checkpoint**: the reporting-checklist claim in the README is now true rather than aspirational.

---

## Phase 6: User Story 4 - A verification loop that will not declare an unfinished review verified (Priority: P4)

**Goal**: The loop computes its certainty, traceability and reporting units from the checks, and
refuses to verify a review missing an applicable one.

**Independent test**: Present a systematic review record omitting `U_checklist`; the loop lists it
under `missing_units` and cannot report `VERIFIED`.

### Tests for User Story 4 (write first, ensure they FAIL)

- [x] T044 [P] [US4] Write `tests/test_review_units.py` covering existing behaviour first — fail-closed on empty and citation-less maps, declared-scope enforcement, plateau detection, floor-guard, and the boolean/negative/non-finite rejections in `_as_count` (FR-037)
- [x] T045 [P] [US4] Extend it with the new units: `U_grade`, `U_rob_trace`, `U_checklist` present-and-zero required for a systematic review; absent applicable unit reported as missing and blocking `VERIFIED` (FR-024); inapplicable unit absent rather than zero-to-achieve (FR-025); `H_rob` never auto-zeroed across any number of cycles (FR-026)

### Implementation for User Story 4

- [x] T046 [US4] Add `U_rob_trace` and `U_checklist` to `DEFAULT_WEIGHTS` at weight 1 in `skills/verify-review/scripts/review_units.py`, leaving `UNIVERSAL_FLOOR` unextended since these are review-type dependent rather than universal (FR-023)
- [x] T047 [US4] Redefine `U_grade` as results failing the certainty check and source `H_rob` from the appraisal check's count rather than a hand-entered assertion (FR-014, FR-023)
- [x] T048 [US4] Extend in-scope resolution by review type per [contracts/review-units.md](./contracts/review-units.md), with `U_rob_trace` and `H_rob` out of scope for rapid reviews where the heuristic basis is permitted (FR-025)
- [x] T049 [US4] Update `skills/verify-review/SKILL.md`: add the three units to the units table and all four rows to the by-review-type scope table (FR-023)

**Checkpoint**: the three checks are now a gate on the review as a whole.

---

## Phase 7: User Story 5 - Checks that are themselves trustworthy (Priority: P5)

**Goal**: Every check capable of failing a review run is covered, and coverage runs automatically.

**Independent test**: `python -m unittest discover -s tests -v` passes with no network access, and
CI reports before merge.

- [x] T050 [P] [US5] Write `tests/test_kappa.py`: Cohen's κ against a hand-computed value, perfect agreement, chance-level agreement, the degenerate single-label case where κ is undefined, sensitivity/MCC against a reference, and `--min-kappa` exit 1 (FR-037)
- [x] T051 [P] [US5] Write `tests/test_dedupe_records.py`: DOI-exact matching, fuzzy-title threshold boundaries, preprint-versus-published reconciliation, and the duplicates-removed count that feeds the flow diagram
- [x] T052 [P] [US5] Write `tests/test_resolve_citation.py` patching `urllib.request.urlopen` in the module: successful resolution, retraction detection, unresolvable DOI, and HTTP error handling — patching at `urlopen` rather than `_get` so an unmocked path raises instead of reaching the network (FR-040, research.md D-012)
- [x] T053 [P] [US5] Write `tests/test_search_openalex.py` with the same patching strategy: search result mapping, abstract reconstruction from the inverted index, and backward/forward snowballing
- [x] T054 [US5] Write `tests/test_coercion_conformance.py` asserting all four checks agree on the shared input table — booleans, non-integral floats, negatives, non-finite values and numeric strings — so the duplicated helpers cannot drift (research.md D-002)
- [x] T055 [US5] Write `tests/test_no_dependencies.py` asserting dependency-freedom mechanically: walk every `.py` file under `skills/*/scripts/` and `tests/`, parse top-level and function-level imports with `ast`, and assert each resolves to a standard-library module — then confirm CI reports on a pull request and the suite completes with no network access, proving both by assertion rather than by absence of observed traffic (FR-039, FR-041, constitution Principle II)

**Checkpoint**: all nine scripts covered; enforcement is as trustworthy as the enforcers.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [x] T056 [P] Update `README.md`: add `grade_profile.py`, `rob_appraisal.py` and `prisma_checklist.py` to the runnable-backends table, and flip their standards rows from ⚠️ guidance to ✅ enforced (FR-035, FR-036)
  - **Partially completed ahead of implementation.** The accuracy half landed early, since leaving an overclaim standing for the duration of the build would itself violate Principle I: `review_units.py` was added to the runnable-backends table, and the standards table gained an explicit **Enforced?** column distinguishing a runnable gate from documented guidance. GRADE, the risk-of-bias instruments, dual extraction, SWiM and the reporting checklist are now marked ⚠️ guidance rather than implied as enforced. What remains here is flipping those rows to ✅ as each check ships.
- [x] T057 [P] Register the three new scripts in `SKILLS-REGISTRY.md`
- [x] T058 Run every scenario in [quickstart.md](./quickstart.md) end to end, including scenario 10's human read of the README, and correct any divergence between documented and actual behaviour
- [x] T059 Review each check's "cannot verify" statement against constitution Principle VI, confirming all four are present and specific rather than generic, so a passing result is never read as a broader guarantee than it is (FR-030, SC-009)
- [x] T060 Open the pull request, calling out the `prisma_flow.py` coercion change (T008) and any pre-existing defects surfaced by T044/T050 as separate items rather than folded into the feature, then run the dual-bot review loop to clean or false-positives-only before merge

---

## Dependencies

```
Phase 1 Setup  ──> Phase 2 Foundational ──> Phase 3 (US1, P1) ──> Phase 4 (US2, P2)
                                                   │                      │
                                                   └──────────┬───────────┘
                                                              v
                                              Phase 5 (US3, P3) ──> Phase 6 (US4, P4)
                                                              │
                                                              v
                                              Phase 7 (US5, P5) ──> Phase 8 Polish
```

- **Phase 2 blocks everything.** Guidance must be correct before a check encodes it.
- **US2 depends on US1** only for the traceability and coherence tasks (T033, T034), which extend
  `grade_profile.py`. The appraisal check itself (T026–T032) is independent and could proceed in
  parallel with US1 if two people were working.
- **US3 is fully independent** of US1 and US2 — it shares only the CLI contract.
- **US4 depends on US1, US2 and US3** existing, since it counts their outputs.
- **US5's backfill tasks (T050–T053) are independent of everything** and could start any time
  after Phase 1; only T054 depends on all four checks existing.

## Parallel opportunities

- **Phase 2**: T004, T005, T006 are three different files — fully parallel.
- **Phase 3**: T010, T011, T012 are fixture and test authoring — parallel; implementation
  T013–T021 is sequential within one file.
- **Phase 4**: T023, T024, T025 parallel.
- **Phase 7**: T050, T051, T052, T053 are four independent test modules — the largest parallel
  block in the feature.
- **Phase 8**: T056, T057 parallel.

## Implementation strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1).** That delivers corrected guidance and a
working certainty check — the largest gap and the one whose failure mode is worst, since an
incomplete certainty rating reads exactly like a sound one. It is independently valuable and
shippable even if nothing else follows.

**Incremental delivery**: each subsequent phase is an independently reviewable increment, matching
the three-phase structure in plan.md — guidance correctness, then the checks, then wiring and
coverage. The pull request should be reviewable phase by phase rather than as one diff.

**Two rules that must not be quietly dropped under time pressure**:

1. T039's prohibition on reconstructing the scoping item table from memory. Shipping without the
   variant plus a non-enforcement note is acceptable; an approximated table is not.
2. T060's separation of pre-existing defects from feature work. Folding a `kappa.py` or
   `review_units.py` fix into this diff hides a behavioural change to a gating script.
