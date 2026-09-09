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

import argparse
import importlib.util
import io
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# Shared with both engines' own parsers so the dispatcher recognises exactly the
# flags either one accepts. argparse.parse_known_args() rather than a manual
# `not arg.startswith("-")` scan: the manual scan misreads the first VALUE of a
# future valued option (e.g. `--foo bar`) as the input file, because "bar" does
# not start with "-" either. No such option exists today, but the hazard is in
# the parsing strategy, not in today's flag set.
_DISPATCH_PARSER = argparse.ArgumentParser(add_help=False)
_DISPATCH_PARSER.add_argument("infile", nargs="?")
_DISPATCH_PARSER.add_argument("--strict", action="store_true")
_DISPATCH_PARSER.add_argument("--json", action="store_true")


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
    args, _unknown = _DISPATCH_PARSER.parse_known_args(sys.argv[1:])
    if args.infile:
        try:
            return Path(args.infile).read_text(encoding="utf-8"), False
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
    # isinstance first: a variant that is itself unhashable (a list or object, from
    # a record shaped as `"variant": [...]`) would raise TypeError on set
    # membership, surfacing as an unhandled traceback instead of the documented
    # exit 2 the branch below reports for any other non-updated variant value.
    if isinstance(variant, str) and variant in _UPDATED_VARIANTS:
        updated = _load_sibling("prisma_updated_flow.py", "_prisma_updated_flow")
        return updated.main()
    if variant is not None:
        # A record naming a `variant` at all is declaring intent to be an
        # updated-review record — `variant` is not a key the new-review contract
        # recognises at all. Falling through to the legacy engine used to report
        # this as an alphabetically-sorted list of every updated-only key the
        # legacy schema does not recognise (e.g. 'new_reports_included',
        # 'new_studies_included', ...), which is a true diagnostic that still
        # points a reader at their data instead of their typo. Naming the
        # unrecognised variant directly is the more useful, closer diagnostic.
        sys.stderr.write(
            f"prisma_flow: record.variant: unrecognised value {variant!r}; expected "
            f"one of {sorted(_UPDATED_VARIANTS)!r} for an updated review, or omit "
            f"variant entirely for a new-review record\n"
        )
        return 2
    return _legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
