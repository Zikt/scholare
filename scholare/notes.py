"""
Research notes generator — produce a structured Markdown summary.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd


def generate_research_notes(
    df: pd.DataFrame,
    config: dict,
    output_dir: str,
    viz_paths: list[str] | None = None,
) -> str:
    """
    Generate a comprehensive Markdown research notes file.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched papers DataFrame.
    config : dict
        Tool configuration (for recording search metadata).
    output_dir : str
        Root output directory. Notes are written to ``<output_dir>/research_notes.md``.
    viz_paths : list[str] | None
        Relative paths (from output_dir) to generated visualizations.

    Returns
    -------
    str
        Absolute path of the generated notes file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    notes_path = out / "research_notes.md"
    viz_paths = viz_paths or []

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = config.get("query", "N/A")
    total = len(df)

    lines: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────
    lines.append(f"# Research Notes\n")
    lines.append(f"> **Query:** `{query}`  ")
    lines.append(f"> **Generated:** {now}  ")
    lines.append(f"> **Total papers:** {total}\n")
    lines.append("---\n")

    # ── 1. Executive Summary ────────────────────────────────────────────
    lines.append("## 1. Executive Summary\n")

    oa_count = (df["OpenAccess"] == "Yes").sum() if "OpenAccess" in df.columns else 0
    code_count = (df["HasCode"].str.upper() == "YES").sum() if "HasCode" in df.columns else 0
    data_count = (df["HasData"].str.upper() == "YES").sum() if "HasData" in df.columns else 0

    oa_pct = f"{oa_count / total * 100:.1f}" if total else "0"
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Open-access papers | {oa_count} / {total} ({oa_pct}%) |")
    lines.append(f"| Papers with code hints | {code_count} |")
    lines.append(f"| Papers with data hints | {data_count} |")
    lines.append("")

    # ── 2. Taxonomy / Category Distribution ─────────────────────────────
    if "Category" in df.columns:
        lines.append("## 2. Taxonomy — Category Distribution\n")
        cat_counts = df["Category"].value_counts()
        lines.append("| Category | Count | % |")
        lines.append("|----------|------:|--:|")
        for cat, cnt in cat_counts.items():
            pct = f"{cnt / total * 100:.1f}" if total else "0"
            lines.append(f"| {cat} | {cnt} | {pct}% |")
        lines.append("")

    # ── 3. Top Cited Papers ─────────────────────────────────────────────
    lines.append("## 3. Top Cited Papers\n")
    if "Citations" in df.columns:
        top = df.nlargest(10, "Citations")
        lines.append("| # | Title | Year | Citations | Category | Link |")
        lines.append("|--:|-------|------|----------:|----------|------|")
        for i, (_, row) in enumerate(top.iterrows(), 1):
            title = str(row.get("Title", ""))
            year = str(row.get("Year", ""))
            cites = row.get("Citations", 0)
            cat = row.get("Category", "")
            link = row.get("Link", "")
            link_md = f"[link]({link})" if link else "—"
            lines.append(f"| {i} | {title} | {year} | {cites} | {cat} | {link_md} |")
        lines.append("")

    # ── 4. Key Findings by Category ─────────────────────────────────────
    if "Category" in df.columns:
        lines.append("## 4. Key Findings by Category\n")
        for cat in df["Category"].unique():
            lines.append(f"### {cat}\n")
            subset = df[df["Category"] == cat].sort_values(
                "Citations", ascending=False
            )
            for _, row in subset.iterrows():
                title = str(row.get("Title", ""))
                year = str(row.get("Year", ""))
                cites = row.get("Citations", 0)
                tldr = str(row.get("TLDR", ""))
                oa = row.get("OpenAccess", "N/A")
                code = row.get("HasCode", "N/A")
                data = row.get("HasData", "N/A")
                link = row.get("Link", "")
                doi = row.get("DOI", "")

                lines.append(f"- **{title}** ({year}, {cites} citations)")
                if tldr and tldr != "N/A":
                    # Wrap in block-quote
                    lines.append(f"  > {tldr}")
                lines.append(
                    f"  - Open Access: {oa} · Code: {code} · Data: {data}"
                )
                if doi:
                    lines.append(f"  - DOI: `{doi}`")
                if link:
                    lines.append(f"  - [Link]({link})")
                lines.append("")

    # ── 5. Visualizations ───────────────────────────────────────────────
    if viz_paths:
        lines.append("## 5. Visual Summary\n")
        for vp in viz_paths:
            label = Path(vp).stem.replace("_", " ").title()
            lines.append(f"### {label}\n")
            lines.append(f"![{label}]({vp})\n")

    # ── 6. Full Paper Index ─────────────────────────────────────────────
    lines.append("## 6. Full Paper Index\n")
    cols = [
        "Title", "Year", "Citations", "Category",
        "OpenAccess", "HasCode", "HasData", "Link",
    ]
    available_cols = [c for c in cols if c in df.columns]
    lines.append("| # | " + " | ".join(available_cols) + " |")
    lines.append("|--:|" + "|".join(["---"] * len(available_cols)) + "|")
    for i, (_, row) in enumerate(df.iterrows(), 1):
        vals = []
        for c in available_cols:
            v = str(row.get(c, ""))
            if c == "Link" and v:
                v = f"[link]({v})"
            vals.append(v)
        lines.append(f"| {i} | " + " | ".join(vals) + " |")
    lines.append("")

    # ── Write file ──────────────────────────────────────────────────────
    notes_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📝 Research notes saved to {notes_path}")
    return str(notes_path)
