# Feature Specification: orx Discovery Backend for acquire-corpus

**Feature Branch**: `claude/openresearch-agentic-research-diff-fq5xyi`

**Feature Directory**: `specs/002-orx-discovery-backend`

**Created**: 2026-09-09

**Last Revised**: 2026-09-11 — implementation review at `d1fcf99` addressed (round 4)

**Status**: Draft — ready for independent re-review

**Input**: Add OpenResearch's `orx discover` as optional, detect-and-degrade discovery enrichment for `acquire-corpus`. The existing keyless OpenAlex/CrossRef path remains the only guaranteed path. Enrichment may add alphaXiv full-text keyword retrieval, semantic retrieval, OpenAlex discovery, and bioRxiv discovery, but it must not weaken portability, reproducibility disclosure, fail-closed behavior, or downstream study-count integrity.

> **Correction to the original premise.** `orx discover` does not require a local daemon or login.
> Current upstream literature discovery invokes public literature endpoints directly. Availability is
> therefore modeled as executable presence plus bounded discovery invocations, not background-service
> health.

## Review corrections incorporated

### Reviewer round 1

Five findings against the original draft are resolved:

| # | Finding | Resolution |
|:--|:--------|:-----------|
| 1 | Availability assumed a local daemon | `orx discover` is modeled as a public-endpoint CLI call with bounded timeout and keyless fallback. |
| 2 | Gate input could not be JSONL + Markdown under the shared contract | `corpus/acquisition-record.json` is the one closed-schema source of truth; `corpus/search-log.md` is generated from it. |
| 3 | Unknown upstream fields conflicted with Principle IV | Unknown top-level `LitHit` keys fail closed: the enriched response is unsupported and the affected query falls back keyless. |
| 4 | `LitHit` did not supply the assumed corpus shape | The mapping below distinguishes directly supplied fields from bibliographic metadata that must be completed before safe admission. |
| 5 | `verify-sources` limitation was overstated | DOI-less records cannot be resolved directly by DOI, but title/author/year reverse lookup remains available when sufficient metadata exists. |

### Reviewer round 2

Three further findings at `10b8f964` are resolved in this revision:

| # | Finding | Resolution |
|:--|:--------|:-----------|
| 1 | Mandatory record-level provenance conflicted with unchanged keyless output | Existing keyless candidate records remain schema/content-compatible with pre-feature output. Keyless provenance is recorded in the canonical acquisition record and existing per-source raw artifacts; only enriched records carry the new enriched-record provenance fields. |
| 2 | `authors: []` violated fail-closed semantics and exposed title-only false merges | No empty/default author list is synthesized. An enriched hit must be completed to the dedupe-safe bibliographic minimum before admission; otherwise it is preserved in `corpus/enrichment-unresolved.jsonl` and excluded from `candidates.jsonl`. |
| 3 | Per-invocation timeout allowed cumulative stalls | A per-sub-source circuit breaker and run-level enrichment failure budget prevent repeated failed calls from accumulating unbounded delay. |

### Reviewer round 3

Two findings at `9cb569b9` are resolved in this revision:

| # | Finding | Resolution |
|:--|:--------|:-----------|
| 1 | Degraded enrichment could disappear from the generated human-readable log | FR-005 records reviewer-selected keyless-only mode; FR-029 preserves every query outcome in `search-log.md` and requires a run-level degradation note whenever enrichment fails or is skipped because a circuit is open. SC-005 requires chosen-keyless and degraded-keyless runs to be distinguishable to a reader. |
| 2 | `enrichment-unresolved.jsonl` had no explicit handoff/consumer | FR-032 now requires the generated log and acquisition handoff to surface the unresolved file path and count for reviewer triage. Automatic admission after resolution remains explicitly out of scope; unresolved hits cannot enter screening until bibliographic resolution satisfies FR-031. |

### Reviewer round 4 (implementation review at `d1fcf993`)

Four P1 and one P2 finding against the implementation are resolved in this revision. The
minimal vocabulary/schema changes they required are flagged here for the owner:

