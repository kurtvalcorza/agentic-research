#!/usr/bin/env python3
"""
prisma_checklist.py — check PRISMA 2020 reporting addressability or substantive
compliance evidence and generate the completed checklist. Standard library only.

Two explicit verification levels are supported:

* ``addressability`` (the backwards-compatible default): every addressable row is
  either located in the manuscript or explicitly justified as not applicable.
* ``compliance``: every applicable row is located, carries a substantive evidence
  assertion, and is explicitly human-confirmed. N/A judgments also require human
  confirmation.

A clean compliance record means the declared evidence/human-gate contract is
complete. The script still cannot decide whether the human judgment itself was
correct; PRISMA is a reporting guideline, not a methodological-quality score.

⚠️ 27 NUMBERED ITEMS, 42 ADDRESSABLE ROWS
PRISMA 2020 is customarily cited as "27 items", but several expand into lettered
sub-items (10a-b, 13a-f, 16a-b, 20a-d, 23a-d, 24a-c). Completeness is evaluated
over the 42 rows.
"""
from __future__ import annotations

import argparse
import json
import sys

SCHEMA_VERSIONS = {"1.0"}
JSON_ENVELOPE_VERSION = "1.0"
VERIFICATION_LEVELS = {"addressability", "compliance"}

# (section, number, topic) — 42 rows. Verified against BMJ 2021;372:n71 Table 1.
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

VARIANTS = {"prisma_2020": PRISMA_2020}
KNOWN_UNIMPLEMENTED = {
    "prisma_scr": (
        "PRISMA-ScR is not implemented: its item table has not been transcribed "
        "from the source publication (Tricco et al., Ann Intern Med 2018, "
        "doi:10.7326/M18-0850). An approximated table would make every "
        "completeness verdict wrong while appearing authoritative, so this "
        "variant refuses rather than guesses."
    ),
}

RECORD_KEYS = {"schema_version", "variant", "verification", "items"}
ITEM_KEYS = {"number", "location", "not_applicable", "evidence", "human_confirmed"}


class InputError(ValueError):
    """The record cannot be read. Fails closed: exit 2, no artifact emitted."""


def _obj(v, name):
    if not isinstance(v, dict):
        raise InputError(f"{name}: expected an object, got {type(v).__name__}")
    return v


def _no_unknown_keys(d, allowed, ctx):
    unknown = sorted(set(d) - set(allowed))
    if unknown:
        raise InputError(
            f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
            f"(expected one of: {', '.join(sorted(allowed))})"
        )


def parse_record(raw: dict) -> tuple[tuple, dict, str]:
    """Return (item table, entries, verification)."""
    _obj(raw, "record")
    _no_unknown_keys(raw, RECORD_KEYS, "record")

    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(
            f"record: unrecognised or missing schema_version {version!r} "
            f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})"
        )

    variant = raw.get("variant")
    if not isinstance(variant, str):
        raise InputError(
            f"record: variant must be a string, got {type(variant).__name__} {variant!r}"
        )
    if variant in KNOWN_UNIMPLEMENTED:
        raise InputError(KNOWN_UNIMPLEMENTED[variant])
    if variant not in VARIANTS:
        raise InputError(
            f"record: variant must be one of {', '.join(sorted(VARIANTS))}, got {variant!r}"
        )

    verification = raw.get("verification", "addressability")
    if not isinstance(verification, str) or verification not in VERIFICATION_LEVELS:
        raise InputError(
            f"record: verification must be one of {', '.join(sorted(VERIFICATION_LEVELS))}, "
            f"got {verification!r}"
        )

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
            raise InputError(
                f"{ctx}.number: {number!r} is not an item of {variant} — "
                "the record and the checklist disagree"
            )
        if number in entries:
            raise InputError(f"{ctx}.number: duplicate item {number!r}")

        has_loc = "location" in it
        has_na = "not_applicable" in it
        if has_loc and has_na:
            raise InputError(
                f"{ctx}: item {number} has both 'location' and 'not_applicable' — "
                "an item is one or the other"
            )

        for field in ("location", "not_applicable", "evidence"):
            if field in it and not isinstance(it[field], str):
                raise InputError(
                    f"{ctx}.{field}: expected a string, got "
                    f"{type(it[field]).__name__} {it[field]!r}"
                )
        if "human_confirmed" in it and not isinstance(it["human_confirmed"], bool):
            raise InputError(
                f"{ctx}.human_confirmed: expected a boolean, got "
                f"{type(it['human_confirmed']).__name__} {it['human_confirmed']!r}"
            )

        entries[number] = {
            "location": it.get("location"),
            "not_applicable": it.get("not_applicable"),
            "evidence": it.get("evidence"),
            "human_confirmed": it.get("human_confirmed"),
        }

    return table, entries, verification


def parse(raw: dict) -> tuple[tuple, dict]:
    """Backwards-compatible parser used by existing callers/tests."""
    table, entries, _ = parse_record(raw)
    return table, entries


def check(table: tuple, entries: dict) -> list[str]:
    """Return rows neither located nor explicitly justified (legacy contract)."""
    errs = []
    for section, number, topic in table:
        e = entries.get(number)
        if e is None:
            errs.append(
                f"item {number} ({topic}, {section}): not addressed — record a "
                "location or an explicit not_applicable justification"
            )
            continue
        loc = (e.get("location") or "").strip() if isinstance(e.get("location"), str) else ""
        na = (e.get("not_applicable") or "").strip() \
            if isinstance(e.get("not_applicable"), str) else ""
        if not loc and not na:
            errs.append(
                f"item {number} ({topic}): present in the record but neither located "
                "nor justified — an empty value does not address the item"
            )
    return errs


