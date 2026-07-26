"""Coverage for skills/dedupe-records/scripts/dedupe_records.py.

The duplicates-removed count feeds the PRISMA flow, so bad dedup corrupts a
published number, not just the screening workload. Standard library only.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

dd = load("skills/dedupe-records/scripts/dedupe_records.py")

T = 0.92  # the script's default fuzzy threshold


def rec(**kw):
    base = {"title": "A study of things", "year": 2024, "authors": ["Ada Smith"]}
    base.update(kw)
    return base


class TestNormalisation(unittest.TestCase):
    def test_doi_forms_collapse(self):
        for form in ("10.1/ABC", "https://doi.org/10.1/abc", "doi:10.1/abc", " 10.1/AbC "):
            with self.subTest(form=form):
                self.assertEqual(dd.norm_doi(form), "10.1/abc")

    def test_empty_doi(self):
        self.assertEqual(dd.norm_doi(None), "")

    def test_title_strips_markup_and_punctuation(self):
        self.assertEqual(dd.norm_title("<i>Effects</i> of X: a study!"), "effects of x a study")

    def test_first_surname(self):
        self.assertEqual(dd.first_surname(["Ada Lovelace", "Bob"]), "lovelace")
        self.assertEqual(dd.first_surname([]), "")

    def test_year_parsing_never_raises(self):
        self.assertEqual(dd._year("2024-05-01"), 2024)
        self.assertEqual(dd._year(2024), 2024)
        self.assertIsNone(dd._year("n.d."))
        self.assertIsNone(dd._year(None))


class TestPreprintDetection(unittest.TestCase):
    def test_arxiv_doi(self):
        self.assertTrue(dd.is_preprint({"doi": "10.48550/arXiv.2401.00001"}))

    def test_biorxiv_doi(self):
        self.assertTrue(dd.is_preprint({"doi": "10.1101/2024.01.01.123456"}))

    def test_type_field(self):
        self.assertTrue(dd.is_preprint({"type": "posted-content preprint"}))

    def test_venue_field(self):
        self.assertTrue(dd.is_preprint({"venue": "SSRN Electronic Journal"}))

    def test_journal_article_is_not_a_preprint(self):
        self.assertFalse(dd.is_preprint({"doi": "10.1016/j.x.2024.01.001",
                                         "type": "journal-article", "venue": "The Lancet"}))


class TestExactDoi(unittest.TestCase):
    def test_same_doi_different_formatting_merges(self):
        canon, report = dd.dedupe([rec(doi="10.1/abc"), rec(doi="https://doi.org/10.1/ABC")], T)
        self.assertEqual(len(canon), 1)
        self.assertEqual(report["duplicates_removed"], 1)

    def test_different_dois_do_not_merge(self):
        canon, report = dd.dedupe([rec(doi="10.1/a", title="Alpha study of one thing"),
                                   rec(doi="10.1/b", title="Beta trial of another matter")], T)
        self.assertEqual(len(canon), 2)
        self.assertEqual(report["duplicates_removed"], 0)


class TestFuzzyTitle(unittest.TestCase):
    def test_near_identical_titles_merge(self):
        canon, _ = dd.dedupe([rec(title="Effects of X on Y: a randomised trial"),
                              rec(title="Effects of X on Y - a randomized trial")], T)
        self.assertEqual(len(canon), 1)

    def test_unrelated_titles_do_not_merge(self):
        canon, _ = dd.dedupe([rec(title="Effects of X on Y"),
                              rec(title="Completely different subject entirely")], T)
        self.assertEqual(len(canon), 2)

    def test_year_guard_blocks_a_false_merge(self):
        """Same title two years apart is more likely two studies than one duplicate."""
        canon, _ = dd.dedupe([rec(title="Annual survey of practice", year=2020),
                              rec(title="Annual survey of practice", year=2024)], T)
        self.assertEqual(len(canon), 2)

    def test_one_year_apart_is_tolerated(self):
        """Online-first vs issue publication legitimately straddles a year boundary."""
        canon, _ = dd.dedupe([rec(title="Annual survey of practice", year=2023),
                              rec(title="Annual survey of practice", year=2024)], T)
        self.assertEqual(len(canon), 1)

    def test_author_guard_blocks_a_false_merge(self):
        canon, _ = dd.dedupe([rec(title="Systematic review of interventions", authors=["Ada Smith"]),
                              rec(title="Systematic review of interventions", authors=["Bo Jones"])], T)
        self.assertEqual(len(canon), 2)

    def test_missing_metadata_does_not_block_a_merge(self):
        """An absent year or author is unknown, not a mismatch."""
        canon, _ = dd.dedupe([rec(title="Effects of X on Y", year=None, authors=None),
                              rec(title="Effects of X on Y")], T)
        self.assertEqual(len(canon), 1)

    def test_threshold_is_respected(self):
        pair = [rec(title="Effects of X on Y in adults"),
                rec(title="Effects of X on Z in adults")]
        self.assertEqual(len(dd.dedupe(pair, 0.99)[0]), 2)
        self.assertEqual(len(dd.dedupe(pair, 0.50)[0]), 1)


class TestPreprintReconciliation(unittest.TestCase):
    def test_published_version_wins(self):
        pre = rec(title="Effects of X on Y", doi="10.48550/arXiv.2401.1")
        pub = rec(title="Effects of X on Y", doi="10.1016/j.x.2024.1", type="journal-article")
        canon, report = dd.dedupe([pre, pub], T)
        self.assertEqual(len(canon), 1)
        self.assertEqual(dd.norm_doi(canon[0]["doi"]), "10.1016/j.x.2024.1")
        self.assertEqual(report["duplicates_removed"], 1)

    def test_winner_records_what_it_absorbed(self):
        pre = rec(title="Effects of X on Y", doi="10.48550/arXiv.2401.1")
        pub = rec(title="Effects of X on Y", doi="10.1016/j.x.2024.1", type="journal-article")
        canon, _ = dd.dedupe([pre, pub], T)
        self.assertIn("10.48550/arxiv.2401.1", canon[0]["duplicate_of"])

    def test_order_does_not_change_the_winner(self):
        pre = rec(title="Effects of X on Y", doi="10.48550/arXiv.2401.1")
        pub = rec(title="Effects of X on Y", doi="10.1016/j.x.2024.1", type="journal-article")
        for order in ([pre, pub], [pub, pre]):
            with self.subTest(order=[r["doi"] for r in order]):
                canon, _ = dd.dedupe(order, T)
                self.assertEqual(dd.norm_doi(canon[0]["doi"]), "10.1016/j.x.2024.1")

    def test_two_preprints_keep_the_most_cited(self):
        a = rec(title="Effects of X on Y", doi="10.48550/arXiv.1", cited_by_count=2)
        b = rec(title="Effects of X on Y", doi="10.48550/arXiv.2", cited_by_count=99)
        canon, _ = dd.dedupe([a, b], T)
        self.assertEqual(canon[0]["cited_by_count"], 99)

    def test_input_records_are_not_mutated(self):
        """The winner is copied before duplicate_of is attached."""
        pub = rec(title="Effects of X on Y", doi="10.1016/j.x.1", type="journal-article")
        pre = rec(title="Effects of X on Y", doi="10.48550/arXiv.1")
        dd.dedupe([pub, pre], T)
        self.assertNotIn("duplicate_of", pub)
        self.assertNotIn("duplicate_of", pre)


class TestReportCounts(unittest.TestCase):
    def test_counts_reconcile_for_the_prisma_flow(self):
        """identified - duplicates_removed must equal after_dedup, since that
        subtraction is exactly what the PRISMA flow reports."""
        records = [rec(doi="10.1/a"), rec(doi="10.1/a"), rec(doi="10.1/a"),
                   rec(doi="10.1/b", title="Second distinct paper about things"),
                   rec(doi="10.1/c", title="Third entirely separate manuscript")]
        canon, report = dd.dedupe(records, T)
        self.assertEqual(report["identified"], 5)
        self.assertEqual(report["duplicates_removed"], 2)
        self.assertEqual(report["after_dedup"], 3)
        self.assertEqual(report["identified"] - report["duplicates_removed"],
                         report["after_dedup"])
        self.assertEqual(len(canon), report["after_dedup"])

    def test_groups_merged_counted(self):
        records = [rec(doi="10.1/a"), rec(doi="10.1/a"),
                   rec(doi="10.1/b", title="Another distinct paper"), rec(doi="10.1/b",
                                                                          title="Another distinct paper")]
        _, report = dd.dedupe(records, T)
        self.assertEqual(report["groups_merged"], 2)

    def test_empty_input_reports_zeroes(self):
        canon, report = dd.dedupe([], T)
        self.assertEqual(canon, [])
        self.assertEqual(report["identified"], 0)
        self.assertEqual(report["duplicates_removed"], 0)

    def test_no_duplicates_removes_nothing(self):
        records = [rec(doi="10.1/a", title="First unique paper on alpha"),
                   rec(doi="10.1/b", title="Second unique paper on beta")]
        _, report = dd.dedupe(records, T)
        self.assertEqual(report["duplicates_removed"], 0)


if __name__ == "__main__":
    unittest.main()