| # | Finding | Resolution |
|:--|:--------|:-----------|
| 1 | Metadata completion bypassed the 15-second enrichment failure budget | FR-033 now names OpenAlex metadata completion explicitly: one five-second deadline per lookup, failure wait charged to the same run budget, a completion circuit opened by the first transport failure, and cached repeated lookups. SC-003 covers completion lookups. |
| 2 | Title/year-only OpenAlex matching could falsely satisfy "verified authors" | FR-031 now requires completion to be addressed and corroborated by a stable identifier (OpenAlex work id, DOI, or arXiv DOI). Title similarity plus a year window is not identity; a title-only completion stays unresolved. |
| 3 | Keyless transport failures collapsed into `empty`/`answered` | FR-014 adds a fifth outcome, `incomplete`, for a keyless search that stopped on a transport/malformed-response failure before the source was exhausted; it carries a failure reason and the partial returned count. Keyless exit semantics (FR-003) are unchanged. **Schema change.** |
| 4 | Zero-normalizable responses lost their normalization-drop counts | FR-008 now states the fallback entry keeps every drop by count and reason; the gate requires the drops to sum to the returned count. |
| 5 | Record/log omitted FR-022 loss counts and FR-012 method disclosure | FR-028 bumps the record schema to `1.1`, adding a structured `loss_summary` (FR-022) and `method_disclosure` (FR-012) that the log renders and the gate reconciles. FR-023 guidance is stated in the owning SKILL/README. **Schema change.** |

The safety rule for sparse enrichment is now explicit: **recall evidence may be preserved without being
fed into an unsafe deduplication path**. A hit that cannot be completed to the bibliographic fields
required for guarded deduplication is not discarded silently; it is retained as unresolved evidence,
counted, logged, and surfaced to the reviewer for triage, but it does not enter the automatic
candidate/dedupe path. This feature does not define a second admission mechanism for unresolved hits:
they require later bibliographic resolution that satisfies FR-031 before they may enter screening.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Wider discovery when OpenResearch is usable (Priority: P1)

A reviewer running `acquire-corpus` on a machine with `orx` installed can receive candidate works
that metadata-only keyword discovery may miss: alphaXiv full-text matches, semantic matches, and
bioRxiv/OpenAlex results. Enriched hits are normalized, bibliographically completed when necessary,
and admitted only when they can safely enter the existing downstream deduplication contract.

**Independent Test**: Use a question with a known full-text-only exemplar. Confirm that enrichment
finds the exemplar, then confirm that an enriched hit enters `candidates.jsonl` only after satisfying
the safe-admission rule in FR-031; otherwise it appears in `enrichment-unresolved.jsonl` and is
surfaced in the reviewer handoff.

**Acceptance Scenarios**:

1. **Given** a supported enriched response and sufficient bibliographic metadata, **When** acquisition
   runs, **Then** the enriched work is admitted with enriched-source provenance and downstream-safe
   bibliographic fields.
2. **Given** an enriched work duplicates a keyless work, **When** candidates are assembled, **Then**
   both are retained for `dedupe-records`; acquisition does not perform cross-source deduplication.
3. **Given** an enriched hit cannot be completed safely, **When** acquisition finishes, **Then** the
   hit is preserved in `corpus/enrichment-unresolved.jsonl`, counted in the acquisition record,
   surfaced by path and count for reviewer triage, and excluded from the automatic candidate/dedupe
   path until bibliographic resolution satisfies FR-031.

---

### User Story 2 — Identical keyless behavior when OpenResearch is absent or unusable (Priority: P1)

A reviewer with no `orx` installed gets the existing keyless acquisition behavior. Candidate records
are not rewritten merely to attach new provenance fields. No warning, prompt, installation advice,
changed exit code, or meaningful delay is introduced.

**Independent Test**: Run acquisition with `orx` absent and compare `candidates.jsonl` plus exit code
to the pre-feature run for the same query.

**Acceptance Scenarios**:

1. **Given** OpenResearch is absent, **When** acquisition runs, **Then** keyless candidate records and
   exit semantics remain compatible with the pre-feature output contract.
