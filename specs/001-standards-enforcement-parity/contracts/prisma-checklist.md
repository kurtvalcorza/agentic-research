# Contract: Reporting Checklist Record (`checklist.json`)

Consumed by `skills/prisma-flow/scripts/prisma_checklist.py`. Generates the completed reporting
checklist.

## Invocation

```bash
python skills/prisma-flow/scripts/prisma_checklist.py checklist.json --strict
```

## ⚠️ Item count: 27 numbered items, 42 addressable rows

The spec refers to "the 27 items", which is how PRISMA 2020 is customarily cited. The published
checklist expands several of those numbers into lettered sub-items, giving **42 rows a manuscript
must actually address**. Completeness is evaluated over the 42 rows, not the 27 numbers — treating
27 as the target would report a manuscript complete while six sub-items of item 13 alone were
unaddressed.

## Item table (`variant: prisma_2020`)

Supplied by the check, not by the record. Official item wording is referenced, not reproduced
(research.md D-013).

| Section | Rows |
|:--|:--|
| Title | 1 |
| Abstract | 2 |
| Introduction | 3 rationale, 4 objectives |
| Methods | 5 eligibility criteria, 6 information sources, 7 search strategy, 8 selection process, 9 data collection process, 10a data items (outcomes), 10b data items (other variables), 11 study risk-of-bias assessment, 12 effect measures, 13a–13f synthesis methods, 14 reporting bias assessment, 15 certainty assessment |
| Results | 16a study selection, 16b excluded studies, 17 study characteristics, 18 risk of bias in studies, 19 results of individual studies, 20a–20d results of syntheses, 21 reporting biases, 22 certainty of evidence |
| Discussion | 23a interpretation, 23b limitations of evidence, 23c limitations of review processes, 23d implications |
| Other information | 24a registration, 24b protocol access, 24c amendments, 25 support, 26 competing interests, 27 availability of data, code and materials |

**Source**: Page MJ et al. The PRISMA 2020 statement. *BMJ* 2021;372:n71. Published under CC BY 4.0.

## Variant: `prisma_scr` — NOT IMPLEMENTED (resolved 2026-07-26)

The scoping variant has a different item set (20 essential plus 2 optional). Its table **could not
be transcribed**: the official PRISMA site serves the checklist only as a PDF download, and the
source article (Tricco AC, et al. *Ann Intern Med* 2018;169:467-473, doi:10.7326/M18-0850) returns
HTTP 403 without a subscription.

Per the rule set before implementation, the **fallback was taken rather than the forbidden third
option**: the variant refuses with a message naming the source and the reason, and the README
standards row records it as deliberately unenforced. An approximated table was not shipped, because
every verdict it produced would be wrong while looking authoritative.

To enable it later: transcribe the table from the source, add it to `VARIANTS` in
`prisma_checklist.py`, remove the entry from `KNOWN_UNIMPLEMENTED`, and update the README row.

## Example

**An excerpt, not a complete record.** It shows the shape of the four item forms; a real
`prisma_2020` record addresses all 42 rows, and Rule 1 below means this excerpt exits 1 under
`--strict` with the other 38 listed as unaddressed. That is the check working, not a defect —
`tests/test_contract_examples.py` pins that exit code so the excerpt cannot silently become
wrong in some other way.

```json
{
  "schema_version": "1.0",
  "variant": "prisma_2020",
  "items": [
    {"number": "1",   "location": "Title page"},
    {"number": "2",   "location": "Abstract, p.1"},
    {"number": "13d", "not_applicable": "No meta-analysis performed; synthesis is narrative per SWiM."},
    {"number": "20b", "not_applicable": "No statistical synthesis; see item 13d."}
  ]
}
```

## Rules

| # | Rule | Violation type |
|:--:|:--|:--|
| 1 | Every row the variant defines appears in `items` | exit 1 — missing rows listed by number |
| 2 | Each item has exactly one of `location` or `not_applicable` | exit 1 if neither; exit 2 if both |
| 3 | `not_applicable` justification is non-empty | exit 1 |
| 4 | Item `number` is one the variant defines | exit 2 — an unknown number means the record and table disagree |
| 5 | `number` unique within `items` | exit 2 |
| 6 | `items` non-empty | exit 2 |
| 7 | `variant` recognised | exit 2 |

## Generated artifact

The completed checklist: section, item number, topic label, and either the location or the
not-applicable justification. Unaddressed rows are listed separately above the table so they are
not lost in forty-two rows of output, with a count.

The artifact links to the source publication for authoritative item wording, and carries a
provenance line naming the generating check and source record.
