#!/usr/bin/env python3
"""
search_openalex.py — keyless literature search + snowballing backend for the
acquire-corpus skill. Standard library only (urllib), no API key.

OpenAlex (https://openalex.org, ~250M works, free) is the baseline corpus-
building backend. This script does three jobs:

  search    Query OpenAlex with filters; paginate via cursor; emit records.
  snowball  From seed DOIs, pull backward (referenced_works) and/or forward
            (cited_by) neighbours — citation chaining.
  reconstruct-abstract  (internal) rebuild an abstract from the inverted index.

Each emitted record: openalex_id, doi, title, authors, year, venue, type,
abstract, cited_by_count, referenced_works_count. Output is JSONL (one record
per line) or a markdown table. The acquire-corpus skill turns the JSONL into
corpus files + a PRISMA-S search log.

USAGE
  # Search (records to stdout as JSONL):
  python search_openalex.py search --query "AI tutoring systems K-12" \
      --from 2018-01-01 --to 2026-06-13 --type article --lang en --max 200 \
      --mailto you@example.com

  # Snowball from seed DOIs (both directions):
  python search_openalex.py snowball --seeds 10.1038/s41586-020-2649-2 \
      --direction both --max 100 --mailto you@example.com

  # Markdown table instead of JSONL:
  python search_openalex.py search --query "..." --md

NOTES
  - Always pass --mailto (joins the OpenAlex "polite pool" — faster, kinder).
  - The search string is a natural-language query; OpenAlex ranks by relevance.
    For a documented Boolean strategy, run several searches and record each in
    the PRISMA-S log (the acquire-corpus skill handles that).
  - Date-stamp every run: the search log must record the date each query ran.
"""
from __future__ import annotations
import argparse, json, sys, time, urllib.parse, urllib.request

BASE = "https://api.openalex.org/works"
UA = "acquire-corpus/1.0 (Obsidian agentic-vault; mailto:{})"


def _get(url: str, mailto: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": UA.format(mailto or "anonymous@example.com")})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def reconstruct_abstract(inv) -> str:
    if not inv:
        return ""
    positions = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def to_record(w: dict) -> dict:
    return {
        "openalex_id": w.get("id"),
        "doi": (w.get("doi") or "").replace("https://doi.org/", "") or None,
        "title": w.get("title"),
        "authors": [a.get("author", {}).get("display_name", "") for a in (w.get("authorships") or [])][:8],
        "year": w.get("publication_year"),
        "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
        "type": w.get("type"),
        "is_retracted": bool(w.get("is_retracted")),
        "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
        "cited_by_count": w.get("cited_by_count"),
        "referenced_works": w.get("referenced_works") or [],
    }


def search(args) -> list[dict]:
    filters = []
    if args.from_date:
        filters.append(f"from_publication_date:{args.from_date}")
    if args.to_date:
        filters.append(f"to_publication_date:{args.to_date}")
    if args.type:
        filters.append(f"type:{args.type}")
    if args.lang:
        filters.append(f"language:{args.lang}")
    params = {"search": args.query, "per_page": "200", "cursor": "*"}
    if filters:
        params["filter"] = ",".join(filters)
    if args.mailto:
        params["mailto"] = args.mailto

    out, seen = [], set()
    while len(out) < args.max:
        url = f"{BASE}?{urllib.parse.urlencode(params)}"
        data, err = _get(url, args.mailto)
        if not data:
            sys.stderr.write(f"[search] stopped: {err}\n")
            break
        results = data.get("results", [])
        if not results:
            break
        for w in results:
            rec = to_record(w)
            key = rec["doi"] or rec["openalex_id"]
            if key in seen:
                continue
            seen.add(key)
            out.append(rec)
            if len(out) >= args.max:
                break
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
        params["cursor"] = cursor
        time.sleep(0.25)
    sys.stderr.write(f"[search] '{args.query}' -> {len(out)} records (date={args.run_date})\n")
    return out


def snowball(args) -> list[dict]:
    out, seen = [], set()
    for seed in args.seeds:
        seed = seed.strip().replace("https://doi.org/", "")
        data, err = _get(f"{BASE}/doi:{urllib.parse.quote(seed)}?mailto={urllib.parse.quote(args.mailto or '')}", args.mailto)
        if not data:
            sys.stderr.write(f"[snowball] seed {seed} unresolved: {err}\n")
            continue
        # backward: referenced_works
        if args.direction in ("backward", "both"):
            for ref_id in (data.get("referenced_works") or [])[: args.max]:
                oid = ref_id.rsplit("/", 1)[-1]
                if oid in seen:
                    continue
                seen.add(oid)
                rec_data, _ = _get(f"{BASE}/{oid}?mailto={urllib.parse.quote(args.mailto or '')}", args.mailto)
                if rec_data:
                    out.append({**to_record(rec_data), "snowball": f"backward<-{seed}"})
                if len(out) >= args.max:
                    break
                time.sleep(0.2)
        # forward: cited_by
        if args.direction in ("forward", "both") and len(out) < args.max:
            cb = data.get("cited_by_api_url")
            if cb:
                fdata, _ = _get(f"{cb}&per_page=200&mailto={urllib.parse.quote(args.mailto or '')}", args.mailto)
                for w in (fdata or {}).get("results", [])[: args.max]:
                    rec = to_record(w)
                    key = rec["doi"] or rec["openalex_id"]
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({**rec, "snowball": f"forward->{seed}"})
                    if len(out) >= args.max:
                        break
    sys.stderr.write(f"[snowball] {len(args.seeds)} seed(s), dir={args.direction} -> {len(out)} records\n")
    return out


def emit(records: list[dict], as_md: bool):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if as_md:
        print("| Year | Title | Authors | DOI | Cited by |")
        print("|:---|:---|:---|:---|:---|")
        for r in records:
            au = ", ".join(r["authors"][:2]) + ("…" if len(r["authors"]) > 2 else "")
            print(f"| {r['year'] or ''} | {(r['title'] or '')[:70]} | {au} | {r['doi'] or '—'} | {r['cited_by_count'] or 0} |")
    else:
        for r in records:
            print(json.dumps(r, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description="Keyless OpenAlex search + snowball for acquire-corpus.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("--query", required=True)
    s.add_argument("--from", dest="from_date", default="")
    s.add_argument("--to", dest="to_date", default="")
    s.add_argument("--type", default="", help="OpenAlex work type, e.g. article")
    s.add_argument("--lang", default="", help="ISO language, e.g. en")
    s.add_argument("--max", type=int, default=200)
    s.add_argument("--mailto", default="")
    s.add_argument("--run-date", dest="run_date", default="", help="date this search was run (for the PRISMA-S log)")
    s.add_argument("--md", action="store_true")

    n = sub.add_parser("snowball")
    n.add_argument("--seeds", nargs="+", required=True, help="seed DOIs")
    n.add_argument("--direction", choices=["backward", "forward", "both"], default="both")
    n.add_argument("--max", type=int, default=100)
    n.add_argument("--mailto", default="")
    n.add_argument("--md", action="store_true")

    args = ap.parse_args()
    recs = search(args) if args.cmd == "search" else snowball(args)
    emit(recs, getattr(args, "md", False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
