#!/usr/bin/env python3
"""PRISMA 2020 flow dispatcher with new- and updated-review support.

Backwards compatibility is preserved by keeping the previously shipped new-review
implementation byte-for-byte in ``prisma_flow_new.py`` and re-exporting its API.
Records without an explicit updated-review variant continue through that engine.
Records with ``variant`` equal to ``updated_databases_registers`` or
``updated_databases_registers_other_methods`` are routed to
``prisma_updated_flow.py``.

WHAT THIS CHECKS
  For new reviews: the established ``prisma_flow_new.py`` reconciliation contract.
  For updated reviews: the explicit previous-review + new-search + updated-total
  contract in ``prisma_updated_flow.py``. Updated-review variants are never inferred.

WHAT THIS CANNOT CHECK
  Whether any supplied count is true, whether report-to-study linkage is correct,
  or whether screening/search decisions are substantively valid. The dispatcher
  chooses the declared flow contract; the selected checker validates arithmetic.

EXIT CODES
  0 reconciles (or non-strict)
  1 reconciliation violations under --strict
  2 malformed input — no authoritative artifact is emitted
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load_sibling(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, _HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load PRISMA flow implementation {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Re-export the legacy/new-review implementation so imports/tests and all existing
# callers retain the same functions, constants and behaviour.
_legacy = _load_sibling("prisma_flow_new.py", "_prisma_flow_new")
for _name in dir(_legacy):
    if not _name.startswith("__") and _name != "main":
        globals()[_name] = getattr(_legacy, _name)

_UPDATED_VARIANTS = {
    "updated_databases_registers",
    "updated_databases_registers_other_methods",
}


def _input_text_and_restore() -> tuple[str | None, bool]:
    """Return input text for routing and whether stdin had to be consumed.

    This deliberately does not validate the record. Validation belongs to the
    selected checker so malformed-input diagnostics and exit codes remain owned by
    the underlying contract.
    """
    positional = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    if positional:
        try:
            return Path(positional[0]).read_text(encoding="utf-8"), False
        except (OSError, UnicodeDecodeError):
            return None, False
    text = sys.stdin.read()
    sys.stdin = io.StringIO(text)
    return text, True


def _declared_variant(text: str | None) -> str | None:
    if not text:
        return None
    try:
        raw = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    return raw.get("variant") if isinstance(raw, dict) else None


def main() -> int:
    text, _ = _input_text_and_restore()
    variant = _declared_variant(text)
    if variant in _UPDATED_VARIANTS:
        updated = _load_sibling("prisma_updated_flow.py", "_prisma_updated_flow")
        return updated.main()
    return _legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
