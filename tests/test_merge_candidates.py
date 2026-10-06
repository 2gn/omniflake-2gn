"""Tests for merging the candidate pool by repository.

The merge is a pure function over lists of rows, so each test builds two
small pools and asserts on what comes out.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import importlib

merge_candidates = importlib.import_module("merge-candidates")


class TestMerge(unittest.TestCase):
    """Tests that the pool is a set of repositories rather than of lines:
    a repository whose star count moved must yield one row, not two."""

    def test_a_changed_star_count_does_not_duplicate_a_repository(self):
        # This is the sort -u defect: the two lines differ, so a line-level
        # union kept both and the pool grew on every harvest.
        old = [{"owner": "a", "repo": "one", "stars": 3}]
        new = [{"owner": "a", "repo": "one", "stars": 5}]
        self.assertEqual(
            merge_candidates.merge([old, new]),
            [{"owner": "a", "repo": "one", "stars": 5}],
        )

    def test_the_later_pool_wins(self):
        # Files are handed over oldest first, so the fresh harvest is the
        # one that decides a repository's star count.
        old = [{"owner": "a", "repo": "one", "stars": 9}]
        new = [{"owner": "a", "repo": "one", "stars": 1}]
        self.assertEqual(merge_candidates.merge([old, new])[0]["stars"], 1)

    def test_a_repository_in_one_pool_only_survives(self):
        old = [{"owner": "a", "repo": "one", "stars": 1}]
        new = [{"owner": "b", "repo": "two", "stars": 2}]
        self.assertEqual(
            [(r["owner"], r["repo"]) for r in merge_candidates.merge([old, new])],
            [("a", "one"), ("b", "two")],
        )

    def test_duplicates_within_one_pool_collapse(self):
        # manual.py appends its bare entries on every run, and the existing
        # pool already carries 394 duplicates from past harvests.
        pool = [
            {"owner": "a", "repo": "one", "stars": 1},
            {"owner": "a", "repo": "one", "stars": 1},
        ]
        self.assertEqual(len(merge_candidates.merge([pool])), 1)

    def test_two_spellings_of_one_repository_collapse(self):
        # GitHub compares owners and repositories without case. A
        # repository renamed only in case is found again under its new
        # spelling, and the fresh harvest's spelling is the one kept.
        old = [{"owner": "ExpressoCodes", "repo": "Nixos-VM", "stars": 17}]
        new = [{"owner": "ExpressoCodes", "repo": "NixOS-VM", "stars": 17}]
        self.assertEqual(
            merge_candidates.merge([old, new]),
            [{"owner": "ExpressoCodes", "repo": "NixOS-VM", "stars": 17}],
        )

    def test_output_is_sorted_by_repository(self):
        # A canonical order, so a run that changes nothing produces no diff.
        pool = [
            {"owner": "b", "repo": "two", "stars": 0},
            {"owner": "a", "repo": "one", "stars": 0},
            {"owner": "a", "repo": "abc", "stars": 0},
        ]
        self.assertEqual(
            [(r["owner"], r["repo"]) for r in merge_candidates.merge([pool])],
            [("a", "abc"), ("a", "one"), ("b", "two")],
        )


if __name__ == "__main__":
    unittest.main()