def check_compliance(table: tuple, entries: dict) -> list[str]:
    """Return rows that cannot support a substantive compliance assertion."""
    address_errors = check(table, entries)
    errors = list(address_errors)
    bad_numbers = {e.split(" ", 2)[1] for e in address_errors}
    for _, number, topic in table:
        if number in bad_numbers:
            continue
        entry = entries[number]
        location = (entry.get("location") or "").strip()
        na = (entry.get("not_applicable") or "").strip()
        evidence = (entry.get("evidence") or "").strip()
        if location and not evidence:
            errors.append(
                f"item {number} ({topic}): location recorded but no substantive evidence supplied"
            )
        if entry.get("human_confirmed") is not True:
            kind = "not-applicable judgment" if na else "substantive compliance"
            errors.append(f"item {number} ({topic}): {kind} is not human-confirmed")
    return errors


def _markdown_cell(value: object) -> str:
    return (
        str(value)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("|", "&#124;")
        .replace("\n", "<br>")
    )


def render(table: tuple, entries: dict, errs: list[str], variant: str,
           source: str = "stdin") -> str:
    """Legacy addressability artifact; intentionally byte-compatible in shape."""
    total = len(table)
    addressed = total - len(errs)
    lines = [f"# PRISMA 2020 checklist — {addressed} of {total} rows addressed", ""]

    if errs:
        lines += [f"## ⚠️ {len(errs)} row(s) not addressed", ""]
        lines += [f"- {e}" for e in errs]
        lines.append("")
    else:
        lines += [
            "✅ Every row is either located in the manuscript or explicitly justified "
            "as not applicable.",
            "",
        ]

    lines += [
        "## Checklist",
        "",
        "| Section | # | Topic | Location / justification |",
        "|:--|:--|:--|:--|",
    ]
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

    lines += [
        "",
        "*Item numbers and topic labels from Page MJ, et al. The PRISMA 2020 statement. "
        "BMJ 2021;372:n71 (CC BY 4.0). Consult the source for the full wording of each "
        "item — it is referenced here, not reproduced.*",
        "",
        "---",
        "",
        f"*Generated by `prisma_checklist.py` from `{source}` (variant `{variant}`). "
        "This check verifies that a location or justification was recorded for every "
        "row. It cannot verify that the cited location actually addresses the item.*",
    ]
    return "\n".join(lines)


def render_compliance(table: tuple, entries: dict, errs: list[str], variant: str,
                      source: str = "stdin") -> str:
    failing = {e.split(" ", 2)[1] for e in errs}
    verified = len(table) - len(failing)
    lines = [
        f"# PRISMA 2020 compliance evidence — {verified} of {len(table)} rows verified",
        "",
    ]
    if errs:
        lines += [f"## ⚠️ {len(errs)} issue(s)", ""] + [f"- {e}" for e in errs] + [""]
    else:
        lines += [
            "✅ Every row is addressed, evidenced, and human-confirmed under the declared contract.",
            "",
        ]

    lines += [
        "## Checklist",
        "",
        "| Section | # | Topic | Location / justification | Evidence | Human confirmed | Status |",
        "|:--|:--|:--|:--|:--|:--:|:--|",
    ]
    last_section = None
    for section, number, topic in table:
        entry = entries.get(number) or {}
        loc = (entry.get("location") or "").strip()
        na = (entry.get("not_applicable") or "").strip()
        location = _markdown_cell(loc) if loc else (f"*n/a — {_markdown_cell(na)}*" if na else "—")
        evidence = _markdown_cell((entry.get("evidence") or "").strip()) or "—"
        confirmed = "yes" if entry.get("human_confirmed") is True else "no"
        status = "verified" if number not in failing else "not verified"
        shown_section = section if section != last_section else ""
        last_section = section
        lines.append(
            f"| {shown_section} | {number} | {topic} | {location} | {evidence} | "
            f"{confirmed} | {status} |"
        )

    lines += [
        "",
        "*Item numbers and topic labels from Page MJ, et al. The PRISMA 2020 statement. "
        "BMJ 2021;372:n71 (CC BY 4.0). Consult the source for full item wording.*",
        "",
        "---",
        "",
        f"*Generated by `prisma_checklist.py` from `{source}` (variant `{variant}`, "
        "verification `compliance`). A clean record means the declared evidence and human "
        "confirmation gates are complete; it does not certify methodological quality or make "
        "the underlying human judgments infallible.*",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check PRISMA 2020 reporting addressability or compliance evidence."
    )
    ap.add_argument("infile", nargs="?")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
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
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write(f"prisma_checklist: cannot read {source} ({e})\n")
        return 2

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"prisma_checklist: input is not valid JSON ({e})\n")
        return 2

    try:
        table, entries, verification = parse_record(data)
    except InputError as e:
        sys.stderr.write(f"prisma_checklist: {e}\n")
        return 2

    errors = check(table, entries) if verification == "addressability" else check_compliance(table, entries)
    failing_rows = {e.split(" ", 2)[1] for e in errors}

    if args.json:
        json.dump(
            {
                "check": "prisma_checklist",
                "schema_version": JSON_ENVELOPE_VERSION,
                "issues": len(errors),
                "units": {"U_checklist": len(failing_rows)},
                "gates": {},
                "unattributed": 0,
                "detail": {"verification": verification},
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 1 if errors and args.strict else 0

    if verification == "compliance":
        print(render_compliance(table, entries, errors, data.get("variant", ""), source))
    else:
        print(render(table, entries, errors, data.get("variant", ""), source))
    return 1 if errors and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
