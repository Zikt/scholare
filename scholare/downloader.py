"""
PDF downloader — download open-access papers into a local folder.
"""

import os
from pathlib import Path

import pandas as pd
import requests

from .utils import sanitize_filename


def download_papers(df: pd.DataFrame, output_dir: str) -> None:
    """
    Download open-access PDFs listed in the DataFrame.

    The DataFrame must have 'Title' and 'OpenAccessURL' columns.
    Papers are saved to ``<output_dir>/papers/<sanitized_title>.pdf``.
    """
    papers_dir = Path(output_dir) / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    downloadable = df[
        (df["OpenAccessURL"].notna()) & (df["OpenAccessURL"].str.strip() != "")
    ]

    if downloadable.empty:
        print("ℹ️  No open-access PDFs available for download.")
        return

    print(f"\n📥 Downloading {len(downloadable)} open-access PDF(s) …")

    success = 0
    for _, row in downloadable.iterrows():
        title = row["Title"]
        url = row["OpenAccessURL"]
        safe_name = sanitize_filename(str(title)) + ".pdf"
        dest = papers_dir / safe_name

        if dest.exists():
            print(f"  ⏭️  Already exists: {safe_name}")
            success += 1
            continue

        try:
            resp = requests.get(url, timeout=30, stream=True)
            if resp.status_code == 200:
                with open(dest, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=8192):
                        fh.write(chunk)
                print(f"  ✅ {safe_name}")
                success += 1
            else:
                print(f"  ❌ HTTP {resp.status_code} — {title[:60]}")
        except Exception as exc:
            print(f"  ❌ Error downloading {title[:60]}: {exc}")

    print(f"\n📥 Downloaded {success}/{len(downloadable)} PDFs to {papers_dir}")
