#!/usr/bin/env python3
"""
prisma_checklist.py — check reporting completeness against the PRISMA 2020 checklist
and generate the completed checklist from the record. Standard library only.

WHAT THIS CHECKS
  That every addressable row of the checklist is either located in the manuscript
  or explicitly justified as not applicable, and that no row is left silently
  unaddressed.

WHAT THIS CANNOT CHECK
  Whether the cited location ACTUALLY addresses the item. "Methods, p.4" satisfies
  this script whether or not page 4 says anything relevant. It verifies that a
  location was recorded, not that the reporting is adequate.

⚠️ 27 NUMBERED ITEMS, 42 ADDRESSABLE ROWS
  PRISMA 2020 is customarily cited as "27 items", but several expand into lettered
  sub-items (10a-b, 13a-f, 16a-b, 20a-d, 23a-d, 24a-c). Completeness is evaluated
  over the 42 rows. Checking only the 27 top-level numbers would report a manuscript
  complete while six sub-items of item 13 alone went unaddressed.

  Item numbers and topic labels transcribed from Table 1 of:
    Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated
    guideline for reporting systematic reviews. BMJ 2021;372:n71. CC BY 4.0.
  Official item wording is REFERENCED, not reproduced — consult the source for it.

INPUT — a JSON record (file arg or stdin):
{
  "schema_version": "1.0",
  "variant": "prisma_2020",
  "items": [
    {"number": "1",   "location": "Title page"},
    {"number": "13d", "not_applicable": "No meta-analysis; synthesis is narrative per SWiM."}
  ]
}

USAGE
  python prisma_checklist.py checklist.json --strict

EXIT CODES
  0 clean, or unaddressed rows found without --strict
  1 rows unaddressed under --strict
  2 malformed input — no artifact is emitted
"""
from __future__ import annotations

import argparse
import json
import sys

SCHEMA_VERSIONS = {"1.0"}

# (section, number, topic) — 42 rows. Verified against BMJ 2021;372:n71 Table 1.
# Lettered sub-items carry their parent's topic label, exactly as the source does;
# consult the source for the wording that distinguishes them.
PRISMA_2020 = (
    ("Title", "1", "Title"),
    ("Abstract", "2", "Abstract"),
    ("Introduction", "3", "Rationale"),
    ("Introduction", "4", "Objectives"),
    ("Methods", "5", "Eligibility criteria"),
    ("Methods", "6", "Information sources"),
    ("Methods", "7", "Search strategy"),
    ("Methods", "8", "Selection process"),
    ("Methods", "9", "Data collection process"),
    ("Methods", "10a", "Data items"),
    ("Methods", "10b", "Data items"),
    ("Methods", "11", "Study risk of bias assessment"),
    ("Methods", "12", "Effect measures"),
    ("Methods", "13a", "Synthesis methods"),
    ("Methods", "13b", "Synthesis methods"),
    ("Methods", "13c", "Synthesis methods"),
    ("Methods", "13d", "Synthesis methods"),
    ("Methods", "13e", "Synthesis methods"),
    ("Methods", "13f", "Synthesis methods"),
    ("Methods", "14", "Reporting bias assessment"),
    ("Methods", "15", "Certainty assessment"),
    ("Results", "16a", "Study selection"),
    ("Results", "16b", "Study selection"),
    ("Results", "17", "Study characteristics"),
    ("Results", "18", "Risk of bias in studies"),
    ("Results", "19", "Results of individual studies"),
    ("Results", "20a", "Results of syntheses"),
    ("Results", "20b", "Results of syntheses"),
    ("Results", "20c", "Results of syntheses"),
    ("Results", "20d", "Results of syntheses"),
    ("Results", "21", "Reporting biases"),
    ("Results", "22", "Certainty of evidence"),
    ("Discussion", "23a", "Discussion"),
    ("Discussion", "23b", "Discussion"),
    ("Discussion", "23c", "Discussion"),
    ("Discussion", "23d", "Discussion"),
    ("Other information", "24a", "Registration and protocol"),
    ("Other information", "24b", "Registration and protocol"),
    ("Other information", "24c", "Registration and protocol"),
    ("Other information", "25", "Support"),
    ("Other information", "26", "Competing interests"),
    ("Other information", "27", "Availability of data, code, and other materials"),
)

