"""Load a skill script that lives outside any importable package.

Skill directories deliberately contain no ``__init__.py``, and several have names
that are not legal Python identifiers (``appraise-risk-of-bias``), so scripts are
loaded by file path rather than imported. This keeps skill directories copyable in
isolation — constitution Principle III — at the cost of one small helper here.

This helper is the ONLY shared test code in the repository, and it never ships with
a skill.

Standard library only.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_cache: dict[str, object] = {}


def load(rel_path: str):
    """Load and return the module at ``rel_path``, relative to the repo root.

    Modules are cached so repeated loads in one test session do not re-execute
    module-level code.
    """
    if rel_path in _cache:
        return _cache[rel_path]

    path = REPO_ROOT / rel_path
    if not path.is_file():
        raise FileNotFoundError(f"no script at {path}")

    # Prefix the module name so a script never shadows a real stdlib module.
    name = "_skillscript_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot build a module spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _cache[rel_path] = module
    return module


def fixture(name: str) -> Path:
    """Absolute path to a fixture in ``tests/fixtures/``."""
    return Path(__file__).resolve().parent / "fixtures" / name