2. **Given** OpenResearch is absent, **When** acquisition runs, **Then** no output stream emits an
   OpenResearch warning, error, prompt, or installation suggestion.
3. **Given** OpenResearch is present but one enriched sub-source fails, **When** acquisition runs,
   **Then** the query falls back keyless and the circuit breaker prevents repeated failed attempts to
   that sub-source during the same run.
4. **Given** OpenResearch is usable, **When** the reviewer requests keyless-only acquisition, **Then**
   no enriched command is invoked and the acquisition record identifies the run as reviewer-selected
   keyless-only mode.

---

### User Story 3 — Search documentation discloses reproducibility and losses (Priority: P2)

A reader can determine which backend answered each query, which enriched hits were admitted, which
were unresolved, whether OpenResearch is required to reproduce the search, whether enrichment was
attempted but degraded, and whether any normalization or metadata-completion loss occurred. One
structured acquisition record is the source of truth and the human-readable search log is generated
from it without dropping method-significant outcomes.

**Independent Test**: Run successful-enriched, reviewer-selected keyless-only, and degraded-keyless
acquisitions; inspect `acquisition-record.json`, regenerate `search-log.md`, and run the disclosure
gate against each.

**Acceptance Scenarios**:

1. Every query entry records backend/sub-source, submitted query, date, outcome, returned count,
   normalization drops, unresolved-enrichment count, and OpenResearch version when used.
2. Successful enrichment requires an explicit non-keyless reproducibility disclosure naming the
   affected queries and backend version(s).
3. A reviewer-selected keyless-only run carries no OpenResearch reproducibility caveat and is
   identified as intentionally keyless-only rather than degraded.
4. `search-log.md` is generated from `acquisition-record.json`; it is never independently authored,
   and it preserves each query outcome.
5. If any query is `failed-and-fell-back` or `skipped-circuit-open`, the generated log includes a
   run-level degradation note so the reader can see that intended enrichment did not complete.
6. An enriched acquisition record missing required disclosure fails the disclosure gate under
   `--strict` as a method violation.
7. A valid keyless acquisition record passes the disclosure gate.

---

### User Story 4 — The skill remains portable (Priority: P3)

Someone copies `skills/acquire-corpus/` into another project with no OpenResearch installation and no
access to sibling repository code. Keyless acquisition still works.

**Independent Test**: Copy the skill directory outside the repository, remove `orx` from `PATH`, and
run acquisition to completion.

**Acceptance Scenarios**:

1. The copied skill completes keyless acquisition and produces candidates, an acquisition record,
   and a generated search log.
2. No import resolves to a sibling skill, shared repository library, or path outside the copied skill.

## Edge Cases

- **Binary present, public endpoint unavailable.** The failed enriched sub-source opens its circuit
  for the remainder of the run; acquisition proceeds keyless.
- **Discovery invocation hangs.** The process is terminated at the per-invocation deadline and its
  sub-source circuit opens.
- **Repeated failures across sub-sources.** The run-level enrichment failure budget stops further
  enrichment attempts once exhausted; remaining queries are keyless and the generated log records
  the degraded outcomes rather than presenting the run as intentionally keyless-only.
- **Malformed transport.** Non-JSON, truncated JSON, a non-collection top-level value, or an empty
  stream is an enrichment failure. A valid empty collection is a genuine zero-result response.
- **Unknown upstream record key.** The enriched response fails closed under FR-007 and falls back
  keyless.
- **Required discovery field missing.** The record is non-normalizable, counted, and not emitted.
- **Authors unavailable.** No `authors: []` placeholder is synthesized. Metadata completion is
  attempted; failure sends the hit to `enrichment-unresolved.jsonl`.
- **Year unavailable.** No null/empty year is used to bypass the dedupe guard. The hit must be
  completed or remain unresolved.
- **DOI unavailable but author/year metadata is verified.** The record may still be admitted under
  FR-016 because guarded fuzzy deduplication remains available and the alternative source identifier
  is preserved.
- **All enriched hits remain unresolved.** The keyless candidate set remains valid; unresolved hits
  are reported separately, surfaced by path and count for reviewer triage, and do not masquerade as
  admitted candidates.
