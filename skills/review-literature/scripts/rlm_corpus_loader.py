#!/usr/bin/env python
"""RLM corpus loader template.

Builds a JSONL corpus from PDF/MD files for REPL-based screening/extraction.
The output is meant to be loaded into a Python REPL as `corpus`.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception as exc:
            raise RuntimeError("Install pypdf or PyPDF2 to read PDFs") from exc

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts)


def _read_md_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def _extract_abstract(text: str) -> str:
    # Simple heuristic: capture after an Abstract heading until next blank line
    match = re.search(r"(?i)\babstract\b[:\s]*\n(.{0,2000}?)(\n\s*\n|$)", text)
    if match:
        return match.group(1).strip()
    return ""


def build_corpus(paths: list[Path]) -> list[dict[str, str]]:
    corpus = []
    for idx, path in enumerate(paths, start=1):
        if path.suffix.lower() == ".pdf":
            text = _read_pdf_text(path)
        else:
            text = _read_md_text(path)
        title = _extract_title(text, path.stem)
        abstract = _extract_abstract(text)
        corpus.append(
            {
                "id": f"P{idx:03d}",
                "path": str(path),
                "title": title,
                "abstract": abstract,
                "text": text,
            }
        )
    return corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Build JSONL corpus for RLM workflows")
    parser.add_argument("corpus_dir", type=Path, help="Directory with PDF/MD files")
    parser.add_argument("--out", type=Path, default=Path("corpus.jsonl"))
    args = parser.parse_args()

    files = sorted(
        [p for p in args.corpus_dir.rglob("*") if p.suffix.lower() in {".pdf", ".md"}]
    )
    corpus = build_corpus(files)

    with args.out.open("w", encoding="utf-8") as f:
        for item in corpus:
            f.write(json.dumps(item, ensure_ascii=False))
            f.write("\n")

    print("Wrote", args.out)
    print("REPL load snippet:")
    print("import json")
    print("corpus = [json.loads(line) for line in open(r'%s', 'r', encoding='utf-8')]" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
