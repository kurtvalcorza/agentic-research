"""Constitution Principle II, made enforceable: nothing imports a third-party package.

"Keyless, stdlib-only" is the repository's adoption promise — point an agent at
`skills/` and it runs, with no `pip install` in the critical path. Until now that
was a convention nobody checked. This walks every script and test, parses the
imports with `ast`, and asserts each resolves to a standard-library module.

Standard library only (obviously).
"""
from __future__ import annotations

import ast
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Modules the suite itself defines. Everything else must be stdlib.
LOCAL_MODULES = {"_load"}


def python_files():
    """Every script that ships with a skill, plus the test suite."""
    yield from sorted(REPO_ROOT.glob("skills/*/scripts/*.py"))
    yield from sorted((REPO_ROOT / "tests").glob("*.py"))


def _names(node) -> set[str]:
    if isinstance(node, ast.Import):
        return {a.name.split(".")[0] for a in node.names}
    if isinstance(node, ast.ImportFrom):
        if node.level or not node.module:   # relative import — local, not a dependency
            return set()
        return {node.module.split(".")[0]}
    return set()


def _catches_missing_import(handler: ast.ExceptHandler) -> bool:
    """Whether this handler can catch an unavailable optional dependency."""
    if handler.type is None:  # bare except
        return True
    catchable = {"ImportError", "ModuleNotFoundError", "Exception", "BaseException"}

    def names(node) -> set[str]:
        if isinstance(node, ast.Name):
            return {node.id}
        if isinstance(node, ast.Attribute):
            return {node.attr}
        if isinstance(node, ast.Tuple):
            return set().union(*(names(item) for item in node.elts))
        return set()

    return bool(names(handler.type) & catchable)


def collect_imports(path: pathlib.Path) -> tuple[set[str], set[str]]:
    """Return (module_level, lazy_guarded) root module names.

    Constitution Principle II permits an optional capability dependency only when the
    import is LAZY (inside a function) and GUARDED (inside a try whose handler can
    catch a missing import). Everything else must be standard library.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    module_level: set[str] = set()
    lazy_guarded: set[str] = set()

    def visit(node, in_func: bool, in_try_body: bool):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            (lazy_guarded if (in_func and in_try_body) else module_level).update(_names(node))
            return

        in_func = in_func or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))

        if isinstance(node, ast.Try):
            # ONLY the try BODY can be guarded by this try, and only when a handler
            # catches ImportError (or a superclass). A `try: import x` followed by
            # only `except ValueError` still raises when x is unavailable.
            catches_import = any(_catches_missing_import(h) for h in node.handlers)
            for stmt in node.body:
                visit(stmt, in_func, in_try_body or catches_import)
            # Handlers, else and finally are not protected by THIS try. Preserve
            # an enclosing guard, though: an import inside a nested try's handler
            # can still propagate to an outer ImportError handler.
            for stmt in node.handlers + node.orelse + node.finalbody:
                visit(stmt, in_func, in_try_body)
            return

        for child in ast.iter_child_nodes(node):
            visit(child, in_func, in_try_body)

    visit(tree, False, False)
    return module_level, lazy_guarded


def top_level_imports(path: pathlib.Path) -> set[str]:
    m, l = collect_imports(path)
    return m | l


class TestNoThirdPartyImports(unittest.TestCase):
    def test_no_module_level_third_party_import(self):
        """Importing any script must never require a third-party package."""
        stdlib = set(sys.stdlib_module_names)
        offenders = []
        for path in python_files():
            module_level, _ = collect_imports(path)
            for name in sorted(module_level):
                if name in stdlib or name in LOCAL_MODULES:
                    continue
                offenders.append(f"{path.relative_to(REPO_ROOT)} imports {name!r} at module level")
        self.assertEqual(offenders, [], "constitution Principle II forbids a dependency "
                                        "required to import a script:\n" + "\n".join(offenders))

    def test_lazy_third_party_imports_are_guarded_and_disclosed(self):
        """The narrow carve-out: lazy + guarded + disclosed in the README."""
        stdlib = set(sys.stdlib_module_names)
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        for path in python_files():
            _, lazy = collect_imports(path)
            third_party = sorted(n for n in lazy if n not in stdlib and n not in LOCAL_MODULES)
            if not third_party:
                continue
            with self.subTest(script=path.name, deps=third_party):
                text = path.read_text(encoding="utf-8")
                # Condition 2: a failure names what to install.
                self.assertIn("Install", text,
                              f"{path.name} must fail with an actionable message")
                # Condition 4: disclosed in the README script table.
                self.assertIn(path.name, readme,
                              f"{path.name} uses {third_party} and must be listed in the README")

    def test_the_only_optional_dependency_is_pdf_extraction(self):
        """Pins the exception set. A new optional dependency must be a deliberate
        decision recorded here, not something that drifts in."""
        stdlib = set(sys.stdlib_module_names)
        found = {}
        for path in python_files():
            _, lazy = collect_imports(path)
            deps = sorted(n for n in lazy if n not in stdlib and n not in LOCAL_MODULES)
            if deps:
                found[path.name] = deps
        self.assertEqual(found, {"rlm_corpus_loader.py": ["PyPDF2", "pypdf"]})

    def test_the_walk_actually_finds_files(self):
        """A guard against the check silently passing because it scanned nothing."""
        files = list(python_files())
        self.assertGreater(len(files), 10, "expected the scripts and test suite")
        self.assertTrue(any("grade_profile" in f.name for f in files))
        self.assertTrue(any("prisma_flow" in f.name for f in files))

    def test_pytest_is_not_used(self):
        """unittest is required; pytest would reintroduce an install step."""
        for path in python_files():
            with self.subTest(file=path.name):
                self.assertNotIn("pytest", top_level_imports(path))


class TestNoDependencyManifests(unittest.TestCase):
    def test_no_requirements_or_lock_files(self):
        """A manifest implies an install step even if nothing imports from it."""
        forbidden = ["requirements.txt", "Pipfile", "poetry.lock", "environment.yml",
                     "setup.py", "pyproject.toml"]
        found = [f for f in forbidden if (REPO_ROOT / f).exists()]
        self.assertEqual(found, [], f"dependency manifest(s) present: {found}")


class TestCiHasNoInstallStep(unittest.TestCase):
    def test_workflow_runs_without_installing(self):
        wf = REPO_ROOT / ".github" / "workflows" / "tests.yml"
        self.assertTrue(wf.exists(), "CI workflow missing")
        text = wf.read_text(encoding="utf-8")
        self.assertIn("unittest discover", text)
        for forbidden in ("pip install", "poetry install", "pipenv install"):
            with self.subTest(command=forbidden):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