- **Disclosure absent from an otherwise valid enriched acquisition record.** Exit `1` under
  `--strict`.
- **Acquisition record malformed, wrong-schema, or carrying unknown keys.** Exit `2`.
- **Version changes during a project.** Version is recorded per enriched query rather than once per
  run.
- **Enrichment dominates identification counts.** Admitted, unresolved, and normalization-dropped
  counts remain separately auditable.

## Requirements *(mandatory)*

### Functional Requirements

**Availability, degradation, and bounded failure**

- **FR-001**: The skill MUST NOT assume or probe a local OpenResearch daemon. Executable presence is
  the local prerequisite; usability is determined by bounded `orx discover` invocations.
- **FR-002**: Each enriched invocation MUST terminate within five seconds on timeout/unreachability
  and MUST NOT block acquisition indefinitely.
- **FR-003**: Absence or failure of enrichment MUST NOT emit an unsolicited runtime OpenResearch
  warning/error, prompt the user, suggest installation, alter keyless exit semantics, or prevent
  keyless completion. Required method disclosure in the generated artifacts under FR-029 is not a
  runtime warning and MUST still be emitted.
- **FR-004**: A failed enriched query MUST fall back to the keyless path and be recorded as
  `failed-and-fell-back`, not as a legitimate zero-result query.
- **FR-005**: The reviewer MUST be able to force keyless-only acquisition even when OpenResearch is
  usable. The canonical acquisition record MUST identify reviewer-selected keyless-only mode so it
  cannot be confused with a run that intended enrichment but degraded to keyless.
- **FR-033**: A timeout, network failure, command-surface failure, or unsupported-schema failure MUST
  open a circuit for the affected enriched sub-source for the remainder of the run. No automatic
  retry is permitted after the circuit opens. The cumulative failure-wait budget across all enriched
  sub-sources MUST NOT exceed fifteen seconds per run; after the budget is exhausted, all remaining
  enrichment attempts are skipped and queries continue keyless. Bibliographic metadata completion
  for enriched hits (FR-031) is part of enrichment and is under the same bound: each completion
  lookup has the same five-second deadline, its failure wait is charged to the same run budget, the
  first completion transport failure opens a completion circuit for the remainder of the run, and
  repeated lookups for one stable identifier MUST be served from a cache. Hits skipped by the
  budget or circuit are unresolved under FR-032 with a machine-readable reason.

**Record handling and safe admission**

- **FR-006**: The adapter MUST normalize supported `LitHit` results using the explicit mapping below.
  It MUST NOT fabricate bibliographic values merely to resemble an OpenAlex record.
- **FR-007**: Every enriched response MUST be validated against the supported top-level `LitHit`
  keys. If any record contains an unrecognized top-level key, the response is unsupported: no record
  from that response is emitted, the sub-source circuit opens, and the query falls back keyless.
- **FR-008**: Within a supported shape, a record missing a required discovery field (`source`, `id`,
  or usable `title`) MUST be dropped with a counted reason. A non-empty response yielding zero
  normalizable records MUST fall back keyless, and its query entry MUST still carry every drop by
  count and reason so that the drops sum to the returned count.
- **FR-009**: Existing keyless candidate records MUST remain schema/content-compatible with the
  pre-feature candidate contract and MUST NOT be rewritten solely to add `source`/`sub_source`
  fields. Keyless backend provenance MUST instead be recorded per query in
  `corpus/acquisition-record.json` and remain auditable through existing per-source raw artifacts.
  Every **enriched** admitted candidate MUST carry `source: "orx"`, `sub_source`, and `source_id`.
- **FR-010**: Enriched raw responses and normalized enriched records MUST be written to source-
  specific raw artifacts so returned/admitted/unresolved counts can be reconciled.
- **FR-011**: `acquire-corpus` MUST NOT deduplicate across keyless/enriched backends.
- **FR-012**: If an enriched source applies opaque ranking, truncation, or internal selection, the
  acquisition record MUST disclose it and MUST NOT label it as the review's deduplication step.
