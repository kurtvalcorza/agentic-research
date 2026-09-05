#!/usr/bin/env python3
"""PRISMA 2020 for Abstracts checker. Standard library only.

The checker supports two explicit verification levels:

* ``addressability`` — every item has a location or explicit not-applicable
  justification.
* ``compliance`` — every applicable item also carries evidence and an explicit
  human confirmation. This prevents a location pointer from being represented as
  substantive compliance.

A clean result means the record satisfies the declared verification contract. It
never means the underlying human judgment was correct.
"""
from __future__ import annotations

import argparse
import json
import sys

SCHEMA_VERSIONS = {"1.0"}
JSON_ENVELOPE_VERSION = "1.0"
VARIANT = "prisma_2020_abstracts"
VERIFICATION_LEVELS = {"addressability", "compliance"}

# Topic labels from the PRISMA 2020 for Abstracts checklist. Full item wording is
# intentionally not reproduced here; consult the source publication/checklist.
PRISMA_ABSTRACTS = (
    ("1", "Title"),
    ("2", "Objectives"),
    ("3", "Eligibility criteria"),
    ("4", "Information sources"),
    ("5", "Risk of bias"),
    ("6", "Synthesis of results"),
    ("7", "Included studies"),
    ("8", "Results of synthesis"),
    ("9", "Limitations of evidence"),
    ("10", "Interpretation"),
    ("11", "Funding"),
    ("12", "Registration"),
)

RECORD_KEYS = {"schema_version", "variant", "verification", "items"}
ITEM_KEYS = {"number", "location", "not_applicable", "evidence", "human_confirmed"}


class InputError(ValueError):
    """Malformed input: exit 2 and emit no authoritative artifact."""


def _obj(value, ctx):
    if not isinstance(value, dict):
        raise InputError(f"{ctx}: expected an object, got {type(value).__name__}")
    return value


def _no_unknown_keys(value, allowed, ctx):
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise InputError(
            f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
            f"(expected one of: {', '.join(sorted(allowed))})"
        )


def _text(value, ctx, *, optional=False):
    if value is None and optional:
        return ""
    if not isinstance(value, str):
        raise InputError(f"{ctx}: expected a string, got {type(value).__name__} {value!r}")
    return value.strip()


def parse(raw: dict) -> tuple[str, dict[str, dict]]:
    _obj(raw, "record")
    _no_unknown_keys(raw, RECORD_KEYS, "record")

    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(
            f"record: unrecognised or missing schema_version {version!r} "
            f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})"
        )

    variant = raw.get("variant")
    if variant != VARIANT:
        raise InputError(f"record: variant must be {VARIANT!r}, got {variant!r}")

    verification = raw.get("verification")
    if verification not in VERIFICATION_LEVELS:
        raise InputError(
            f"record: verification must be one of {', '.join(sorted(VERIFICATION_LEVELS))}, "
            f"got {verification!r}"
        )

    items = raw.get("items")
    if not isinstance(items, list):
        raise InputError("record: 'items' must be a list")
    if not items:
        raise InputError("record: 'items' is empty — there is nothing to check")

    valid_numbers = {number for number, _ in PRISMA_ABSTRACTS}
    entries: dict[str, dict] = {}
    for i, item in enumerate(items):
        ctx = f"items[{i}]"
        _obj(item, ctx)
        _no_unknown_keys(item, ITEM_KEYS, ctx)

        number = item.get("number")
        if not isinstance(number, str):
            raise InputError(f"{ctx}.number: expected a string, got {number!r}")
        if number not in valid_numbers:
            raise InputError(f"{ctx}.number: {number!r} is not an item of {VARIANT}")
        if number in entries:
            raise InputError(f"{ctx}.number: duplicate item {number!r}")

        has_location = "location" in item
        has_na = "not_applicable" in item
        if has_location and has_na:
            raise InputError(
                f"{ctx}: item {number} has both 'location' and 'not_applicable' — "
                "an item is one or the other"
            )

        location = _text(item.get("location"), f"{ctx}.location", optional=True)
        not_applicable = _text(
            item.get("not_applicable"), f"{ctx}.not_applicable", optional=True
        )
        evidence = _text(item.get("evidence"), f"{ctx}.evidence", optional=True)
        confirmed = item.get("human_confirmed")
        if confirmed is not None and not isinstance(confirmed, bool):
            raise InputError(
                f"{ctx}.human_confirmed: expected a boolean, got "
                f"{type(confirmed).__name__} {confirmed!r}"
            )

        entries[number] = {
            "location": location,
            "not_applicable": not_applicable,
            "evidence": evidence,
            "human_confirmed": confirmed,
        }

    return verification, entries


