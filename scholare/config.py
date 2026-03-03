"""
Configuration loader — reads JSON config + .env API keys.
"""

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # handled gracefully below


def _find_env_file() -> Path | None:
    """Walk up from CWD looking for a .env file."""
    current = Path.cwd()
    for directory in [current, *current.parents]:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_config(config_path: str) -> dict:
    """
    Load and validate a research-tool configuration.

    Parameters
    ----------
    config_path : str
        Path to a JSON config file.

    Returns
    -------
    dict
        Validated configuration dictionary with the following keys:
        - query (str)
        - limit (int)
        - output_dir (str)
        - categories (dict[str, list[str]])
        - default_category (str)
        - download_pdfs (bool)
        - serp_api_key (str | None)
        - s2_api_key (str | None)
        - unpaywall_email (str | None)
        - sources (list[str])
    """
    # --- Load .env ----------------------------------------------------------
    env_file = _find_env_file()
    if env_file and load_dotenv:
        load_dotenv(env_file)
    elif env_file is None:
        print("⚠️  No .env file found. Relying on environment variables for API keys.")

    # --- Load JSON config ---------------------------------------------------
    config_path = Path(config_path)
    if not config_path.is_file():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    # --- Validate required fields -------------------------------------------
    required = ["query", "limit", "output_dir", "categories", "default_category"]
    for key in required:
        if key not in cfg:
            print(f"❌ Missing required config key: '{key}'")
            sys.exit(1)

    # --- Inject API keys from environment -----------------------------------
    cfg["serp_api_key"] = os.getenv("SERP_API_KEY", "")  # Optional now
    cfg["s2_api_key"] = os.getenv("S2_API_KEY", "")  # optional
    cfg["unpaywall_email"] = os.getenv("UNPAYWALL_EMAIL", "")  # optional

    # --- Defaults -----------------------------------------------------------
    cfg.setdefault("download_pdfs", True)
    cfg.setdefault("sources", ["openalex", "arxiv", "biorxiv"])

    return cfg