- **FR-031**: Before an enriched hit may enter `candidates.jsonl`, it MUST satisfy the downstream
  dedupe-safe bibliographic minimum: usable `title`, a non-empty verified `authors` list, and a
  verified `year`. A DOI is preferred but not mandatory; when absent, a stable `source_id` MUST be
  retained. Metadata completion MAY use the skill's existing keyless bibliographic sources, but a
  field not actually resolved MUST remain missing and MUST NOT be defaulted to an empty/zero value.
  Completion MUST be addressed and corroborated by a stable identifier carried by the hit (OpenAlex
  work id, DOI, or the arXiv DOI derived from an alphaXiv identifier). Title similarity and a year
  window are not identity: a candidate matched on title/year alone MUST NOT supply verified
  authors, and a hit with no stable identifier or no corroborated candidate remains unresolved.
- **FR-032**: An enriched hit that cannot satisfy FR-031 MUST NOT enter `candidates.jsonl`. It MUST be
  preserved in `corpus/enrichment-unresolved.jsonl` with source identifier, title, available
  discovery metadata, and a machine-readable reason for non-admission. Its count MUST be reported in
  the acquisition record and generated search log. When the unresolved count is non-zero, the
  generated log and acquisition handoff MUST surface the file path and count for reviewer triage.
  Automatic admission or a separate downstream consumer for unresolved hits is out of scope for this
  feature; an unresolved hit MUST NOT enter screening unless later bibliographic resolution satisfies
  FR-031.

#### Normalized enriched discovery mapping

Current upstream `LitHit` serialization is the external discovery contract understood by this
feature. Unknown top-level keys invoke FR-007 until deliberately reviewed and added.

| OpenResearch field | Normalized field | Rule |
|:--|:--|:--|
| `source` | `source`, `sub_source` | `source` is `orx`; preserve upstream source (`alphaxiv`, `openalex`, `biorxiv`) as `sub_source`. Required. |
| `id` | `source_id` | Preserve verbatim. Required. |
| `id` | `doi` | Populate only when syntactically a DOI; otherwise DOI remains unresolved unless metadata completion finds one. |
| `title` | `title` | Required non-empty string. |
| *(not supplied by discovery)* | `authors` | **Do not synthesize or emit an empty placeholder.** Resolve through metadata completion before admission; otherwise FR-032 applies. |
| `publicationDate` | `year` | May supply the year when valid; otherwise metadata completion must resolve it before admission. |
| `abstract` | `abstract` | Preserve when supplied. |
| `citations` | `cited_by_count` | Preserve integer count when supplied. |
| `votes` | `orx_votes` | Preserve source-specific metadata when supplied. |
| `snippets` | `orx_snippets` | Preserve source-specific match evidence when supplied. |
| *(derived after completion)* | `identifier_less` | `true` only when the admitted record has no DOI; `false` otherwise. |

The adapter MUST NOT invent authors, venue, publication type, retraction status, references, DOI, or
year. Missing metadata is a resolution problem, not a value to encode as empty merely to satisfy a
shape check.

**Search record, generated log, and provenance**

- **FR-028**: Acquisition MUST emit `corpus/acquisition-record.json` as the canonical structured
  account of the search. It MUST be one closed-schema JSON object with required schema version.
  Schema `1.1` adds a run-level `loss_summary` (FR-022 counts) and `method_disclosure` (FR-012);
  the disclosure gate accepts `1.0` records unchanged and requires both objects from `1.1`.
- **FR-013**: The acquisition record MUST identify whether enrichment was reviewer-selected
  keyless-only or automatic, and MUST capture per query: backend/sub-source, submitted query, date,
  outcome, returned count, normalization-drop counts/reasons, admitted enriched count,
  unresolved-enrichment count/reasons, circuit-breaker state, and OpenResearch version when used.
- **FR-014**: The record MUST distinguish `answered`, `empty`, `incomplete`, `failed-and-fell-back`,
  and `skipped-circuit-open` outcomes. `incomplete` applies to a keyless search whose transport or
  response failed before the source was exhausted or the result limit was reached: a first-page
  failure is NOT `empty` and a later-page failure is NOT `answered`. An `incomplete` entry MUST
  carry a machine-readable failure reason and the partial returned count. Keyless exit semantics
  (FR-003) are unaffected; this is truthful provenance, not a runtime warning.
