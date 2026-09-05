#!/usr/bin/env python3
"""Reconcile and render PRISMA 2020 updated-review flow records. Standard library only.

The existing ``prisma_flow.py`` remains the backwards-compatible new-review
checker. This companion implements the official updated-review shape explicitly,
including the previous review, newly identified/included evidence, and updated
totals. The ``variant`` is mandatory so database/register-only and +other-methods
records cannot be inferred ambiguously.

WHAT THIS CHECKS
  New-search flow arithmetic; independent other-methods-arm arithmetic where the
  explicit variant enables it; previous + new = updated study/report totals; and
  report/study cardinality (reports may not be fewer than studies) for the
  previous review's own arm as well as for the newly included evidence.

WHAT THIS CANNOT CHECK
  Whether the supplied counts are true, whether reports have been correctly linked
  to studies, whether search/screening decisions are correct, or whether the prior
  review counts were transcribed accurately. Reconciliation is consistency, not
  provenance authentication.

EXIT CODES
  0 reconciles, or violations found without --strict
  1 reconciliation violations under --strict
  2 malformed input — no authoritative artifact is emitted
"""
from __future__ import annotations

import argparse
import json
import math
import sys

SCHEMA_VERSIONS = {"1.0"}
JSON_ENVELOPE_VERSION = "1.0"
VARIANTS = {"updated_databases_registers", "updated_databases_registers_other_methods"}
BREAKDOWN_KEYS = {
    "identified_databases", "identified_registers", "identified_other",
    "reports_excluded", "other_reports_excluded",
}
COUNT_KEYS = {
    "duplicates_removed", "removed_other_reasons", "records_screened",
    "records_excluded_title_abstract", "reports_sought", "reports_not_retrieved",
    "reports_assessed", "new_studies_included_databases", "other_reports_sought",
    "other_reports_not_retrieved", "other_reports_assessed", "new_studies_included_other",
    "previous_studies_included", "previous_reports_included", "new_studies_included",
    "new_reports_included", "updated_studies_included", "updated_reports_included",
}
ROOT_KEYS = {"schema_version", "variant"} | BREAKDOWN_KEYS | COUNT_KEYS
OTHER_KEYS = {
    "identified_other", "other_reports_sought", "other_reports_not_retrieved",
    "other_reports_assessed", "other_reports_excluded", "new_studies_included_other",
}


class CountError(ValueError):
    """Malformed input (exit 2)."""


def _int(value, ctx):
    if isinstance(value, bool):
        raise CountError(f"{ctx}: expected a whole non-negative JSON number, got boolean")
    if isinstance(value, int):
        out = value
    elif isinstance(value, float) and math.isfinite(value) and value.is_integer():
        out = int(value)
    else:
        raise CountError(f"{ctx}: expected a whole non-negative JSON number, got {value!r}")
    if out < 0:
        raise CountError(f"{ctx}: count must be non-negative")
    return out


def _mapping(value, ctx):
    if not isinstance(value, dict):
        raise CountError(f"{ctx}: expected an object mapping labels to counts")
    return {str(key): _int(count, f"{ctx}.{key}") for key, count in value.items()}


def parse(raw):
    if not isinstance(raw, dict):
        raise CountError("record: expected an object")
    unknown = sorted(set(raw) - ROOT_KEYS)
    if unknown:
        raise CountError(f"record: unrecognised key(s) {', '.join(repr(k) for k in unknown)}")
    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise CountError(f"record: unrecognised or missing schema_version {version!r}")
    variant = raw.get("variant")
    if not isinstance(variant, str) or variant not in VARIANTS:
        raise CountError(f"record.variant: expected one of {sorted(VARIANTS)!r}, got {variant!r}")
    required = {
        "identified_databases", "identified_registers", "duplicates_removed",
        "removed_other_reasons", "records_screened", "records_excluded_title_abstract",
        "reports_sought", "reports_not_retrieved", "reports_assessed", "reports_excluded",
        "new_studies_included_databases", "previous_studies_included", "previous_reports_included",
        "new_studies_included", "new_reports_included", "updated_studies_included",
        "updated_reports_included",
    }
    if variant == "updated_databases_registers_other_methods":
        required |= OTHER_KEYS
    missing = sorted(required - set(raw))
    if missing:
        raise CountError(f"record: missing required updated-review field(s): {', '.join(missing)}")
    if variant == "updated_databases_registers" and (OTHER_KEYS & set(raw)):
        raise CountError("record: other-methods fields are not permitted by the databases/registers-only variant")

    record = {"schema_version": version, "variant": variant}
    for key in BREAKDOWN_KEYS & set(raw):
        record[key] = _mapping(raw[key], key)
    for key in COUNT_KEYS & set(raw):
        record[key] = _int(raw[key], key)
    return record


