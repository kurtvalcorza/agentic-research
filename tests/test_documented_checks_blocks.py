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

# Docs that print a `checks` block a reader is meant to copy.
DOCS = [
    "skills/verify-review/references/loop-protocol.md",
    "skills/verify-review/SKILL.md",
    "specs/001-standards-enforcement-parity/contracts/review-units.md",
]

FENCE = re.compile(r"^```(?:json)?\n(.*?)^```", re.S | re.M)


def checks_blocks():
    """Yield (doc, index, checks-dict) for every fenced block naming `checks`.

    Accepts a bare fence as well as a `json` one: `review-units.md` prints its
    block bare on purpose, so `test_contract_examples.py` does not try to execute
    a fragment as a whole record.
    """
    for doc in DOCS:
        text = (REPO / doc).read_text(encoding="utf-8")
        for i, block in enumerate(FENCE.findall(text)):
            if '"checks"' not in block:
                continue
            try:                        # a whole record
                parsed = json.loads(block)
                checks = parsed.get("checks")
            except json.JSONDecodeError:  # a fragment: `"checks": {…}`
                try:
                    checks = json.loads("{" + block.rstrip().rstrip(",") + "}")["checks"]
                except (json.JSONDecodeError, KeyError):
                    continue
            if isinstance(checks, dict):
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
    def test_at_least_one_block_is_found(self):
        """A regex that silently matches nothing would make every test below pass
        for the worst possible reason."""
        found = list(checks_blocks())
        self.assertGreaterEqual(len(found), 2, f"only found: {[(d, i) for d, i, _ in found]}")

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
