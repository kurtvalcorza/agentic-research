"""Every `checks` block printed in the documentation must be one the backend accepts.

`tests/test_contract_examples.py` exists because a documented example that nothing
executes drifts the moment the schema changes. This is the same guard for a surface
that file does not cover: the `checks` blocks in the verify-review skill docs.

It was needed within one review round of the feature shipping. Round 2 added the rule
that `grade_profile.rob_record` requires a `rob_appraisal` entry on the same record —
and the canonical `units.json` example in `loop-protocol.md`, which predated the rule,
was left naming `rob_record` alone. A caller copying it got exit 2 from `--dry-run`,
before anything ran. Nothing failed, because nothing executed the example.

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

# Docs that print a `checks` block a reader is meant to copy. EVERY entry must
# contribute at least one block — see test_every_listed_doc_is_actually_covered.
DOCS = [
    "skills/verify-review/references/loop-protocol.md",
    "skills/verify-review/SKILL.md",
    "specs/001-standards-enforcement-parity/contracts/review-units.md",
    # A Python kwarg literal in a ```python fence, not JSON. The first version of
    # this guard silently skipped it, and its content is the same identity rule
    # that broke loop-protocol.md — so the file most likely to drift was the one
    # least covered.
    "skills/orchestrate-research/references/detailed-guide.md",
]


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
    """Yield (doc, index, checks-dict) for every documented `checks` block."""
    for doc in DOCS:
        text = (REPO / doc).read_text(encoding="utf-8")
        for i, (_lang, body) in enumerate(fenced_blocks(text)):
            checks = _checks_from(body)
            if checks:
                yield doc, i, checks


class _NoFilesystem(ru.CheckRunner):
    """Resolves paths symbolically, so a documented block is judged on its SHAPE.

    The docs name artifact paths that do not exist here. Substituting resolution
    lets the cross-entry rules — which is where the drift happened — be checked
    without inventing a fixture tree that would itself have to be kept in step.
    """

    def __init__(self):
        super().__init__(records_root=".", skills_root=REPO)

    def argv_for(self, name, entry):
        return ["<doc>", name]

    def contained_record(self, value, ctx):
        return f"<doc>/{value}"


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
        runner = _NoFilesystem()
        for doc, i, checks in checks_blocks():
            with self.subTest(doc=doc, block=i):
                data = {"schema_version": ru.SCHEMA_VERSION, "checks": checks}
                try:
                    ru._validated_checks(data, runner)
                except ru.InputError as e:
                    self.fail(f"{doc} block {i} is not a valid `checks` block: {e}")

    def test_the_guard_catches_the_defect_it_was_written_for(self):
        """Mutation check. `rob_record` without `rob_appraisal` is exactly what was
        printed in loop-protocol.md, and the test above must reject it."""
        runner = _NoFilesystem()
        broken = {"grade_profile": {"record": "a.json", "rob_record": "b.json"}}
        with self.assertRaises(ru.InputError):
            ru._validated_checks({"schema_version": ru.SCHEMA_VERSION,
                                  "checks": broken}, runner)


if __name__ == "__main__":
    unittest.main()