def _sum(mapping):
    return sum(mapping.values())


def check(c):
    errors = []
    if c["previous_reports_included"] < c["previous_studies_included"]:
        errors.append(
            f"previous review: previous_reports_included={c['previous_reports_included']} "
            f"cannot be fewer than previous_studies_included={c['previous_studies_included']}"
        )
    identified_db = _sum(c["identified_databases"]) + _sum(c["identified_registers"])
    expected_screened = identified_db - c["duplicates_removed"] - c["removed_other_reasons"]
    if expected_screened < 0 or c["records_screened"] != expected_screened:
        errors.append(
            f"new database/register arm: records_screened={c['records_screened']} but identified({identified_db}) - duplicates({c['duplicates_removed']}) - other removals({c['removed_other_reasons']}) = {expected_screened}"
        )
    expected_sought = c["records_screened"] - c["records_excluded_title_abstract"]
    if expected_sought < 0 or c["reports_sought"] != expected_sought:
        errors.append(
            f"new database/register arm: reports_sought={c['reports_sought']} but screened({c['records_screened']}) - title/abstract excluded({c['records_excluded_title_abstract']}) = {expected_sought}"
        )
    expected_assessed = c["reports_sought"] - c["reports_not_retrieved"]
    if expected_assessed < 0 or c["reports_assessed"] != expected_assessed:
        errors.append(
            f"new database/register arm: reports_assessed={c['reports_assessed']} but sought({c['reports_sought']}) - not retrieved({c['reports_not_retrieved']}) = {expected_assessed}"
        )
    expected_db_included = c["reports_assessed"] - _sum(c["reports_excluded"])
    if expected_db_included < 0 or c["new_studies_included_databases"] != expected_db_included:
        errors.append(
            f"new database/register arm: included={c['new_studies_included_databases']} but assessed({c['reports_assessed']}) - full-text excluded({_sum(c['reports_excluded'])}) = {expected_db_included}"
        )

    new_other = 0
    if c["variant"] == "updated_databases_registers_other_methods":
        identified_other = _sum(c["identified_other"])
        if c["other_reports_sought"] != identified_other:
            errors.append(
                f"new other-methods arm: reports_sought={c['other_reports_sought']} but identified_other={identified_other}"
            )
        expected_other_assessed = c["other_reports_sought"] - c["other_reports_not_retrieved"]
        if expected_other_assessed < 0 or c["other_reports_assessed"] != expected_other_assessed:
            errors.append(
                f"new other-methods arm: reports_assessed={c['other_reports_assessed']} but sought({c['other_reports_sought']}) - not retrieved({c['other_reports_not_retrieved']}) = {expected_other_assessed}"
            )
        expected_other_included = c["other_reports_assessed"] - _sum(c["other_reports_excluded"])
        if expected_other_included < 0 or c["new_studies_included_other"] != expected_other_included:
            errors.append(
                f"new other-methods arm: included={c['new_studies_included_other']} but assessed({c['other_reports_assessed']}) - excluded({_sum(c['other_reports_excluded'])}) = {expected_other_included}"
            )
        new_other = c["new_studies_included_other"]

    expected_new_studies = c["new_studies_included_databases"] + new_other
    if c["new_studies_included"] != expected_new_studies:
        errors.append(
            f"new evidence merge: new_studies_included={c['new_studies_included']} but database/register({c['new_studies_included_databases']}) + other({new_other}) = {expected_new_studies}"
        )
    expected_total_studies = c["previous_studies_included"] + c["new_studies_included"]
    if c["updated_studies_included"] != expected_total_studies:
        errors.append(
            f"updated review: updated_studies_included={c['updated_studies_included']} but previous({c['previous_studies_included']}) + new({c['new_studies_included']}) = {expected_total_studies}"
        )
    if c["new_reports_included"] < c["new_studies_included"]:
        errors.append(
            f"updated review: new_reports_included={c['new_reports_included']} cannot be fewer than new_studies_included={c['new_studies_included']}"
        )
    expected_total_reports = c["previous_reports_included"] + c["new_reports_included"]
    if c["updated_reports_included"] != expected_total_reports:
        errors.append(
            f"updated review: updated_reports_included={c['updated_reports_included']} but previous({c['previous_reports_included']}) + new({c['new_reports_included']}) = {expected_total_reports}"
        )
    if c["updated_reports_included"] < c["updated_studies_included"]:
        errors.append("updated review: total included reports cannot be fewer than total included studies")
    return errors


