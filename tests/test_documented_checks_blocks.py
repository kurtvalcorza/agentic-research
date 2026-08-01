"""Every `checks` block printed in the documentation must be one the backend accepts,
AND one that is right for the review type the surrounding example is written for.

`tests/test_contract_examples.py` exists because a documented example that nothing
executes drifts the moment the schema changes. This is the same guard for a surface
that file does not cover: the `checks` blocks in the verify-review skill docs.

It was needed within one review round of the feature shipping. Round 2 added the rule
that `grade_profile.rob_record` requires a `rob_appraisal` entry on the same record —
and the canonical `units.json` example in `loop-protocol.md`, which predated the rule,
was left naming `rob_record` alone. A caller copying it got exit 2 from `--dry-run`,
before anything ran. Nothing failed, because nothing executed the example.

TWO AXES, AND THE SECOND ONE COST A ROUND OF ITS OWN. Validating shape is not enough.
The orchestrator guide's example is parameterised by review type, and its block
declared all four checks unconditionally — perfectly well-formed, and wrong for three
of the five review types, because `contained_record()` rejects a DECLARED record that
does not exist and a scoping review has no certainty profile. The first version of
this file widened its COVERAGE (two docs to four) while leaving its AXIS at shape
only, so it could not have caught that no matter how many files it read. Both axes are
now asserted: `TestDocumentedChecksBlocksAreAccepted` for shape,
`TestTheScopeDerivedExampleMatchesItsScope` for scope.

Validation only, deliberately: these blocks name artifact paths that do not exist in
this repository (`artifacts/counts.json`), so the records cannot be RUN here. What can
be checked is everything `_validated_checks` decides before touching the filesystem —
unknown check names, unknown entry keys, and the cross-entry rules — which is exactly
the class of error that bit.

Standard library only.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

ru = load("skills/verify-review/scripts/review_units.py")
REPO = pathlib.Path(__file__).resolve().parent.parent

# Docs that print a LITERAL `checks` block a reader is meant to copy. EVERY entry must
# contribute at least one block — see test_every_listed_doc_is_actually_covered.
DOCS = [
    "skills/verify-review/references/loop-protocol.md",
    "skills/verify-review/SKILL.md",
    "specs/001-standards-enforcement-parity/contracts/review-units.md",
]

# The one doc that does NOT print a literal block, because it must not: its example is
# parameterised by review type, so it DERIVES the block from the frozen scope. Covered
# by TestTheScopeDerivedExampleMatchesItsScope instead, which executes the documented
# function rather than reading a constant.
SCOPE_DERIVED_DOC = "skills/orchestrate-research/references/detailed-guide.md"

# The authority on which units each review type carries. Parsed rather than restated:
# a copy here would be one more thing to drift, and drift between the table and the
# example is the whole defect this guards.
SCOPE_TABLE_DOC = "skills/verify-review/SKILL.md"

IN, OUT = "✅", "⬜"     # ✅ in scope, ⬜ absent (not "zero to achieve")


def fenced_blocks(text):
    """Yield (language, body) for each fenced block, tracking state line by line.

    A regex could not do this correctly. The first version's pattern matched a
    CLOSING fence as an opening one, so it consumed the prose between one block's
    close and the next block's open — and `review-units.md`'s bare-fenced fragment
    fell into that gap and was never checked at all. The guard listed three files
    and validated two.
    """
    lang, buf, inside = None, [], False
    for line in text.splitlines():
        if line.startswith("```"):
            if inside:
                yield lang, "\n".join(buf)
                lang, buf, inside = None, [], False
            else:
                lang, buf, inside = line[3:].strip(), [], True
            continue
        if inside:
            buf.append(line)


def _checks_from(body):
    """The `checks` mapping in a block, however it is written there."""
    if '"checks"' in body:
        for candidate in (body, "{" + body.rstrip().rstrip(",") + "}"):
            try:
                got = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(got, dict) and isinstance(got.get("checks"), dict):
                return got["checks"]
    # A Python kwarg: `checks={ ... },` — take the balanced brace span, then make
    # it JSON. The literal is JSON-shaped but carries two things JSON rejects and
    # a reader's eye skips: trailing `# …` comments, and a trailing comma before
    # the closing brace. Both are stripped rather than tolerated, so a block that
    # is genuinely malformed still returns None and fails the coverage test loudly.
    start = body.find("checks={")
    if start == -1:
        return None
    span, depth = body[start + len("checks="):], 0
    for i, ch in enumerate(span):
        depth += (ch == "{") - (ch == "}")
        if depth == 0:
            literal = "\n".join(re.sub(r"\s+#.*$", "", ln) for ln in span[:i + 1].splitlines())
            literal = re.sub(r",(\s*[}\]])", r"\1", literal)
            try:
                return json.loads(literal)
            except json.JSONDecodeError:
                return None
    return None


def checks_blocks():
    """Yield (doc, index, checks-dict) for every documented LITERAL `checks` block."""
    for doc in DOCS:
        text = (REPO / doc).read_text(encoding="utf-8")
        for i, (_lang, body) in enumerate(fenced_blocks(text)):
            checks = _checks_from(body)
            if checks:
                yield doc, i, checks


def scope_table():
    """{review type: (units marked in scope, units marked ABSENT)} from SKILL.md.

    Only the two explicit markers are read. A cell carrying neither — narrative's
    `U_grade` is "only if grading was performed" — is genuinely conditional, and a
    guard that forced it either way would be asserting something the table does not
    say.
    """
    text = (REPO / SCOPE_TABLE_DOC).read_text(encoding="utf-8").splitlines()
    # Matched on the review types themselves, not on `| Unit |`: SKILL.md carries a
    # SECOND table starting `| Unit | Weight | From | Counts |`, and anchoring on the
    # first column found that one. Every scope assertion below then iterated three
    # bogus columns holding empty sets and passed — the same vacuous-green this file
    # was written to prevent, one level up. `test_the_documented_function_is_still_
    # there` is what caught it.
    head = next(i for i, ln in enumerate(text)
                if ln.startswith("| Unit |") and "systematic" in ln and "narrative" in ln)
    types = [c.strip() for c in text[head].strip("|").split("|")][1:]
    inside, absent = {t: set() for t in types}, {t: set() for t in types}
    for line in text[head + 2:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        names = re.findall(r"`(\w+)`", cells[0])
        for t, cell in zip(types, cells[1:]):
            bucket = inside[t] if IN in cell else absent[t] if OUT in cell else None
            if bucket is not None:
                bucket.update(names)
    return {t: (inside[t], absent[t]) for t in types}


def documented_checks_for():
    """Execute the guide's own `checks_for(scope)` rather than modelling it.

    Reading a mapping constant out of the doc would only prove the RECORDS are right
    and leave the branching — which is where the review-type mistake actually lives —
    unverified. The source is a tracked file in this repository, not caller input.
    """
    text = (REPO / SCOPE_DERIVED_DOC).read_text(encoding="utf-8")
    for _lang, body in fenced_blocks(text):
        lines = body.splitlines()
        for i, line in enumerate(lines):
            if not line.startswith("def checks_for(scope):"):
                continue
            end = i + 1
            while end < len(lines) and (not lines[end].strip() or lines[end][:1].isspace()):
                end += 1
            ns = {}
            exec("\n".join(lines[i:end]), ns)          # noqa: S102 - repo-owned doc
            return ns["checks_for"]
    return None


class _NoFilesystem(ru.CheckRunner):
    """Resolves paths symbolically, so a documented block is judged on its SHAPE.

    The docs name artifact paths that do not exist here. Substituting resolution
    lets the cross-entry rules — which is where the drift happened — be checked
    without inventing a fixture tree that would itself have to be kept in step.

    WHAT THIS COSTS, and why the second test class exists. Stubbing resolution also
    stubs out the existence check that `contained_record` performs in the real run —
    so no test in this file can catch a block that declares a record which will not
    be there. That is precisely how the orchestrator guide reached a state where it
    validated here and exited 2 in practice. Existence is not decidable from the
    docs; the review type it is declared under IS, and that is what the scope tests
    below assert instead.
    """

    def __init__(self):
        super().__init__(records_root=".", skills_root=REPO)

    def argv_for(self, name, entry):
        return ["<doc>", name]

    def contained_record(self, value, ctx):
        return f"<doc>/{value}"


def _validate(checks):
    ru._validated_checks({"schema_version": ru.SCHEMA_VERSION, "checks": checks},
                         _NoFilesystem())


def _units_declared(checks):
    """Every unit the block would DERIVE, by the backend's own table."""
    out = set()
    for name, entry in checks.items():
        out |= set(ru._would_derive(name, entry))
    return out


