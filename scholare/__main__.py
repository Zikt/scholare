"""
CLI entry point — run with: scholare --config config.json
"""

import argparse

from .config import load_config
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scholare",
        description="Scholare — general-purpose literature review pipeline. "
        "Searches Google Scholar, enriches with Semantic Scholar, "
        "downloads open-access PDFs, and generates structured research notes.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to JSON config file (see config_example.json).",
    )
    parser.add_argument(
        "--previous-csv",
        default="",
        help="Path to a previous results.csv for new-paper comparison.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Disable downloading of PDFs (overrides config).",
    )

    args = parser.parse_args()

    config = load_config(args.config)

    if args.previous_csv:
        config["previous_csv"] = args.previous_csv

    if args.no_download:
        config["download_pdfs"] = False

    run_pipeline(config)


if __name__ == "__main__":
    main()