def render(c, errors, source):
    lines = ["# PRISMA 2020 updated-review flow", "", f"**Variant:** `{c['variant']}`", ""]
    if errors:
        lines += [f"## ⚠️ {len(errors)} reconciliation issue(s)", ""] + [f"- {e}" for e in errors] + [""]
    else:
        lines += ["✅ Updated-review counts reconcile.", ""]
    lines += ["```mermaid", "flowchart TD"]
    lines.append(f"  PREV[Previous review<br/>Studies n={c['previous_studies_included']}<br/>Reports n={c['previous_reports_included']}]")
    identified = _sum(c["identified_databases"]) + _sum(c["identified_registers"])
    lines.append(f"  IDDB[New records identified<br/>databases/registers n={identified}]")
    lines.append(f"  INDB[New studies included<br/>databases/registers n={c['new_studies_included_databases']}]")
    lines.append("  IDDB --> INDB")
    if c["variant"] == "updated_databases_registers_other_methods":
        lines.append(f"  IDO[New reports identified<br/>other methods n={_sum(c['identified_other'])}]")
        lines.append(f"  INO[New studies included<br/>other methods n={c['new_studies_included_other']}]")
        lines.append("  IDO --> INO")
        lines.append("  INO --> NEW")
    lines.append(f"  NEW[New studies included n={c['new_studies_included']}<br/>New reports included n={c['new_reports_included']}]")
    lines.append("  INDB --> NEW")
    lines.append(f"  TOTAL[Updated review<br/>Studies n={c['updated_studies_included']}<br/>Reports n={c['updated_reports_included']}]")
    lines.append("  PREV --> TOTAL")
    lines.append("  NEW --> TOTAL")
    lines.append("```")
    lines += ["", "---", "", f"*Generated by `prisma_updated_flow.py` from `{source}`. Reconciliation checks arithmetic, not the truth or provenance of the counts.*"]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Reconcile PRISMA 2020 updated-review flow counts.")
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
        sys.stderr.write(f"prisma_updated_flow: cannot read {source} ({exc})\n")
        return 2
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"prisma_updated_flow: invalid JSON ({exc})\n")
        return 2
    try:
        record = parse(raw)
    except CountError as exc:
        sys.stderr.write(f"prisma_updated_flow: {exc}\n")
        return 2
    errors = check(record)
    if args.json:
        json.dump(
            {"check": "prisma_updated_flow", "schema_version": JSON_ENVELOPE_VERSION,
             "issues": len(errors), "units": {"U_prisma_updated": len(errors)},
             "gates": {}, "unattributed": 0, "detail": {"variant": record["variant"]}},
            sys.stdout, indent=2,
        )
        sys.stdout.write("\n")
        return 1 if errors and args.strict else 0
    print(render(record, errors, source))
    return 1 if errors and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