# PRISMA-ScR (scoping reviews) is DELIBERATELY NOT IMPLEMENTED.
#
# Its checklist is 20 essential plus 2 optional items, but the item table could not
# be transcribed from an accessible copy of the source: the official site serves the
# checklist only as a PDF download, and the Annals of Internal Medicine article
# (Tricco AC, et al. Ann Intern Med. 2018;169:467-473. doi:10.7326/M18-0850) is not
# retrievable without a subscription.
#
# An APPROXIMATED table is worse than no table at all: every completeness verdict it
# produced would be wrong while looking authoritative, which is precisely the false
# confidence this repository exists to prevent. So the variant refuses rather than
# guesses. To enable it, transcribe the table from the source, add it below, and
# update the README's standards row.
VARIANTS = {"prisma_2020": PRISMA_2020}
KNOWN_UNIMPLEMENTED = {
    "prisma_scr": ("PRISMA-ScR is not implemented: its item table has not been transcribed "
                   "from the source publication (Tricco et al., Ann Intern Med 2018, "
                   "doi:10.7326/M18-0850). An approximated table would make every "
                   "completeness verdict wrong while appearing authoritative, so this "
                   "variant refuses rather than guesses."),
}

ITEM_KEYS = {"number", "location", "not_applicable"}


class InputError(ValueError):
    """The record cannot be read. Fails closed: exit 2, no artifact emitted."""


def _obj(v, name):
    if not isinstance(v, dict):
        raise InputError(f"{name}: expected an object, got {type(v).__name__}")
    return v


def _no_unknown_keys(d, allowed, ctx):
    unknown = sorted(set(d) - set(allowed))
    if unknown:
        raise InputError(f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
                         f"(expected one of: {', '.join(sorted(allowed))})")


def parse(raw: dict) -> tuple[tuple, dict]:
    """Return (item table, {number: entry}). Raises InputError on malformed input."""
    _obj(raw, "record")
    _no_unknown_keys(raw, {"schema_version", "variant", "items"}, "record")

    version = raw.get("schema_version")
    # isinstance FIRST: an unhashable value raises TypeError on set membership.
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(f"record: unrecognised or missing schema_version {version!r} "
                         f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})")

    variant = raw.get("variant")
    if not isinstance(variant, str):
        raise InputError(f"record: variant must be a string, got "
                         f"{type(variant).__name__} {variant!r}")
    if variant in KNOWN_UNIMPLEMENTED:
        raise InputError(KNOWN_UNIMPLEMENTED[variant])
    if variant not in VARIANTS:
        raise InputError(f"record: variant must be one of {', '.join(sorted(VARIANTS))}, "
                         f"got {variant!r}")
    table = VARIANTS[variant]
    valid_numbers = {n for _, n, _ in table}

    items = raw.get("items")
    if not isinstance(items, list):
        raise InputError("record: 'items' must be a list")
    if not items:
        raise InputError("record: 'items' is empty — there is nothing to check")

    entries: dict[str, dict] = {}
    for i, it in enumerate(items):
        ctx = f"items[{i}]"
        _obj(it, ctx)
        _no_unknown_keys(it, ITEM_KEYS, ctx)

        number = it.get("number")
        if not isinstance(number, str):
            raise InputError(f"{ctx}.number: expected a string, got {number!r}")
        if number not in valid_numbers:
            raise InputError(f"{ctx}.number: {number!r} is not an item of {variant} — "
                             f"the record and the checklist disagree")
        if number in entries:
            raise InputError(f"{ctx}.number: duplicate item {number!r}")

        has_loc = "location" in it
        has_na = "not_applicable" in it
        if has_loc and has_na:
            raise InputError(f"{ctx}: item {number} has both 'location' and "
                             f"'not_applicable' — an item is one or the other")

        # Both fields are TEXT. A number, boolean, object or list is malformed input
        # (exit 2), not merely an unaddressed item (exit 1) — otherwise a typo in the
        # record type would be reported as a reporting gap and "fixed" in the wrong file.
        for field in ("location", "not_applicable"):
            if field in it and not isinstance(it[field], str):
                raise InputError(f"{ctx}.{field}: expected a string, got "
                                 f"{type(it[field]).__name__} {it[field]!r}")

        entries[number] = {"location": it.get("location"),
                           "not_applicable": it.get("not_applicable")}
    return table, entries


