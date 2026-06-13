#!/usr/bin/env python3
"""
prisma_flow.py — assemble a PRISMA 2020 flow diagram from REAL run counts and
check that the numbers reconcile. Standard library only.

The vault's pipeline previously emitted a PRISMA "flow diagram" whose
duplicates/screening numbers were not computed from an actual search+dedup
process. This script makes the flow real: it takes the counts produced by
acquire-corpus (identification), dedupe-records (duplicates removed), and
screen-literature (screened / excluded / included), renders the PRISMA 2020
flow as a Mermaid diagram (GitHub/Obsidian-renderable), and FAILS if the
arithmetic does not reconcile end to end.

INPUT — a JSON counts object (file arg or stdin), e.g.:
{
  "identified_databases": {"OpenAlex": 412, "CrossRef": 88},
  "identified_other": {"snowball": 23, "registers": 0},
  "duplicates_removed": 96,
  "removed_other_reasons": 0,
  "records_screened": 427,
  "records_excluded_title_abstract": 351,
  "reports_sought": 76,
  "reports_not_retrieved": 4,
  "reports_assessed": 72,
  "reports_excluded": {"wrong population": 18, "not empirical": 9, "wrong outcome": 7},
  "studies_included": 38
}

USAGE
  python prisma_flow.py counts.json            # mermaid + reconciliation
  echo '{...}' | python prisma_flow.py --strict   # exit 1 if reconciliation fails
"""
from __future__ import annotations
import argparse, json, sys


def _sum(d) -> int:
    return sum(int(v) for v in (d or {}).values())


def reconcile(c: dict) -> list[str]:
    """Return a list of reconciliation errors (empty = clean)."""
    errs = []
    id_db = _sum(c.get("identified_databases"))
    id_ot = _sum(c.get("identified_other"))
    dup = int(c.get("duplicates_removed", 0)) + int(c.get("removed_other_reasons", 0))
    screened = int(c.get("records_screened", 0))
    # identification - duplicates = screened. This pipeline pools other-method records
    # (snowball/registers from acquire-corpus) into the same dedup + title/abstract screening
    # stream, so both arms count toward records_screened — a valid PRISMA 2020 single-column flow.
    identified = id_db + id_ot
    if identified and screened and (identified - dup) != screened:
        errs.append(f"identification: identified {identified} (databases {id_db} + other {id_ot}) - removed {dup} = {identified - dup}, but records_screened = {screened}")
    ex_ta = int(c.get("records_excluded_title_abstract", 0))
    sought = int(c.get("reports_sought", 0))
    if screened and sought and (screened - ex_ta) != sought:
        errs.append(f"screening: screened {screened} - excluded(t/a) {ex_ta} = {screened - ex_ta}, but reports_sought = {sought}")
    not_ret = int(c.get("reports_not_retrieved", 0))
    assessed = int(c.get("reports_assessed", 0))
    if sought and assessed and (sought - not_ret) != assessed:
        errs.append(f"retrieval: sought {sought} - not_retrieved {not_ret} = {sought - not_ret}, but reports_assessed = {assessed}")
    ex_ft = _sum(c.get("reports_excluded"))
    included = int(c.get("studies_included", 0))
    if assessed and included and (assessed - ex_ft) != included:
        errs.append(f"eligibility: assessed {assessed} - excluded(full-text) {ex_ft} = {assessed - ex_ft}, but studies_included = {included}")
    return errs


def mermaid(c: dict) -> str:
    id_db = _sum(c.get("identified_databases"))
    id_ot = _sum(c.get("identified_other"))
    dbs = ", ".join(f"{k} n={v}" for k, v in (c.get("identified_databases") or {}).items())
    oth = ", ".join(f"{k} n={v}" for k, v in (c.get("identified_other") or {}).items())
    dup = int(c.get("duplicates_removed", 0))
    ex_ta = int(c.get("records_excluded_title_abstract", 0))
    not_ret = int(c.get("reports_not_retrieved", 0))
    ex_ft = c.get("reports_excluded") or {}
    ex_ft_lines = "<br/>".join(f"{k}: {v}" for k, v in ex_ft.items()) or "n=0"
    L = [
        "```mermaid",
        "flowchart TB",
        f'  ID["Records identified (databases): n={id_db}<br/>{dbs}"]',
        f'  IDO["Records identified (other methods): n={id_ot}<br/>{oth}"]',
        f'  DUP["Records removed before screening:<br/>duplicates n={dup}, other n={int(c.get("removed_other_reasons",0))}"]',
        f'  SCR["Records screened: n={c.get("records_screened",0)}"]',
        f'  EXTA["Records excluded (title/abstract): n={ex_ta}"]',
        f'  SOU["Reports sought for retrieval: n={c.get("reports_sought",0)}"]',
        f'  NR["Reports not retrieved: n={not_ret}"]',
        f'  ASS["Reports assessed for eligibility: n={c.get("reports_assessed",0)}"]',
        f'  EXFT["Reports excluded:<br/>{ex_ft_lines}"]',
        f'  INC["Studies included: n={c.get("studies_included",0)}"]',
        "  ID --> DUP",
        "  ID --> SCR",
        "  IDO -.snowball/registers.-> DUP",
        "  IDO -.snowball/registers.-> SCR",
        "  SCR --> EXTA",
        "  SCR --> SOU",
        "  SOU --> NR",
        "  SOU --> ASS",
        "  ASS --> EXFT",
        "  ASS --> INC",
        "```",
    ]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble + reconcile a PRISMA 2020 flow diagram from real counts.")
    ap.add_argument("infile", nargs="?")
    ap.add_argument("--strict", action="store_true", help="exit 1 if the counts do not reconcile")
    args = ap.parse_args()
    raw = open(args.infile, encoding="utf-8").read() if args.infile else sys.stdin.read()
    c = json.loads(raw)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    errs = reconcile(c)
    print("# PRISMA 2020 Flow Diagram\n")
    print(mermaid(c))
    print("\n## Reconciliation\n")
    if errs:
        print("⚠️ **Counts do NOT reconcile** — fix before reporting:")
        for e in errs:
            print(f"- {e}")
    else:
        print("✅ Counts reconcile end to end (identification → duplicates → screening → eligibility → included).")
    return 1 if (errs and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
