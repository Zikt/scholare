"""
Unit tests for scholare.config
"""

import json
import os

import pytest

from scholare.config import load_config


class TestLoadConfig:
    """Tests for config validation (uses temp files, no real API keys)."""

    def _write_config(self, tmp_path, data: dict) -> str:
        path = tmp_path / "test_config.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def _valid_config(self) -> dict:
        return {
            "query": "test query",
            "limit": 10,
            "output_dir": "./test_output",
            "categories": {"Cat A": ["kw1"], "Other": []},
            "default_category": "Other",
        }

    def test_loads_valid_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SERP_API_KEY", "test_key_123")
        path = self._write_config(tmp_path, self._valid_config())
        cfg = load_config(path)
        assert cfg["query"] == "test query"
        assert cfg["limit"] == 10
        assert cfg["serp_api_key"] == "test_key_123"

    def test_missing_required_key_exits(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SERP_API_KEY", "test_key_123")
        incomplete = {"query": "test"}  # missing limit, output_dir, etc.
        path = self._write_config(tmp_path, incomplete)
        with pytest.raises(SystemExit):
            load_config(path)

    def test_missing_file_exits(self):
        with pytest.raises(SystemExit):
            load_config("nonexistent_config.json")

    def test_default_download_pdfs(self, tmp_path):
        cfg_data = self._valid_config()
        # don't set download_pdfs — should default to True
        path = self._write_config(tmp_path, cfg_data)
        cfg = load_config(path)
        assert cfg["download_pdfs"] is True
        assert cfg["sources"] == ["openalex", "arxiv", "biorxiv"]
