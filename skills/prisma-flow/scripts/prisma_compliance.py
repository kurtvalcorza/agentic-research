#!/usr/bin/env python3
"""Evidence-bearing PRISMA 2020 reporting compliance checker. Standard library only.

This is deliberately separate from ``prisma_checklist.py``. The legacy checker
answers "was every row addressed?"; this checker answers the stronger question
"does every row carry a reporting location/N-A assertion, substantive evidence,
and a recorded human confirmation?". Keeping the predicates separate prevents a
location-only checklist from being rendered as compliance verification.

WHAT THIS CHECKS
  All 42 addressable PRISMA 2020 rows; exact row identity; located versus explicitly
  not-applicable disposition, restricted to the items PRISMA 2020 itself makes
  conditional (CONDITIONALLY_APPLICABLE) so a review cannot declare a mandatory
  row (e.g. Title, Rationale, Eligibility criteria) not-applicable; substantive
  evidence for located rows, where "substantive" means at least
  MIN_SUBSTANTIVE_CHARS characters and not a verbatim repeat of the location text;
  and an explicit human confirmation for every positive or N/A compliance
  assertion.

WHAT THIS CANNOT CHECK
  Whether the evidence text or cited manuscript passage actually satisfies the
  PRISMA item, whether an N/A justification is substantively correct even though
  it is long enough, whether the human confirmation is substantively correct, or
  whether the review methods themselves were rigorous. The length floor and the
  conditionally-applicable set catch vacuous and blanket-N/A records; they cannot
  certify that a passing record is methodologically sound. PRISMA is a reporting
  guideline.

EXIT CODES
  0 clean, or violations found without --strict
  1 compliance-record violations under --strict
  2 malformed input — no authoritative artifact is emitted
"""
from __future__ import annotations

import argparse
import json
import sys

SCHEMA_VERSIONS = {"1.0"}
JSON_ENVELOPE_VERSION = "1.0"
VARIANT = "prisma_2020"

PRISMA_2020 = (
    ("Title", "1", "Title"), ("Abstract", "2", "Abstract"),
    ("Introduction", "3", "Rationale"), ("Introduction", "4", "Objectives"),
    ("Methods", "5", "Eligibility criteria"), ("Methods", "6", "Information sources"),
    ("Methods", "7", "Search strategy"), ("Methods", "8", "Selection process"),
    ("Methods", "9", "Data collection process"), ("Methods", "10a", "Data items"),
    ("Methods", "10b", "Data items"), ("Methods", "11", "Study risk of bias assessment"),
    ("Methods", "12", "Effect measures"), ("Methods", "13a", "Synthesis methods"),
    ("Methods", "13b", "Synthesis methods"), ("Methods", "13c", "Synthesis methods"),
    ("Methods", "13d", "Synthesis methods"), ("Methods", "13e", "Synthesis methods"),
    ("Methods", "13f", "Synthesis methods"), ("Methods", "14", "Reporting bias assessment"),
    ("Methods", "15", "Certainty assessment"), ("Results", "16a", "Study selection"),
    ("Results", "16b", "Study selection"), ("Results", "17", "Study characteristics"),
    ("Results", "18", "Risk of bias in studies"), ("Results", "19", "Results of individual studies"),
    ("Results", "20a", "Results of syntheses"), ("Results", "20b", "Results of syntheses"),
    ("Results", "20c", "Results of syntheses"), ("Results", "20d", "Results of syntheses"),
    ("Results", "21", "Reporting biases"), ("Results", "22", "Certainty of evidence"),
    ("Discussion", "23a", "Discussion"), ("Discussion", "23b", "Discussion"),
    ("Discussion", "23c", "Discussion"), ("Discussion", "23d", "Discussion"),
    ("Other information", "24a", "Registration and protocol"),
    ("Other information", "24b", "Registration and protocol"),
    ("Other information", "24c", "Registration and protocol"),
    ("Other information", "25", "Support"), ("Other information", "26", "Competing interests"),
    ("Other information", "27", "Availability of data, code, and other materials"),
)
ROOT_KEYS = {"schema_version", "variant", "items"}
ITEM_KEYS = {"number", "location", "not_applicable", "evidence", "human_confirmed"}

