#!/usr/bin/env python3
"""
dedupe_records.py — record-level deduplication for the dedupe-records skill.
Standard library only (difflib) — no dependencies.

Cross-database searching and snowballing produce heavy duplication (the same
paper from OpenAlex + CrossRef + a snowball edge, or a preprint + its published
version). Naive "same DOI" matching misses near-duplicates. This script applies
a stepwise method (after Bramer et al.):

  1. Exact DOI match (normalized).
  2. Fuzzy title match: normalized-title similarity >= threshold AND year within
     +/-1 AND a shared first-author surname (guards against same-title-different-
     paper collisions).
  3. Preprint <-> published reconciliation: when a duplicate group contains both
     a preprint (arXiv/biorxiv/ssrn/preprint DOI or type) and a published record,
     keep the published one as canonical.

Input:  JSONL records (one per line) as emitted by search_openalex.py — must have
        at least: doi, title, year, authors (list). Extra fields are preserved.
Output: deduped JSONL on stdout (canonical record per group, with a
        `duplicate_of` list of the dropped ids) + a summary report on stderr,
        OR a markdown report with --report.

The "records identified", "duplicates removed", and "records after dedup" counts
printed here are the inputs to the PRISMA 2020 flow diagram.

USAGE
  cat corpus.jsonl | python dedupe_records.py > deduped.jsonl
  python dedupe_records.py corpus.jsonl --threshold 0.92 --report
"""
from __future__ import annotations
import argparse, json, re, sys
from difflib import SequenceMatcher

PREPRINT_HINTS = ("arxiv", "biorxiv", "medrxiv", "ssrn", "preprint", "10.48550", "10.1101")


def norm_doi(doi) -> str:
    if not doi:
        return ""
    return str(doi).lower().replace("https://doi.org/", "").replace("doi:", "").strip()


def norm_title(t) -> str:
    if not t:
        return ""
    t = str(t).lower()
    t = re.sub(r"<[^>]+>", " ", t)          # strip any markup
    t = re.sub(r"[^a-z0-9 ]+", " ", t)      # punctuation -> space
    return re.sub(r"\s+", " ", t).strip()


def first_surname(authors) -> str:
    if not authors:
        return ""
    a = authors[0] if isinstance(authors, list) else str(authors)
    return (a.strip().split()[-1] if a.strip() else "").lower()


def _year(v):
    """Parse a year to int (first 4 chars), or None if unparseable — never raises."""
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


def is_preprint(rec) -> bool:
    doi = norm_doi(rec.get("doi"))
    typ = (rec.get("type") or "").lower()
    venue = (rec.get("venue") or "").lower()
    return any(h in doi for h in PREPRINT_HINTS) or "preprint" in typ or any(h in venue for h in PREPRINT_HINTS)


def rec_id(rec) -> str:
    return norm_doi(rec.get("doi")) or rec.get("openalex_id") or norm_title(rec.get("title"))


def dedupe(records: list[dict], threshold: float) -> tuple[list[dict], dict]:
    groups: list[list[dict]] = []
    doi_index: dict[str, int] = {}      # normalized doi -> group index

    for rec in records:
        d = norm_doi(rec.get("doi"))
        placed = False
        # 1. exact DOI
        if d and d in doi_index:
            groups[doi_index[d]].append(rec)
            placed = True
        if not placed:
            nt, yr, sn = norm_title(rec.get("title")), rec.get("year"), first_surname(rec.get("authors"))
            # 2. fuzzy title + year + author guard (scan existing groups' canonical record)
            for gi, g in enumerate(groups):
                c = g[0]
                cnt, cyr, csn = norm_title(c.get("title")), c.get("year"), first_surname(c.get("authors"))
                if not nt or not cnt:
                    continue
                yi, cyi = _year(yr), _year(cyr)
                year_ok = (yi is None or cyi is None) or abs(yi - cyi) <= 1
                author_ok = (not sn or not csn) or sn == csn
                if year_ok and author_ok and SequenceMatcher(None, nt, cnt).ratio() >= threshold:
                    g.append(rec)
                    placed = True
                    break
        if not placed:
            groups.append([rec])
        # index the doi to the (new or matched) group
        if d:
            gi = next(i for i, g in enumerate(groups) if rec in g)
            doi_index[d] = gi

    canon, dup_removed = [], 0
    for g in groups:
        if len(g) == 1:
            canon.append(g[0])
            continue
        # 3. preprint<->published reconciliation: prefer a published record
        published = [r for r in g if not is_preprint(r)]
        winner = (published or g)
        # among candidates, prefer the one with a DOI, then most-cited
        winner = sorted(winner, key=lambda r: (bool(norm_doi(r.get("doi"))), r.get("cited_by_count") or 0), reverse=True)[0]
        dup_ids = [rec_id(r) for r in g if r is not winner]   # against the ORIGINAL winner, before copy
        winner = dict(winner)
        winner["duplicate_of"] = dup_ids
        canon.append(winner)
        dup_removed += len(g) - 1

    report = {"identified": len(records), "duplicates_removed": dup_removed,
              "after_dedup": len(canon), "groups_merged": sum(1 for g in groups if len(g) > 1)}
    return canon, report


def main() -> int:
    ap = argparse.ArgumentParser(description="Record-level dedup for a merged literature corpus.")
    ap.add_argument("infile", nargs="?", help="JSONL input (default: stdin)")
    ap.add_argument("--threshold", type=float, default=0.92, help="fuzzy title-similarity cutoff (0-1)")
    ap.add_argument("--report", action="store_true", help="emit a markdown report instead of JSONL")
    args = ap.parse_args()

    src = open(args.infile, encoding="utf-8") if args.infile else sys.stdin
    records = []
    for i, ln in enumerate(src, 1):
        if not ln.strip():
            continue
        try:
            records.append(json.loads(ln))
        except json.JSONDecodeError as e:
            sys.stderr.write(f"[dedupe] skipping malformed line {i}: {e}\n")
    canon, rep = dedupe(records, args.threshold)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    if args.report:
        print("# Deduplication report\n")
        print(f"- Records identified (pre-dedup): **{rep['identified']}**")
        print(f"- Duplicate records removed: **{rep['duplicates_removed']}** ({rep['groups_merged']} groups merged)")
        print(f"- Records after deduplication: **{rep['after_dedup']}**\n")
        print("> These three numbers feed the PRISMA 2020 flow diagram (identification → records after duplicates removed).")
    else:
        for r in canon:
            print(json.dumps(r, ensure_ascii=False))
    sys.stderr.write(f"[dedupe] {rep['identified']} -> {rep['after_dedup']} ({rep['duplicates_removed']} removed)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