def _gates_declared(checks):
    return {g for g, owner in ru.DERIVED_BY_GATE.items() if owner in checks}


class TestDocumentedChecksBlocksAreAccepted(unittest.TestCase):
    def test_every_listed_doc_is_actually_covered(self):
        """Per-FILE coverage, not a minimum count.

        The first version asserted `>= 2` blocks and found exactly 2 — passing
        while silently skipping `review-units.md` entirely. A guard against
        vacuous tests calibrated to a magic number is itself a vacuous test: it
        has to assert coverage of the enumerated set, or the set is decoration.
        """
        covered = {doc for doc, _, _ in checks_blocks()}
        for doc in DOCS:
            with self.subTest(doc=doc):
                self.assertIn(doc, covered, "listed in DOCS but no `checks` block was extracted")

    def test_every_documented_block_validates(self):
        """The headline: a reader copying any of these gets a block the backend
        accepts, not exit 2."""
        for doc, i, checks in checks_blocks():
            with self.subTest(doc=doc, block=i):
                try:
                    _validate(checks)
                except ru.InputError as e:
                    self.fail(f"{doc} block {i} is not a valid `checks` block: {e}")

    def test_the_guard_catches_the_defect_it_was_written_for(self):
        """Mutation check. `rob_record` without `rob_appraisal` is exactly what was
        printed in loop-protocol.md, and the test above must reject it."""
        with self.assertRaises(ru.InputError):
            _validate({"grade_profile": {"record": "a.json", "rob_record": "b.json"}})