# Items whose OWN PRISMA 2020 wording is conditional — "if applicable", "if
# meta-analysis was done", "if done/performed" — or that report the outcome of a
# method an earlier item (11, 14, 15) allows a review to skip. Every other row
# describes something every systematic review must report regardless of which
# methods it chose, so it can never be legitimately not-applicable. Without this
# set, a record could mark items 1 (Title) through 9 (Data collection process)
# not_applicable and still pass — the all-N/A record this policy exists to reject.
# This is a documented, revisitable convention, not a PRISMA-authored rule: a
# reviewer who disagrees with a specific inclusion changes this set, not the
# reader.
CONDITIONALLY_APPLICABLE = {
    "10b",  # other variables collected, "if applicable"
    "13d",  # methods to synthesise results, "if meta-analysis was done"
    "13e",  # methods to explore heterogeneity, "if applicable"
    "13f",  # sensitivity analyses, "if done"
    "18",   # risk of bias in studies — only if item 11's assessment was performed
    "20b",  # results of statistical syntheses, "if meta-analysis was done"
    "20c",  # investigations of heterogeneity — only if undertaken
    "20d",  # sensitivity analyses results — only if undertaken
    "21",   # reporting bias results — only if item 14's assessment was performed
    "22",   # certainty of evidence — only if item 15's GRADE-style assessment was performed
    "27",   # data/code/materials availability — only if there is material to locate
}

# A one-character "x" or "n" is a value, not an assertion. Chosen to admit the
# shortest plausible genuine sentence ("Not registered.") while rejecting a bare
# token; it is a floor, not a substantiveness judgement software can make.
MIN_SUBSTANTIVE_CHARS = 10


def _substantive(text: str) -> bool:
    return len(text.strip()) >= MIN_SUBSTANTIVE_CHARS


class InputError(ValueError):
    """Malformed input (exit 2)."""


def _obj(value, ctx):
    if not isinstance(value, dict):
        raise InputError(f"{ctx}: expected an object, got {type(value).__name__}")
    return value


def _closed(value, allowed, ctx):
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise InputError(
            f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
            f"(expected one of: {', '.join(sorted(allowed))})"
        )


def _optional_text(value, ctx):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InputError(f"{ctx}: expected a string, got {type(value).__name__} {value!r}")
    return value.strip()


def parse(raw: dict) -> dict[str, dict]:
    _obj(raw, "record")
    _closed(raw, ROOT_KEYS, "record")
    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(f"record: unrecognised or missing schema_version {version!r}")
    if raw.get("variant") != VARIANT:
        raise InputError(f"record.variant: expected {VARIANT!r}, got {raw.get('variant')!r}")
    items = raw.get("items")
    if not isinstance(items, list) or not items:
        raise InputError("record.items: expected a non-empty list")
    valid = {number for _, number, _ in PRISMA_2020}
    entries: dict[str, dict] = {}
    for i, item in enumerate(items):
        ctx = f"record.items[{i}]"
        _obj(item, ctx)
        _closed(item, ITEM_KEYS, ctx)
        number = item.get("number")
        if not isinstance(number, str) or number not in valid:
            raise InputError(f"{ctx}.number: unknown PRISMA 2020 row {number!r}")
        if number in entries:
            raise InputError(f"{ctx}.number: duplicate row {number!r}")
        if "location" in item and "not_applicable" in item:
            raise InputError(f"{ctx}: location and not_applicable are mutually exclusive")
        location = _optional_text(item.get("location"), f"{ctx}.location")
        na = _optional_text(item.get("not_applicable"), f"{ctx}.not_applicable")
        evidence = _optional_text(item.get("evidence"), f"{ctx}.evidence")
        confirmed = item.get("human_confirmed")
        if confirmed is not None and not isinstance(confirmed, bool):
            raise InputError(f"{ctx}.human_confirmed: expected a boolean")
        entries[number] = {
            "location": location,
            "not_applicable": na,
            "evidence": evidence,
            "human_confirmed": confirmed,
        }
    return entries


