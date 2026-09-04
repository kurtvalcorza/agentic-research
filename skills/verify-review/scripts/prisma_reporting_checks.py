#!/usr/bin/env python3
"""Aggregate strengthened PRISMA reporting checks for ``verify-review``.

This companion is intentionally additive to ``review_units.py`` so the established
verification loop remains backwards compatible. A standards-aware systematic-review
run can invoke this script as the PRISMA reporting sub-gate. Missing stronger
artifacts are reported explicitly as UNDERIVED rather than silently treated as zero.

WHAT THIS CHECKS
  Runs the 12-item abstract checker and the 42-row evidence-bearing compliance
  checker, and optionally the updated-review flow checker, consuming their JSON
  envelopes rather than re-deriving their units.

WHAT THIS CANNOT CHECK
  The substantive correctness of human PRISMA judgments, whether a review is of
  high methodological quality, or any unit owned by the general ``review_units.py``
  verification loop. A clean aggregate is a reporting-subgate result, not external
  PRISMA certification.

EXIT CODES
  0 all supplied required reporting checks are clean
  1 one or more reporting checks fail or a required stronger artifact is underived
  2 malformed invocation / child check could not produce a valid envelope
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

JSON_ENVELOPE_VERSION = "1.0"
HERE = Path(__file__).resolve().parent
PRISMA_SCRIPTS = (HERE.parent.parent / "prisma-flow" / "scripts").resolve()


class InputError(ValueError):
    """Invocation/child-output error (exit 2)."""


def run_check(script: str, record: str) -> dict:
    path = PRISMA_SCRIPTS / script
    proc = subprocess.run(
        [sys.executable, str(path), record, "--strict", "--json"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode == 2:
        raise InputError(f"{script}: malformed/unreadable child input: {proc.stderr.strip()}")
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise InputError(f"{script}: child did not emit valid JSON ({exc})") from exc
    if not isinstance(envelope, dict):
        raise InputError(f"{script}: child envelope must be an object")
    required = {"check", "schema_version", "issues", "units", "gates", "unattributed"}
    missing = sorted(required - set(envelope))
    if missing:
        raise InputError(f"{script}: child envelope missing {', '.join(missing)}")
    if envelope["schema_version"] != JSON_ENVELOPE_VERSION:
        raise InputError(f"{script}: unsupported child envelope version {envelope['schema_version']!r}")
    if proc.returncode not in (0, 1):
        raise InputError(f"{script}: unexpected child exit code {proc.returncode}")
    envelope["exit_code"] = proc.returncode
    return envelope


def aggregate(abstract: dict, compliance: dict, updated: dict | None, *, require_updated: bool) -> dict:
    units = {}
    issues = 0
    checks = {}
    for name, envelope in (("abstract", abstract), ("compliance", compliance)):
        checks[name] = envelope["check"]
        issues += int(envelope["issues"])
        for key, value in envelope["units"].items():
            units[key] = int(value)
    underived = []
    if updated is not None:
        checks["updated_flow"] = updated["check"]
        issues += int(updated["issues"])
        for key, value in updated["units"].items():
            units[key] = int(value)
    elif require_updated:
        underived.append("U_prisma_updated")
    return {
        "check": "prisma_reporting_checks",
        "schema_version": JSON_ENVELOPE_VERSION,
        "issues": issues + len(underived),
        "units": units,
        "gates": {"underived": underived},
        "unattributed": 0,
        "detail": {"checks": checks, "not_certification": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate strengthened PRISMA reporting checks for verify-review.")
    parser.add_argument("--abstract", required=True, help="PRISMA 2020 for Abstracts record")
    parser.add_argument("--compliance", required=True, help="42-row evidence-bearing PRISMA compliance record")
    parser.add_argument("--updated-flow", help="updated-review flow record")
    parser.add_argument("--require-updated-flow", action="store_true",
                        help="report U_prisma_updated as underived when no updated-flow record is supplied")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    try:
        abstract = run_check("prisma_abstract_checklist.py", args.abstract)
        compliance = run_check("prisma_compliance.py", args.compliance)
        updated = run_check("prisma_updated_flow.py", args.updated_flow) if args.updated_flow else None
        envelope = aggregate(abstract, compliance, updated, require_updated=args.require_updated_flow)
    except InputError as exc:
        sys.stderr.write(f"prisma_reporting_checks: {exc}\n")
        return 2

    failed = bool(envelope["issues"] or envelope["gates"]["underived"])
    if args.json:
        json.dump(envelope, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print("# verify-review — PRISMA reporting sub-gate")
        print()
        print(f"Issues: {envelope['issues']}")
        for key, value in sorted(envelope["units"].items()):
            print(f"- {key}: {value}")
        if envelope["gates"]["underived"]:
            print("- UNDERIVED: " + ", ".join(envelope["gates"]["underived"]))
        print()
        print("This is pipeline reporting verification, not PRISMA certification or methodological-quality assessment.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