def check(verification: str, entries: dict[str, dict]) -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []
    statuses: dict[str, str] = {}

    for number, topic in PRISMA_ABSTRACTS:
        entry = entries.get(number)
        if entry is None:
            errors.append(
                f"item {number} ({topic}): not addressed — record a location or an explicit "
                "not_applicable justification"
            )
            statuses[number] = "not addressed"
            continue

        location = entry["location"]
        na = entry["not_applicable"]
        if not location and not na:
            errors.append(
                f"item {number} ({topic}): present but neither located nor justified"
            )
            statuses[number] = "not addressed"
            continue

        if verification == "addressability":
            statuses[number] = "addressed"
            continue

        # Compliance mode deliberately requires a human gate for both a positive
        # reporting assertion and an N/A judgment. A location pointer alone is not
        # substantive evidence that the reporting requirement is met.
        if location and not entry["evidence"]:
            errors.append(
                f"item {number} ({topic}): location recorded but no substantive evidence supplied"
            )
        if entry["human_confirmed"] is not True:
            errors.append(
                f"item {number} ({topic}): substantive compliance is not human-confirmed"
            )

        statuses[number] = (
            "verified"
            if not any(err.startswith(f"item {number} ") for err in errors)
            else "not verified"
        )

    return errors, statuses


def _cell(value: object) -> str:
    return (
        str(value)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("|", "&#124;")
        .replace("\n", "<br>")
    )


def render(verification: str, entries: dict[str, dict], errors: list[str],
           statuses: dict[str, str], source: str) -> str:
    total = len(PRISMA_ABSTRACTS)
    passed = sum(statuses.get(number) in {"addressed", "verified"}
                 for number, _ in PRISMA_ABSTRACTS)
    label = "verified" if verification == "compliance" else "addressed"
    lines = [f"# PRISMA 2020 for Abstracts — {passed} of {total} items {label}", ""]
    if errors:
        lines += [f"## ⚠️ {len(errors)} issue(s)", ""] + [f"- {e}" for e in errors] + [""]
    else:
        lines += [f"✅ Every abstract item satisfies the declared `{verification}` contract.", ""]

    lines += [
        "| # | Topic | Location / justification | Evidence | Human confirmed | Status |",
        "|:--|:--|:--|:--|:--:|:--|",
    ]
    for number, topic in PRISMA_ABSTRACTS:
        entry = entries.get(number) or {}
        location = entry.get("location") or ""
        na = entry.get("not_applicable") or ""
        loc_cell = _cell(location) if location else (f"*n/a — {_cell(na)}*" if na else "—")
        evidence = _cell(entry.get("evidence") or "") or "—"
        confirmed = "yes" if entry.get("human_confirmed") is True else "no"
        lines.append(
            f"| {number} | {topic} | {loc_cell} | {evidence} | {confirmed} | "
            f"{statuses.get(number, 'not addressed')} |"
        )

    lines += [
        "",
        "*Item numbers and topic labels follow the PRISMA 2020 for Abstracts checklist. "
        "Consult the source for full item wording.*",
        "",
        "---",
        "",
        f"*Generated by `prisma_abstract_checklist.py` from `{source}` in "
        f"`{verification}` mode. A clean compliance record means evidence was supplied and "
        "human-confirmed for every applicable item; it does not make the underlying judgment "
        "infallible.*",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check PRISMA 2020 for Abstracts reporting addressability/compliance."
    )
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
        raw = open(args.infile, encoding="utf-8").read() if args.infile else sys.stdin.read()
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"prisma_abstract_checklist: cannot read {source} ({exc})\n")
        return 2

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"prisma_abstract_checklist: input is not valid JSON ({exc})\n")
        return 2

    try:
        verification, entries = parse(data)
    except InputError as exc:
        sys.stderr.write(f"prisma_abstract_checklist: {exc}\n")
        return 2

    errors, statuses = check(verification, entries)
    if args.json:
        json.dump(
            {
                "check": "prisma_abstract_checklist",
                "schema_version": JSON_ENVELOPE_VERSION,
                "issues": len(errors),
                "units": {"U_prisma_abstract": len({e.split(' ', 2)[1] for e in errors})},
                "gates": {},
                "unattributed": 0,
                "detail": {"verification": verification},
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 1 if errors and args.strict else 0

    print(render(verification, entries, errors, statuses, source))
    return 1 if errors and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