- **FR-015**: When any query was answered successfully by enrichment, the acquisition record MUST
  state that the search is not fully reproducible without OpenResearch, naming affected queries and
  backend version(s).
- **FR-029**: `corpus/search-log.md` MUST be generated from the acquisition record and MUST NOT be a
  separately hand-maintained source of truth. The generated log MUST preserve each query's
  backend/sub-source, submitted query, date, outcome, returned/admitted/unresolved counts, and
  circuit-breaker state. If any query is `failed-and-fell-back` or `skipped-circuit-open`, the log
  MUST include a run-level degradation note stating that enrichment was attempted but did not answer
  those queries. The log MUST distinguish reviewer-selected keyless-only runs from runs that intended
  enrichment but degraded to keyless.
- **FR-021**: Successful enriched acquisition MUST be stamped as AI-assisted provenance with backend,
  sub-source, and OpenResearch version.

**Downstream compatibility**

- **FR-016**: A DOI-less enriched record MAY be admitted only after FR-031 is satisfied. It MUST
  retain `source_id`, `authors`, and `year` so downstream fuzzy deduplication keeps its collision
  guards. DOI-less records that cannot satisfy FR-031 remain unresolved under FR-032.
- **FR-022**: The acquisition record and generated log MUST report counts of admitted DOI-less
  enriched records and unresolved records missing authors/year, as structured fields of the record
  (`loss_summary`) from which the log is generated and which the gate reconciles against the query
  entries and the unresolved count. The handoff MUST state that admitted
  DOI-less records lack exact DOI matching but retain the author/year guards; unresolved sparse hits
  are intentionally withheld from automatic deduplication to prevent title-only false merges.
- **FR-023**: Documentation MUST state that DOI-less admitted records cannot be resolved directly by
  DOI but may use title/author/year reverse lookup. Unresolved records are not represented as
  verified candidates and require manual or later bibliographic resolution.
- **FR-030**: This feature MUST NOT modify `dedupe-records` or `verify-sources`. Safe admission in
  `acquire-corpus` is the compatibility boundary for this feature.

**Enforcement posture**

- **FR-017**: A runnable disclosure check MUST consume the canonical acquisition record and verify
  that successful enrichment carries the FR-015 disclosure.
- **FR-024**: The disclosure check MUST follow the shared gate contract: one JSON object from path or
  stdin; `--strict`; exit `0` clean/non-strict, `1` method violation under strict, `2` malformed;
  unknown keys/wrong schema/non-object/invalid JSON are malformed; `--json` changes only output
  format using the shared envelope.
- **FR-025**: A valid keyless acquisition record MUST pass without complaint.
- **FR-026**: The check MUST state what it cannot verify, including truthfulness of provenance,
  backend version, source attribution, candidate-file counts, and correctness of metadata resolution.
- **FR-027**: The disclosure gate MUST NOT be represented as making `acquire-corpus` PRISMA-S
  compliant. PRISMA-S remains guidance/alignment only.

**Constitutional constraints**

- **FR-018**: No dependency may be required to import or run the skill's scripts. OpenResearch is an
  external optional executable.
- **FR-019**: The skill MUST remain functional when copied out alone with no OpenResearch present.
- **FR-020**: The skill MUST state what OpenResearch cannot verify: at minimum opaque ranking,
  uncharacterized recall against the review question, and unquantified source coverage.

### Key Entities

- **Keyless candidate record**: Existing pre-feature candidate schema; not rewritten solely for new
  provenance.
- **Enriched admitted record**: An `orx` discovery hit that satisfies FR-031 and carries enriched
  provenance plus downstream-safe bibliographic fields.
- **Unresolved enriched hit**: Discovery evidence preserved in `enrichment-unresolved.jsonl` because
  it cannot safely enter the automatic dedupe path; surfaced to the reviewer by path/count for
  triage and excluded from screening until later bibliographic resolution satisfies FR-031.
