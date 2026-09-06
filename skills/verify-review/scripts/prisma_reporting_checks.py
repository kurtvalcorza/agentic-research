#!/usr/bin/env python3
"""The PRISMA reporting sub-gate: one envelope `review_units.py` can ingest.

The three strengthened PRISMA reporting checks each emit their own `--json`
envelope, and `review_units.py` runs ONE script per `CHECK_TABLE` entry. This
script is that entry: it runs the checks and reports their counts under a single
`check` identity, so `U_prisma_compliance`, `U_prisma_abstract` and
`U_prisma_updated` are DERIVED from a run rather than asserted by whoever wrote
`units.json`.

WHY THE CLI IS SHAPED THIS WAY. `review_units.py` builds argv itself — a
mandatory positional record, `--strict --json`, and one flag per declared
secondary record — because nothing from `units.json` may reach the command line.
So the 42-row compliance record is the positional argument, and the abstract and
updated-flow records are the two secondary records:

    prisma_reporting_checks.py compliance.json --strict --json \
        [--abstract abstract.json] [--updated-flow updated.json]

An absent secondary record is NOT reported as zero. The unit is simply not in the
envelope, and `review_units.py` — whose `conditional_units` mapping owns this
semantics — lists it under `underived_units` and holds the verdict. That is the
same mechanism `grade_profile.py --rob` uses for `U_rob_trace`, and it is why the
earlier `gates: {"underived": [...]}` field is gone: `gates` carries human-gate
COUNTS, and the ingesting side already models "declared in scope but not derived".

WHAT THIS CHECKS
  Nothing itself. It runs the child checks, validates their envelopes, and
  aggregates. Every count belongs to the check that produced it.

WHAT THIS CANNOT CHECK
  Whether an abstract or checklist row substantively satisfies its PRISMA item,
  whether a recorded human confirmation was really given by a human, or whether the
  review is methodologically sound. A clean aggregate is a reporting sub-gate
  result, not PRISMA certification.

EXIT CODES
  0 clean, or issues found without --strict
  1 reporting issues or pending human confirmations under --strict
  2 malformed invocation, or a child check that could not produce a valid envelope
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

CHECK_NAME = "prisma_reporting_checks"
JSON_ENVELOPE_VERSION = "1.0"
HUMAN_GATE = "H_prisma_evidence"
HERE = Path(__file__).resolve().parent
PRISMA_SCRIPTS = (HERE.parent.parent / "prisma-flow" / "scripts").resolve()

# Child script -> the unit it owns. The sub-gate never invents a unit name: it
# reports exactly what the child reported, under the key the child used.
CHILDREN = {
    "compliance": ("prisma_compliance.py", "U_prisma_compliance"),
    "abstract": ("prisma_abstract_checklist.py", "U_prisma_abstract"),
    "updated_flow": ("prisma_updated_flow.py", "U_prisma_updated"),
}
ENVELOPE_REQUIRED = {"check", "schema_version", "issues", "units", "gates", "unattributed"}


class InputError(ValueError):
    """Invocation or child-output error (exit 2)."""


def run_check(script: str, record: str) -> dict:
    """Run one child check and return its validated envelope.

    A child that exits 2 (malformed record) or crashes is an error here, never a
    count of zero: an unreadable record is not a clean one.
    """
    path = PRISMA_SCRIPTS / script
    if not path.is_file():
        raise InputError(
            f"{script}: the check is not available at {str(path)!r}. A skill "
            f"directory copied out on its own has no sibling skills")
    proc = subprocess.run(
        [sys.executable, str(path), record, "--strict", "--json"],
        text=True, capture_output=True, check=False,
    )
    if proc.returncode == 2:
        raise InputError(f"{script}: malformed/unreadable child input: {proc.stderr.strip()}")
    if proc.returncode not in (0, 1):
        raise InputError(f"{script}: unexpected child exit code {proc.returncode}")
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise InputError(f"{script}: child did not emit valid JSON ({exc})") from exc
    if not isinstance(envelope, dict):
        raise InputError(f"{script}: child envelope must be an object")
    missing = sorted(ENVELOPE_REQUIRED - set(envelope))
    if missing:
        raise InputError(f"{script}: child envelope missing {', '.join(missing)}")
    if envelope["schema_version"] != JSON_ENVELOPE_VERSION:
        raise InputError(
            f"{script}: unsupported child envelope version {envelope['schema_version']!r}")
    if not isinstance(envelope["units"], dict) or not isinstance(envelope["gates"], dict):
        raise InputError(f"{script}: child 'units' and 'gates' must be objects")
    envelope["exit_code"] = proc.returncode
    return envelope


def _count(envelope: dict, key: str, where: str, *, required: bool) -> int:
    """Read one non-negative integer count out of a child envelope.

    `required` separates the two cases. A child MUST report the unit it owns —
    absent is not zero, and a child that quietly stopped reporting its unit would
    otherwise aggregate as clean. The GATE is optional, because a child with no
    confirmations to count (`prisma_updated_flow`) legitimately reports `gates: {}`.
    """
    if required and key not in envelope[where]:
        raise InputError(
            f"{envelope['check']}: child envelope omits {where}.{key} — absent is not "
            f"zero, and a check that did not say is not a check that reported none")
    value = envelope[where].get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InputError(f"{envelope['check']}: {where}.{key} is not a non-negative integer")
    return value


def aggregate(compliance: dict, abstract: dict | None = None,
              updated: dict | None = None) -> dict:
    """Combine the child envelopes into the one this sub-gate reports.

    `compliance` is mandatory — it is the positional record — and `abstract` and
    `updated` are present exactly when their secondary record was supplied. A unit
    whose child did not run is ABSENT from `units`, never zero.
    """
    supplied = {"compliance": compliance, "abstract": abstract, "updated_flow": updated}
    units: dict[str, int] = {}
    issues = 0
    checks: dict[str, str] = {}
    gate = 0
    for name, envelope in supplied.items():
        if envelope is None:
            continue
        script, unit = CHILDREN[name]
        expected = script.removesuffix(".py")
        if envelope.get("check") != expected:
            raise InputError(
                f"{script}: the child identifies itself as {envelope.get('check')!r}, "
                f"expected {expected!r}")
        checks[name] = envelope["check"]
        reported = envelope["issues"]
        if isinstance(reported, bool) or not isinstance(reported, int) or reported < 0:
            raise InputError(f"{script}: child 'issues' is not a non-negative integer")
        issues += reported
        units[unit] = _count(envelope, unit, "units", required=True)
        gate += _count(envelope, HUMAN_GATE, "gates", required=False)

    # An addressability-mode abstract record asserts no compliance and owes no
    # confirmation, so folding it in here would report a satisfied human gate over a
    # record that never claimed one. Refused rather than silently down-weighted.
    if abstract is not None:
        level = (abstract.get("detail") or {}).get("verification")
        if level != "compliance":
            raise InputError(
                f"prisma_abstract_checklist.py: the reporting sub-gate requires a "
                f"'compliance' abstract record, got {level!r}. An addressability "
                f"record cannot supply the human confirmation this gate counts")

    return {
        "check": CHECK_NAME,
        "schema_version": JSON_ENVELOPE_VERSION,
        "issues": issues,
        "units": units,
        # One gate, summed over the children that count confirmations. Never
        # auto-zeroed by the loop: a signature is not agent-reducible work.
        "gates": {HUMAN_GATE: gate},
        "unattributed": 0,
        "detail": {
            "checks": checks,
            "underived": sorted(unit for name, (_s, unit) in CHILDREN.items()
                                if supplied[name] is None),
            "not_certification": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the strengthened PRISMA reporting checks and report one envelope.")
    parser.add_argument("infile", nargs="?",
                        help="the 42-row evidence-bearing PRISMA compliance record")
    parser.add_argument("--abstract", help="PRISMA 2020 for Abstracts record (compliance mode)")
    parser.add_argument("--updated-flow", dest="updated_flow",
                        help="updated-review flow record")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 when a reporting issue or pending confirmation remains")
    parser.add_argument("--json", action="store_true", help="machine-readable counts envelope")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if not args.infile:
        sys.stderr.write(
            "prisma_reporting_checks: the compliance record is required as the "
            "positional argument\n")
        return 2
    try:
        compliance = run_check("prisma_compliance.py", args.infile)
        abstract = run_check("prisma_abstract_checklist.py", args.abstract) if args.abstract else None
        updated = run_check("prisma_updated_flow.py", args.updated_flow) if args.updated_flow else None
        envelope = aggregate(compliance, abstract, updated)
    except InputError as exc:
        sys.stderr.write(f"prisma_reporting_checks: {exc}\n")
        return 2

    pending = envelope["gates"][HUMAN_GATE]
    failed = bool(envelope["issues"] or pending)
    if args.json:
        json.dump(envelope, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print("# verify-review — PRISMA reporting sub-gate")
        print()
        print(f"Issues: {envelope['issues']}")
        for key, value in sorted(envelope["units"].items()):
            print(f"- {key}: {value}")
        print(f"- {HUMAN_GATE}: {pending} (human confirmations still owed)")
        if envelope["detail"]["underived"]:
            print("- UNDERIVED (no record supplied): "
                  + ", ".join(envelope["detail"]["underived"]))
        print()
        print("This is pipeline reporting verification, not PRISMA certification or "
              "methodological-quality assessment.")
    return 1 if failed and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
