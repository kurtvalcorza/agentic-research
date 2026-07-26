# Quickstart: Validating Standards Enforcement Parity

Runnable scenarios proving the feature works end to end. Each states its prerequisite, the command,
and the expected outcome. Field definitions are in [data-model.md](./data-model.md); rules are in
[contracts/](./contracts/).

## Prerequisites

Python 3.11 or later. **Nothing to install** — the checks and their tests use only the standard
library (constitution Principle II). Run everything from the repository root.

```bash
python --version    # 3.11+
```

---

## Scenario 1 — The suite runs clean

```bash
python -m unittest discover -s tests -v
```

**Expected**: all eleven test modules pass — nine covering the nine scripts, plus the coercion
conformance and dependency-freedom modules — exit code 0, no network access. Confirms SC-006 and
SC-007: every check that can fail a review run is covered, and the suite needs no installation.

---

## Scenario 2 — A complete, sound certainty record passes

```bash
python skills/validate-evidence/scripts/grade_profile.py \
  tests/fixtures/grade-profile.valid.json --strict
echo $?    # 0
```

**Expected**: the evidence profile and summary-of-findings tables print, headed with whether
certainty is keyed to outcomes or themes, followed by `✅`. Exit 0.

---

## Scenario 3 — Each certainty defect is caught individually

Run against the malformed fixtures; each must fail for its own reason, not a generic one.

All paths below are under `tests/fixtures/`.

| Fixture | Expected exit | Expected message |
|:--|:--:|:--|
| `grade-profile.missing-domain.json` | 1 | Names the absent domain; does not treat it as `0` |
| `grade-profile.bad-arithmetic.json` | 1 | Reports starting level, sum of adjustments, computed value, and declared final |
| `grade-profile.illegal-upgrade.json` | 2 | Rejects the upgrade key outside the permitted three |
| `grade-profile.aggregate-certainty.json` | 2 | Rejects the cross-result aggregate key |
| `grade-profile.typo-domain.json` | 2 | Rejects the misspelled key — **not** reported as a missing domain |
| `grade-profile.no-version.json` | 2 | Rejects the record for lacking a format version |
| `grade-profile.quoted-count.json` | 2 | Rejects the numeric string rather than coercing it |

**Expected**: seven distinct failures. Confirms SC-002 and SC-003 — an incomplete assessment
cannot be silently accepted, and an aggregate certainty cannot be expressed at all.

The `typo-domain` case is the one worth watching: a completeness check that reads a misspelling as
an omission reports the right verdict for the wrong reason, and would pass once the reviewer
"fixed" the wrong thing.

---

## Scenario 4 — Traceability holds and fails correctly

```bash
# Resolves: every referenced study is confirmed in the appraisal record
python skills/validate-evidence/scripts/grade_profile.py tests/fixtures/grade-profile.valid.json \
  --rob tests/fixtures/risk-of-bias.valid.json --strict          # exit 0

# Claims confirmed appraisals but supplies none
python skills/validate-evidence/scripts/grade_profile.py tests/fixtures/grade-profile.valid.json --strict
                                                   # exit 1 — claim not accepted on trust

# Referenced study differs only in case
python skills/validate-evidence/scripts/grade_profile.py tests/fixtures/grade-profile.case-mismatch.json \
  --rob tests/fixtures/risk-of-bias.valid.json --strict          # exit 1 — unresolved, not matched
```

**Expected**: the second and third fail. Confirms FR-018 and FR-042 — a basis claim is not taken on
trust, and near-miss identifiers surface rather than being reconciled.

---

## Scenario 5 — Body-level coherence

```bash
python skills/validate-evidence/scripts/grade_profile.py tests/fixtures/grade-profile.incoherent-rob.json \
  --rob tests/fixtures/risk-of-bias.mostly-high.json --strict
```

**Expected**: exit 1, reporting that a body-level judgment of no risk-of-bias concern is
contradicted by a study set in which high-risk studies predominate. Adding
`coherence_justification` to the record makes the same command exit 0.

---

## Scenario 6 — Appraisal completeness and the human gate

```bash
python skills/appraise-risk-of-bias/scripts/rob_appraisal.py tests/fixtures/risk-of-bias.valid.json --strict
```

**Expected**: exit 0; per-study table and traffic-light summary print; `H_rob: 0`. Output carries
the statement that the check establishes a confirmation record is present, not that a human made
the judgment.

Then the failing cases: an instrument applied to the wrong design (exit 1), a domain outside the
instrument's vocabulary (exit 2), an overall more favourable than the worst domain without
justification (exit 1), and a study lacking confirmation (exit 1, `H_rob: 1`).

---

## Scenario 7 — Reporting completeness over all 42 rows

```bash
python skills/prisma-flow/scripts/prisma_checklist.py tests/fixtures/checklist.partial.json --strict
```

**Expected**: exit 1, with unaddressed rows listed by number **above** the table and counted.
Critically, a record addressing all 27 top-level numbers but omitting sub-items such as `13d` or
`20b` must still fail — completeness is over the 42 addressable rows. Confirms SC-004.

---

## Scenario 8 — The loop refuses to verify an incomplete review

```bash
python skills/verify-review/scripts/review_units.py tests/fixtures/units.systematic-missing-checklist.json
```

**Expected**: the verdict is not `VERIFIED`; `U_checklist` appears under `missing_units`. Confirms
SC-008 — a review type requiring a check cannot be verified while that check is absent from its
record.

Then confirm the converse: the same command on a narrative review omitting `U_checklist` treats it
as out of scope rather than missing.

---

## Scenario 9 — Human gates never auto-satisfy

Run the loop repeatedly against a record with `H_rob: 3`.

**Expected**: `H_rob` remains 3 across every cycle up to the ceiling. No number of cycles satisfies
it. Confirms FR-026 and constitution Principle V.

---

## Scenario 10 — No unbacked claims remain

Read the README's standards table. Every row must name an enforcing check or carry an explicit
non-enforcement note, and the runnable-checks table must list all nine scripts including
`review_units.py`. Confirms SC-001 and FR-036.

This one is a human read rather than a command, and it is the scenario most likely to be skipped —
which is precisely why it is listed as a scenario rather than left as a documentation chore.

---

## Fixture location

Test fixtures live in `tests/fixtures/`, named `<record>.<defect>.json` with valid records named
`<record>.valid.json` (T003).

**All fixtures referenced above now exist**, and every scenario in this guide was executed end to
end during T058. Each behaved exactly as documented — same exit codes, same messages. Where a
scenario and the implementation had diverged, the implementation was corrected rather than the
guide.