class TestTheScopeDerivedExampleMatchesItsScope(unittest.TestCase):
    """The axis the shape tests cannot reach.

    A `checks` block is only correct RELATIVE TO A REVIEW TYPE. The guide's example
    passes `units_in_scope=scope_for(project_context.review_type)` and so is written
    for all five; declaring a check whose unit the scope table marks absent means the
    record will not exist, and `contained_record()` rejects it during validation —
    exit 2, before a single check runs, on the three lighter review types.
    """

    @classmethod
    def setUpClass(cls):
        cls.checks_for = staticmethod(documented_checks_for())
        cls.table = scope_table()

    def test_the_documented_function_is_still_there(self):
        """Anti-vacuity, per file, same lesson as the coverage test above: if the
        example is rewritten and this stops finding `checks_for`, every assertion
        below would pass over an empty set and prove nothing."""
        self.assertIsNotNone(self.checks_for,
                             f"no `def checks_for(scope):` found in {SCOPE_DERIVED_DOC}")
        self.assertTrue(self.table, f"no scope table parsed from {SCOPE_TABLE_DOC}")
        for expected in ("systematic", "scoping", "narrative", "rapid", "umbrella"):
            self.assertIn(expected, self.table)

    def test_no_review_type_declares_a_check_for_an_absent_unit(self):
        """The finding, generalised. Scoping has no certainty profile and no ScR
        checklist; rapid has no traced appraisal; narrative has none of the four."""
        for review_type, (in_scope, absent) in self.table.items():
            with self.subTest(review_type=review_type):
                checks = self.checks_for(in_scope)
                self.assertFalse(
                    _units_declared(checks) & absent,
                    f"{review_type}: declares a check deriving "
                    f"{sorted(_units_declared(checks) & absent)}, which the scope "
                    f"table marks absent — the record will not exist")
                self.assertFalse(
                    _gates_declared(checks) & absent,
                    f"{review_type}: declares the check owning "
                    f"{sorted(_gates_declared(checks) & absent)}, marked absent")

    def test_every_review_types_block_is_also_well_formed(self):
        """Shape still has to hold for each type's block, not only for systematic."""
        for review_type, (in_scope, _absent) in self.table.items():
            with self.subTest(review_type=review_type):
                try:
                    _validate(self.checks_for(in_scope))
                except ru.InputError as e:
                    self.fail(f"{review_type}: {e}")

    def test_every_in_scope_derivable_unit_is_still_declared(self):
        """The other direction, and the reason this cannot just drop entries.

        A unit in scope that no `checks` entry derives lands in `underived_units`
        and holds the verdict at CONTINUE forever — issue #4's failure mode from the
        opposite side. Trimming the block to fit the artifacts must never trim
        something the scope still demands.
        """
        for review_type, (in_scope, _absent) in self.table.items():
            with self.subTest(review_type=review_type):
                derivable = {u for u in in_scope if u in ru.DERIVED_BY}
                missing = derivable - _units_declared(self.checks_for(in_scope))
                self.assertFalse(missing, f"{review_type}: {sorted(missing)} in scope "
                                          f"but no check declared to derive it")

    def test_the_guard_catches_the_block_that_was_actually_printed(self):
        """Mutation check against the real defect, not a synthetic one.

        This is verbatim what the guide printed until the Codex review caught it —
        well-formed, accepted by every shape assertion in this file, and exit 2 for
        a scoping review. If this stops failing, the axis has been lost again.
        """
        hardcoded = {
            "prisma_flow": {"record": "reporting/counts.json"},
            "prisma_checklist": {"record": "reporting/checklist.json"},
            "rob_appraisal": {"record": "appraisal/risk-of-bias.json"},
            "grade_profile": {"record": "certainty/grade-profile.json",
                              "rob_record": "appraisal/risk-of-bias.json"},
        }
        _validate(hardcoded)        # shape-valid, which is the whole problem
        _in_scope, absent = self.table["scoping"]
        self.assertTrue(_units_declared(hardcoded) & absent,
                        "the block that shipped must still register as out of scope "
                        "for a scoping review")


if __name__ == "__main__":
    unittest.main()
