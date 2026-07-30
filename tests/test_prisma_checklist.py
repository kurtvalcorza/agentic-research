"""Coverage for skills/prisma-flow/scripts/prisma_checklist.py.

Asserts the rules in specs/001-standards-enforcement-parity/contracts/prisma-checklist.md.
Standard library only.
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load, fixture  # noqa: E402

pc = load("skills/prisma-flow/scripts/prisma_checklist.py")


def run(path, *args):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(sys, "argv", ["prisma_checklist.py", str(path), *args]), \
            redirect_stdout(out), redirect_stderr(err):
        code = pc.main()
    return code, out.getvalue(), err.getvalue()


class TestItemTable(unittest.TestCase):
    """The table is transcribed from BMJ 2021;372:n71 Table 1 and verified against it."""

    def test_forty_two_addressable_rows(self):
        self.assertEqual(len(pc.PRISMA_2020), 42)

    def test_twenty_seven_numbered_items(self):
        import re
        numbers = {re.match(r"\d+", n).group() for _, n, _ in pc.PRISMA_2020}
        self.assertEqual(len(numbers), 27)

    def test_lettered_groups_are_complete(self):
        numbers = [n for _, n, _ in pc.PRISMA_2020]
        for prefix, letters in [("10", "ab"), ("13", "abcdef"), ("16", "ab"),
                                ("20", "abcd"), ("23", "abcd"), ("24", "abc")]:
            for letter in letters:
                with self.subTest(item=prefix + letter):
                    self.assertIn(prefix + letter, numbers)

    def test_no_duplicate_numbers(self):
        numbers = [n for _, n, _ in pc.PRISMA_2020]
        self.assertEqual(len(numbers), len(set(numbers)))

    def test_sections_are_the_seven_prisma_sections(self):
        sections = []
        for section, _, _ in pc.PRISMA_2020:
            if section not in sections:
                sections.append(section)
        self.assertEqual(sections, ["Title", "Abstract", "Introduction", "Methods",
                                    "Results", "Discussion", "Other information"])


class TestValidRecord(unittest.TestCase):
    def test_complete_record_passes(self):
        code, out, err = run(fixture("checklist.valid.json"), "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("✅", out)
        self.assertIn("42 of 42 rows addressed", out)

    def test_not_applicable_justification_appears(self):
        _, out, _ = run(fixture("checklist.valid.json"))
        self.assertIn("No meta-analysis performed", out)
        self.assertIn("*n/a —", out)

    def test_cites_the_source_and_does_not_reproduce_wording(self):
        _, out, _ = run(fixture("checklist.valid.json"))
        self.assertIn("BMJ 2021;372:n71", out)
        self.assertIn("referenced here, not reproduced", out)

    def test_states_what_it_cannot_verify(self):
        _, out, _ = run(fixture("checklist.valid.json"))
        self.assertIn("cannot verify that the cited location actually addresses the item", out)

    def test_escapes_free_text_in_checklist_cells(self):
        rec = json.loads(fixture("checklist.valid.json").read_text(encoding="utf-8"))
        rec["items"][0]["location"] = "Methods | search\nAppendix A"
        na_item = next(item for item in rec["items"] if "not_applicable" in item)
        na_item["not_applicable"] = "No pooling | narrative\nper SWiM"
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "checklist.json"
            path.write_text(json.dumps(rec), encoding="utf-8")
            code, out, err = run(path, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("Methods &#124; search<br>Appendix A", out)
        self.assertIn("No pooling &#124; narrative<br>per SWiM", out)
        self.assertNotIn("| Methods | search", out)


class TestCompleteness(unittest.TestCase):
    def test_all_27_numbers_but_missing_subitems_still_fails(self):
        """The headline trap.

        A record addressing every top-level number looks complete if you count 27.
        Counting the 42 addressable rows catches the fifteen missing sub-items.
        """
        code, out, _ = run(fixture("checklist.subitems-omitted.json"), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("27 of 42 rows addressed", out)
        for missing in ("13b", "13c", "13d", "13e", "13f", "20b", "20c", "20d", "23b", "24b"):
            with self.subTest(item=missing):
                self.assertIn(f"item {missing}", out)

    def test_partial_record_lists_unaddressed_rows(self):
        code, out, _ = run(fixture("checklist.partial.json"), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("row(s) not addressed", out)

    def test_unaddressed_rows_listed_above_the_table(self):
        """In 42 rows, a gap shown only as a blank cell is a gap nobody sees."""
        _, out, _ = run(fixture("checklist.partial.json"))
        self.assertLess(out.index("row(s) not addressed"), out.index("## Checklist"))

    def test_empty_justification_does_not_address_an_item(self):
        code, out, _ = run(fixture("checklist.empty-justification.json"), "--strict")
        self.assertEqual(code, 1)
        self.assertIn("an empty value does not address the item", out)

    def test_violation_without_strict_exits_zero(self):
        code, out, _ = run(fixture("checklist.partial.json"))
        self.assertEqual(code, 0)
        self.assertIn("not addressed", out)


class TestMalformed(unittest.TestCase):
    def assert_malformed(self, name, *needles):
        code, out, err = run(fixture(name), "--strict")
        self.assertEqual(code, 2, msg=f"expected exit 2 for {name}, got {code}")
        for n in needles:
            self.assertIn(n, err)
        self.assertNotIn("## Checklist", out)

    def test_both_fields_rejected(self):
        self.assert_malformed("checklist.both-fields.json", "one or the other")

    def test_unknown_number_rejected(self):
        self.assert_malformed("checklist.unknown-number.json", "'28'", "disagree")

    def test_duplicate_number_rejected(self):
        self.assert_malformed("checklist.duplicate-number.json", "duplicate item")

    def test_empty_items_rejected(self):
        self.assert_malformed("checklist.empty-items.json", "nothing to check")

    def test_unknown_variant_rejected(self):
        self.assert_malformed("checklist.bad-variant.json", "prisma_2009")


class TestScopingVariantRefuses(unittest.TestCase):
    """PRISMA-ScR refuses rather than guessing.

    Its item table could not be transcribed from an accessible copy of the source.
    An approximated table would make every verdict wrong while looking authoritative,
    so the variant must fail loudly and say why.
    """

    def test_scr_variant_refuses_with_a_reason(self):
        code, out, err = run(fixture("checklist.scr-variant.json"), "--strict")
        self.assertEqual(code, 2)
        self.assertIn("not implemented", err)
        self.assertIn("10.7326/M18-0850", err)
        self.assertIn("approximated table", err)
        self.assertNotIn("## Checklist", out)

    def test_scr_is_not_silently_treated_as_prisma_2020(self):
        """The dangerous failure would be falling back to the wrong table."""
        _, out, _ = run(fixture("checklist.scr-variant.json"))
        self.assertNotIn("42", out)


class TestGolden(unittest.TestCase):
    def test_generated_checklist_matches_golden(self):
        _, out, _ = run(fixture("checklist.valid.json"))
        expected = fixture("checklist.valid.golden.md").read_text(encoding="utf-8")
        self.assertEqual(out.rstrip() + "\n", expected)


if __name__ == "__main__":
    unittest.main()