def check(table: tuple, entries: dict) -> list[str]:
    """Return the list of rows that are neither located nor justified."""
    errs = []
    for section, number, topic in table:
        e = entries.get(number)
        if e is None:
            errs.append(f"item {number} ({topic}, {section}): not addressed — record a "
                        f"location or an explicit not_applicable justification")
            continue
        loc = (e["location"] or "").strip() if isinstance(e["location"], str) else ""
        na = (e["not_applicable"] or "").strip() if isinstance(e["not_applicable"], str) else ""
        if not loc and not na:
            errs.append(f"item {number} ({topic}): present in the record but neither located "
                        f"nor justified — an empty value does not address the item")
    return errs


def _markdown_cell(value: object) -> str:
    """Render caller-controlled text without creating extra table cells or rows."""
    return (str(value).replace("\r\n", "\n").replace("\r", "\n")
            .replace("|", "&#124;").replace("\n", "<br>"))


def render(table: tuple, entries: dict, errs: list[str], variant: str) -> str:
    total = len(table)
    addressed = total - len(errs)
    lines = [f"# PRISMA 2020 checklist — {addressed} of {total} rows addressed", ""]

    # Unaddressed rows go ABOVE the table, with a count. In forty-two rows, a gap
    # reported only by a blank cell somewhere in the middle is a gap nobody sees.
    if errs:
        lines += [f"## ⚠️ {len(errs)} row(s) not addressed", ""]
        lines += [f"- {e}" for e in errs]
        lines.append("")
    else:
        lines += ["✅ Every row is either located in the manuscript or explicitly justified "
                  "as not applicable.", ""]

    lines += ["## Checklist", "",
              "| Section | # | Topic | Location / justification |",
              "|:--|:--|:--|:--|"]
    last_section = None
    for section, number, topic in table:
        e = entries.get(number) or {}
        loc = (e.get("location") or "").strip() if isinstance(e.get("location"), str) else ""
        na = (e.get("not_applicable") or "").strip() \
            if isinstance(e.get("not_applicable"), str) else ""
        if loc:
            cell = _markdown_cell(loc)
        elif na:
            cell = f"*n/a — {_markdown_cell(na)}*"
        else:
            cell = "⚠️ **not addressed**"
        shown_section = section if section != last_section else ""
        last_section = section
        lines.append(f"| {shown_section} | {number} | {topic} | {cell} |")

    lines += ["",
              "*Item numbers and topic labels from Page MJ, et al. The PRISMA 2020 statement. "
              "BMJ 2021;372:n71 (CC BY 4.0). Consult the source for the full wording of each "
              "item — it is referenced here, not reproduced.*",
              "",
              "---",
              "",
              f"*Generated by `prisma_checklist.py` (variant `{variant}`). This check verifies "
              f"that a location or justification was recorded for every row. It cannot verify "
              f"that the cited location actually addresses the item.*"]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check reporting completeness and generate the PRISMA 2020 checklist.")
    ap.add_argument("infile", nargs="?")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any row is unaddressed")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    source = args.infile or "stdin"
    try:
        if args.infile:
            with open(args.infile, encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except OSError as e:
        sys.stderr.write(f"prisma_checklist: cannot read {source} ({e})\n")
        return 2

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"prisma_checklist: input is not valid JSON ({e})\n")
        return 2

    try:
        table, entries = parse(data)
    except InputError as e:
        sys.stderr.write(f"prisma_checklist: {e}\n")
        return 2

    errs = check(table, entries)
    print(render(table, entries, errs, data.get("variant", "")))
    return 1 if (errs and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
