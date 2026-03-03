"""
Unit tests for scholare.utils
"""

import pandas as pd
import pytest

from scholare.utils import categorize_paper, find_new_discoveries, sanitize_filename


# ── sanitize_filename ───────────────────────────────────────────────────

class TestSanitizeFilename:
    def test_basic(self):
        assert sanitize_filename("Hello World") == "Hello_World"

    def test_removes_invalid_chars(self):
        assert sanitize_filename('file<>:"/\\|?*name') == "filename"

    def test_truncates(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name, max_len=50)
        assert len(result) == 50

    def test_strips_whitespace(self):
        assert sanitize_filename("  spaced  ") == "spaced"

    def test_empty_string(self):
        assert sanitize_filename("") == ""


# ── categorize_paper ────────────────────────────────────────────────────

class TestCategorizePaper:
    CATEGORIES = {
        "Hardware": ["electrode", "impedance", "sensor"],
        "Software": ["algorithm", "cnn", "model"],
        "Other": [],
    }

    def test_matches_first_category(self):
        row = pd.Series({"Title": "Electrode impedance study", "Abstract": ""})
        assert categorize_paper(row, self.CATEGORIES, "Other") == "Hardware"

    def test_matches_second_category(self):
        row = pd.Series({"Title": "A new CNN model", "Abstract": ""})
        assert categorize_paper(row, self.CATEGORIES, "Other") == "Software"

    def test_falls_back_to_default(self):
        row = pd.Series({"Title": "Unrelated paper", "Abstract": "Nothing here"})
        assert categorize_paper(row, self.CATEGORIES, "Other") == "Other"

    def test_case_insensitive(self):
        row = pd.Series({"Title": "ELECTRODE study", "Abstract": ""})
        assert categorize_paper(row, self.CATEGORIES, "Other") == "Hardware"

    def test_matches_in_abstract(self):
        row = pd.Series({"Title": "A study", "Abstract": "We used an algorithm"})
        assert categorize_paper(row, self.CATEGORIES, "Other") == "Software"


# ── find_new_discoveries ───────────────────────────────────────────────

class TestFindNewDiscoveries:
    def test_all_new_when_no_previous(self, tmp_path):
        df = pd.DataFrame({"Title": ["Paper A", "Paper B"]})
        fake_path = str(tmp_path / "nonexistent.csv")
        result = find_new_discoveries(df, fake_path)
        assert len(result) == 2

    def test_finds_new_papers(self, tmp_path):
        old_csv = tmp_path / "old.csv"
        pd.DataFrame({"Title": ["Paper A"]}).to_csv(old_csv, index=False)

        new_df = pd.DataFrame({"Title": ["Paper A", "Paper B", "Paper C"]})
        result = find_new_discoveries(new_df, str(old_csv))
        assert len(result) == 2
        assert set(result["Title"]) == {"Paper B", "Paper C"}

    def test_no_new_papers(self, tmp_path):
        old_csv = tmp_path / "old.csv"
        pd.DataFrame({"Title": ["Paper A", "Paper B"]}).to_csv(old_csv, index=False)

        new_df = pd.DataFrame({"Title": ["Paper A", "Paper B"]})
        result = find_new_discoveries(new_df, str(old_csv))
        assert len(result) == 0
