"""
Visualization generator — save charts as PNG images.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd


def generate_visualizations(df: pd.DataFrame, output_dir: str) -> list[str]:
    """
    Create and save charts summarizing the paper collection.

    Returns a list of saved file paths (relative to output_dir).
    """
    viz_dir = Path(output_dir) / "visualizations"
    viz_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []

    # ── 1. Category distribution (pie) ──────────────────────────────────
    if "Category" in df.columns:
        fig, ax = plt.subplots(figsize=(7, 5))
        counts = df["Category"].value_counts()
        colors = plt.cm.Set2.colors[: len(counts)]
        counts.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=140, colors=colors)
        ax.set_ylabel("")
        ax.set_title("Research Focus — Category Distribution")
        path = viz_dir / "category_distribution.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        saved.append("visualizations/category_distribution.png")

    # ── 2. Open-access status (bar) ─────────────────────────────────────
    if "OpenAccess" in df.columns:
        fig, ax = plt.subplots(figsize=(5, 4))
        oa_counts = df["OpenAccess"].value_counts()
        bar_colors = {"Yes": "#4CAF50", "No": "#F44336", "N/A": "#9E9E9E"}
        oa_counts.plot(
            kind="bar",
            ax=ax,
            color=[bar_colors.get(k, "#9E9E9E") for k in oa_counts.index],
        )
        ax.set_title("Open Access Status")
        ax.set_ylabel("Papers")
        ax.set_xlabel("")
        plt.xticks(rotation=0)
        path = viz_dir / "open_access_status.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        saved.append("visualizations/open_access_status.png")

    # ── 3. Citation distribution (histogram) ────────────────────────────
    if "Citations" in df.columns:
        fig, ax = plt.subplots(figsize=(7, 4))
        citations = pd.to_numeric(df["Citations"], errors="coerce").dropna()
        if not citations.empty:
            ax.hist(citations, bins=15, color="#5C6BC0", edgecolor="white")
            ax.set_title("Citation Count Distribution")
            ax.set_xlabel("Citations")
            ax.set_ylabel("Papers")
            path = viz_dir / "citation_distribution.png"
            fig.savefig(path, dpi=150, bbox_inches="tight")
            saved.append("visualizations/citation_distribution.png")
        plt.close(fig)

    # ── 4. Year timeline (bar) ──────────────────────────────────────────
    if "Year" in df.columns:
        fig, ax = plt.subplots(figsize=(8, 4))
        years = df["Year"].replace("N/A", pd.NA).dropna()
        years = pd.to_numeric(years, errors="coerce").dropna().astype(int)
        if not years.empty:
            year_counts = years.value_counts().sort_index()
            year_counts.plot(kind="bar", ax=ax, color="#26A69A", edgecolor="white")
            ax.set_title("Publications per Year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Papers")
            plt.xticks(rotation=45)
            path = viz_dir / "year_distribution.png"
            fig.savefig(path, dpi=150, bbox_inches="tight")
            saved.append("visualizations/year_distribution.png")
        plt.close(fig)

    print(f"📊 Saved {len(saved)} visualization(s) to {viz_dir}")
    return saved