def check(entries: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    for section, number, topic in PRISMA_2020:
        entry = entries.get(number)
        prefix = f"item {number} ({topic}, {section})"
        if entry is None:
            errors.append(f"{prefix}: missing from compliance record")
            continue
        loc, na = entry["location"], entry["not_applicable"]
        if not loc and not na:
            errors.append(f"{prefix}: neither a manuscript location nor an N/A justification is recorded")
            continue
        if na:
            if number not in CONDITIONALLY_APPLICABLE:
                errors.append(
                    f"{prefix}: not applicable is not a legitimate disposition for this "
                    f"item — PRISMA 2020 requires every review to report it"
                )
            elif not _substantive(na):
                errors.append(
                    f"{prefix}: not-applicable justification is too short to be "
                    f"substantive ({na!r})"
                )
        if loc:
            if not entry["evidence"]:
                errors.append(f"{prefix}: located but no substantive reporting evidence is supplied")
            elif not _substantive(entry["evidence"]):
                errors.append(
                    f"{prefix}: evidence is too short to be substantive ({entry['evidence']!r})"
                )
            elif entry["evidence"].strip().casefold() == loc.strip().casefold():
                errors.append(
                    f"{prefix}: evidence merely restates the location and asserts nothing"
                )
        if entry["human_confirmed"] is not True:
            errors.append(f"{prefix}: compliance assertion is not human-confirmed")
    return errors


def mechanical_defects(entries: dict[str, dict]) -> set[str]:
    """Rows carrying a reporting defect an agent loop can repair.

    This deliberately mirrors every non-human predicate in ``check``: missing rows,
    undisposed rows, invalid N/A dispositions, vacuous N/A justifications, absent or
    vacuous located evidence, and evidence that merely repeats its location. Human
    confirmation is excluded and counted by ``unconfirmed_assertions`` instead.
    Keeping the unit predicate aligned with ``check`` prevents a strict child failure
    from being rendered as zero repairable PRISMA work at the verify-review layer.
    """
    rows: set[str] = set()
    for _section, number, _topic in PRISMA_2020:
        entry = entries.get(number)
        if entry is None:
            rows.add(number)
            continue
        loc, na = entry["location"], entry["not_applicable"]
        if not loc and not na:
            rows.add(number)
            continue
        if na:
            if number not in CONDITIONALLY_APPLICABLE or not _substantive(na):
                rows.add(number)
            continue
        evidence = entry["evidence"]
        if (not evidence or not _substantive(evidence)
                or evidence.strip().casefold() == loc.strip().casefold()):
            rows.add(number)
    return rows


def unconfirmed_assertions(entries: dict[str, dict]) -> int:
    """Recorded compliance assertions still owed a human confirmation.

    Counts rows that ARE disposed (located, or justified as N/A) and whose
    ``human_confirmed`` is not exactly ``true``. A row that is not disposed at all
    is not yet an assertion anyone could confirm, so it belongs to
    ``mechanical_defects`` alone and is not double-booked here.

    This makes the confirmation VISIBLE to the verification loop as a pending human
    gate. It does not make it authentic: nothing here can establish that a person
    actually reviewed the row, only that the record does not yet claim they did.
    """
    total = 0
    for _section, number, _topic in PRISMA_2020:
        entry = entries.get(number)
        if entry is None:
            continue
        if not entry["location"] and not entry["not_applicable"]:
            continue
        if entry["human_confirmed"] is not True:
            total += 1
    return total


def _cell(value):
    return str(value).replace("|", "&#124;").replace("\n", "<br>")


def render(entries: dict[str, dict], errors: list[str], source: str) -> str:
    failing = {err.split(" ", 2)[1] for err in errors}
    passed = len(PRISMA_2020) - len(failing)
    lines = [f"# PRISMA 2020 compliance evidence — {passed} of {len(PRISMA_2020)} rows verified", ""]
    if errors:
        lines += [f"## ⚠️ {len(errors)} issue(s)", ""] + [f"- {e}" for e in errors] + [""]
    else:
        lines += ["✅ Every row is addressed, evidenced where applicable, and human-confirmed.", ""]
    lines += [
        "| Section | # | Topic | Location / N-A justification | Evidence | Human confirmed | Status |",
        "|:--|:--|:--|:--|:--|:--:|:--|",
    ]
    last = None
    for section, number, topic in PRISMA_2020:
        entry = entries.get(number) or {}
        loc = entry.get("location") or ""
        na = entry.get("not_applicable") or ""
        disposition = _cell(loc) if loc else (f"*n/a — {_cell(na)}*" if na else "—")
        evidence = _cell(entry.get("evidence") or "") or "—"
        confirmed = "yes" if entry.get("human_confirmed") is True else "no"
        status = "verified" if number not in failing else "not verified"
        shown = section if section != last else ""
        last = section
        lines.append(f"| {shown} | {number} | {topic} | {disposition} | {evidence} | {confirmed} | {status} |")
    lines += [
        "", "---", "",
        f"*Generated by `prisma_compliance.py` from `{source}`. A clean result means the recorded "
        "reporting assertions are evidence-bearing and human-confirmed; it does not score methodological "
        "quality and cannot make the underlying human judgment infallible.*",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate evidence-bearing PRISMA 2020 reporting compliance records.")
    parser.add_argument("infile", nargs="?")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    source = args.infile or "stdin"
    try:
        text = open(args.infile, encoding="utf-8").read() if args.infile else sys.stdin.read()
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"prisma_compliance: cannot read {source} ({exc})\n")
        return 2
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"prisma_compliance: invalid JSON ({exc})\n")
        return 2
    try:
        entries = parse(raw)
    except InputError as exc:
        sys.stderr.write(f"prisma_compliance: {exc}\n")
        return 2
    errors = check(entries)
    if args.json:
        json.dump(
            {
                "check": "prisma_compliance", "schema_version": JSON_ENVELOPE_VERSION,
                "issues": len(errors),
                "units": {"U_prisma_compliance": len(mechanical_defects(entries))},
                "gates": {"H_prisma_evidence": unconfirmed_assertions(entries)},
                "unattributed": 0,
            }, sys.stdout, indent=2,
        )
        sys.stdout.write("\n")
        return 1 if errors and args.strict else 0
    print(render(entries, errors, source))
    return 1 if errors and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