- **Acquisition record**: Closed-schema source of truth for query provenance, outcomes, counts,
  unresolved evidence, circuit state, requested enrichment mode, and reproducibility disclosure.
- **Search log**: Human-readable artifact generated from the acquisition record that preserves query
  outcomes and run-level degradation state.
- **Circuit breaker**: Per-sub-source run state that prevents repeated failed enrichment calls.
- **Disclosure verdict**: Gate result concerning enrichment disclosure only, not search quality.

## Success Criteria *(mandatory)*

- **SC-001**: With OpenResearch absent, keyless candidate output and exit code remain compatible with
  pre-feature behavior for 100% of tested queries.
- **SC-002**: With OpenResearch absent, acquisition adds no more than one second wall-clock time.
- **SC-003**: A failed enriched sub-source incurs at most one five-second failure wait in a run; total
  failure waiting across all enriched sub-sources, including metadata-completion lookups, never
  exceeds fifteen seconds.
- **SC-004**: 100% of admitted enriched candidates carry `source`, `sub_source`, `source_id`, usable
  title, non-empty verified authors, and verified year. Existing keyless candidates are not required
  to gain new record-level provenance fields.
- **SC-005**: A reader can determine from the generated log which queries require OpenResearch to
  reproduce, which enrichment attempts failed or were skipped because a circuit was open, and whether
  a keyless run was reviewer-selected or the result of degradation.
- **SC-006**: Malformed transport, timeout, unknown top-level keys, or unsupported enriched output
  never aborts acquisition and cannot trigger repeated calls after its sub-source circuit opens.
- **SC-007**: The copied-out skill completes keyless acquisition without OpenResearch.
- **SC-008**: For a known full-text-only exemplar, the enriched run records at least one discovery
  absent from keyless-only search, either as safely admitted or explicitly unresolved evidence that
  is surfaced for reviewer triage.
- **SC-009**: Every normalization drop and unresolved enriched hit is represented by count and reason
  in the acquisition record.
- **SC-010**: No admitted enriched record uses an empty/default author list or missing year to satisfy
  the downstream minimum.
- **SC-011**: The disclosure gate fails a well-formed enriched acquisition missing disclosure and
  passes it after disclosure is added.
- **SC-012**: The disclosure gate passes 100% of valid keyless acquisition records.
- **SC-013**: Regenerating `search-log.md` from the same acquisition record produces identical
  documentation, including the same query outcomes and degradation note.
- **SC-014**: A constructed same-title/different-study case with an unresolved author-less hit cannot
  be falsely merged by `dedupe-records` because the unresolved hit never enters `candidates.jsonl`.

## Assumptions

- **Enrichment is on by default when usable.** FR-005 provides a keyless-only opt-out and records that
  reviewer-selected mode explicitly.
- **Discovery needs no daemon, account, or key.** Current literature discovery uses public endpoints.
- **The backend is an external program.** No OpenResearch library is imported.
- **The reviewed `LitHit` shape is version-sensitive.** Additive/breaking upstream changes are
  possible and fail closed until reviewed.
- **Keyless candidate compatibility is intentional.** New per-query provenance belongs in the
  acquisition record; the feature does not rewrite historical keyless records merely for symmetry.
- **Metadata sparsity is not fabricated away.** Missing author/year data triggers completion or the
  unresolved path; empty placeholders are forbidden for safe-admission fields.
- **Recall evidence can exist outside the automatic candidate set.** `enrichment-unresolved.jsonl`
  preserves discovered evidence that is methodologically unsafe to deduplicate automatically. A
  non-zero unresolved count is surfaced to the reviewer for triage; automatic admission after that
  triage is outside this feature and requires later bibliographic resolution satisfying FR-031.
- **No downstream remediation is hidden here.** `dedupe-records` and `verify-sources` remain unchanged;
  this feature protects them by enforcing a safe admission boundary.
- **The acquisition record is the source of truth.** The Markdown search log is generated from it and
  preserves method-significant outcomes rather than silently dropping degradation state.
- **The disclosure gate does not upgrade standards claims.** It enforces enrichment disclosure only;
  PRISMA-S remains guidance rather than machine-verified compliance.
