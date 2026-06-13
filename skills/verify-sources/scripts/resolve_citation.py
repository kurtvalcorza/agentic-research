#!/usr/bin/env python3
"""
resolve_citation.py — external citation verification backend for the verify-sources skill.

Resolves DOIs (or title+author+year) against free bibliographic APIs and reports
existence + retraction status. Standard-library only (urllib) — no pip install,
no API key. OpenAlex is primary (clean `is_retracted` boolean); CrossRef is the
fallback and the title->DOI reverse-lookup source.

This is the no-scite-MCP backend. When the scite MCP is available, prefer it
(it adds Smart-Citation fidelity signals); this script covers existence +
integrity for any user/agent.

USAGE
  # Resolve DOIs (args or stdin, one per line):
  python resolve_citation.py 10.1038/s41586-020-2649-2 10.1016/S0140-6736(97)11096-0
  echo "10.1038/s41586-020-2649-2" | python resolve_citation.py

  # Reverse-lookup by title (quote it):
  python resolve_citation.py --title "Array programming with NumPy" --author Harris --year 2020

  # JSON output (default is a markdown table):
  python resolve_citation.py --json 10.1038/s41586-020-2649-2

  # Be a polite API citizen (recommended): set a contact email
  python resolve_citation.py --mailto you@example.com 10.xxxx/yyyy

EXIT CODE
  0 if all resolved and none retracted; 1 if any UNVERIFIED or RETRACTED
  (so it can act as a shell-level gate).
"""
from __future__ import annotations
import argparse, json, sys, time, urllib.parse, urllib.request

UA_BASE = "verify-sources/1.0 (Obsidian agentic-vault; mailto:{})"


def _get(url: str, mailto: str, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": UA_BASE.format(mailto or "anonymous@example.com")})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 - report any failure as a resolution miss
        return None, str(e)


def _openalex_authors(work) -> list[str]:
    return [a.get("author", {}).get("display_name", "") for a in (work.get("authorships") or [])][:5]


def resolve_doi(doi: str, mailto: str) -> dict:
    doi = doi.strip().lstrip("https://doi.org/").lstrip("doi:").strip()
    out = {"doi": doi, "status": "UNVERIFIED", "resolved_title": None, "authors": [],
           "year": None, "journal": None, "is_retracted": False, "retraction_source": None, "backend": None, "note": ""}

    # --- Primary: OpenAlex (free, has is_retracted) ---
    data, err = _get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}?mailto={urllib.parse.quote(mailto or '')}", mailto)
    if data:
        out["backend"] = "openalex"
        out["resolved_title"] = data.get("title")
        out["authors"] = _openalex_authors(data)
        out["year"] = data.get("publication_year")
        loc = (data.get("primary_location") or {}).get("source") or {}
        out["journal"] = loc.get("display_name")
        out["is_retracted"] = bool(data.get("is_retracted"))
        out["status"] = "RETRACTED" if out["is_retracted"] else "VERIFIED"
        if out["is_retracted"]:
            out["retraction_source"] = "openalex:is_retracted"
        return out

    # --- Fallback: CrossRef ---
    data, err2 = _get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto={urllib.parse.quote(mailto or '')}", mailto)
    if data and data.get("message"):
        m = data["message"]
        out["backend"] = "crossref"
        out["resolved_title"] = (m.get("title") or [None])[0]
        out["authors"] = [f"{a.get('given','')} {a.get('family','')}".strip() for a in (m.get("author") or [])][:5]
        dp = (((m.get("published") or m.get("published-print") or m.get("published-online") or {}).get("date-parts")) or [[None]])
        out["year"] = dp[0][0] if dp and dp[0] else None
        out["journal"] = (m.get("container-title") or [None])[0]
        updates = m.get("update-to") or []
        retr = [u for u in updates if (u.get("type") or "").lower() == "retraction"]
        out["is_retracted"] = bool(retr)
        out["status"] = "RETRACTED" if retr else "VERIFIED"
        if retr:
            out["retraction_source"] = f"crossref:update-to:{retr[0].get('DOI','')}"
        return out

    out["note"] = f"unresolved (openalex: {err}; crossref: {err2})"
    return out


def reverse_lookup(title: str, author: str, year, mailto: str) -> dict:
    q = urllib.parse.quote(title)
    data, err = _get(f"https://api.openalex.org/works?search={q}&per_page=5&mailto={urllib.parse.quote(mailto or '')}", mailto)
    if data and data.get("results"):
        for w in data["results"]:
            wy = w.get("publication_year")
            wa = " ".join(_openalex_authors(w)).lower()
            if (not year or (wy and abs(int(wy) - int(year)) <= 1)) and (not author or author.lower() in wa):
                doi = (w.get("doi") or "").replace("https://doi.org/", "")
                if doi:
                    res = resolve_doi(doi, mailto)
                    res["note"] = "matched via title reverse-lookup"
                    return res
        return {"doi": None, "status": "UNVERIFIED", "resolved_title": title, "authors": [], "year": year,
                "journal": None, "is_retracted": False, "retraction_source": None, "backend": "openalex",
                "note": "title found candidates but none matched author/year — review manually"}
    return {"doi": None, "status": "UNVERIFIED", "resolved_title": title, "authors": [], "year": year,
            "journal": None, "is_retracted": False, "retraction_source": None, "backend": "openalex",
            "note": f"no record for title ({err}) — likely fabricated, investigate"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve citations against OpenAlex/CrossRef and report retraction status.")
    ap.add_argument("dois", nargs="*", help="DOIs to resolve (or pipe one per line on stdin)")
    ap.add_argument("--title", help="reverse-lookup by title")
    ap.add_argument("--author", default="", help="author surname to disambiguate a title lookup")
    ap.add_argument("--year", default="", help="publication year to disambiguate a title lookup")
    ap.add_argument("--mailto", default="", help="contact email for the API polite pool (recommended)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a markdown table")
    args = ap.parse_args()

    # Resolved titles/authors and the status icons are non-ASCII; force UTF-8 so
    # this runs on Windows consoles (cp1252) and anywhere else.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 - older Pythons / odd streams
        pass

    results = []
    if args.title:
        results.append(reverse_lookup(args.title, args.author, args.year or None, args.mailto))
    dois = list(args.dois)
    if not dois and not sys.stdin.isatty():
        dois += [ln.strip() for ln in sys.stdin if ln.strip()]
    for i, doi in enumerate(dois):
        if i:
            time.sleep(0.3)  # be polite
        results.append(resolve_doi(doi, args.mailto))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("| Status | DOI | Resolved title | Authors | Year | Note |")
        print("|:---|:---|:---|:---|:---|:---|")
        for r in results:
            icon = {"VERIFIED": "✅", "RETRACTED": "⛔", "UNVERIFIED": "⚠️"}.get(r["status"], "?")
            auths = ", ".join(r["authors"][:2]) + ("…" if len(r["authors"]) > 2 else "")
            title = (r["resolved_title"] or "")[:60]
            print(f"| {icon} {r['status']} | {r['doi'] or '—'} | {title} | {auths} | {r['year'] or ''} | {r['retraction_source'] or r['note']} |")

    bad = [r for r in results if r["status"] in ("UNVERIFIED", "RETRACTED")]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
