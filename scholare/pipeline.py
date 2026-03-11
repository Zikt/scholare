"""
Pipeline orchestrator — ties all modules together.
"""

import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from .api import get_paper_metadata, search_openalex, search_arxiv, search_biorxiv, get_unpaywall_pdf
from .downloader import download_papers
from .notes import generate_research_notes
from .exporters import generate_bibtex
from .utils import categorize_paper, find_new_discoveries, sanitize_filename, deduplicate_papers, check_boolean_query, score_relevance, score_relevance_embeddings
from .visualizations import generate_visualizations


def _build_output_dirname(query: str, max_terms: int = 5) -> str:
    """
    Build a descriptive directory name from today's date and key search terms.

    Example: '2026-02-25_EEG_BCI_melanin_bias'
    """
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Strip boolean operators and quoted phrases, keep meaningful words
    cleaned = re.sub(r'["()\[\]]', "", query)
    # Remove boolean operators
    tokens = cleaned.split()
    stop = {"AND", "OR", "NOT", "and", "or", "not", ""}
    terms = [t.strip() for t in tokens if t.strip() not in stop]
    # Take the first few unique terms
    seen = set()
    unique_terms = []
    for t in terms:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            unique_terms.append(t)
        if len(unique_terms) >= max_terms:
            break

    slug = "_".join(unique_terms) if unique_terms else "search"
    slug = sanitize_filename(slug, max_len=80)
    return f"{date_str}_{slug}"


def _save_config_snapshot(config: dict, output_dir: str) -> None:
    """Save a sanitized copy of the config (API keys removed) into the output folder."""
    safe_config = {
        k: v for k, v in config.items()
        if k not in ("serp_api_key", "s2_api_key")
    }
    path = Path(output_dir) / "search_config.json"
    path.write_text(json.dumps(safe_config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📋 Config snapshot saved to {path}")


def _save_run_summary(
    df: pd.DataFrame, config: dict, output_dir: str, run_timestamp: str
) -> None:
    """Write a concise run_summary.txt with key stats about the search."""
    total = len(df)
    oa_count = (df["OpenAccess"] == "Yes").sum() if "OpenAccess" in df.columns else 0
    downloaded = len(list((Path(output_dir) / "papers").glob("*.pdf"))) if (Path(output_dir) / "papers").exists() else 0
    cats = df["Category"].value_counts().to_dict() if "Category" in df.columns else {}

    lines = [
        "═══════════════════════════════════════════",
        "  SCHOLARE — RUN SUMMARY",
        "═══════════════════════════════════════════",
        "",
        f"  Timestamp    : {run_timestamp}",
        f"  Query        : {config['query']}",
        f"  Limit        : {config['limit']}",
        f"  Total found  : {total}",
        f"  Open access  : {oa_count} / {total}",
        f"  PDFs saved   : {downloaded}",
        "",
        "  Categories:",
    ]
    for cat, count in cats.items():
        lines.append(f"    • {cat}: {count}")
    lines.append("")
    lines.append("  Files in this folder:")
    for f in sorted(Path(output_dir).rglob("*")):
        if f.is_file():
            rel = f.relative_to(output_dir)
            lines.append(f"    {rel}")
    lines.append("")
    lines.append("═══════════════════════════════════════════")

    path = Path(output_dir) / "run_summary.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📊 Run summary saved to {path}")


def run_pipeline(config: dict) -> pd.DataFrame:
    """
    Execute the full literature review pipeline:

    1. Search Google Scholar
    2. Enrich each result via Semantic Scholar
    3. Categorize papers
    4. Save raw CSV
    5. Download open-access PDFs (optional)
    6. Generate visualizations
    7. Generate structured research notes
    8. (Optional) Compare with previous run
    9. Save config snapshot + run summary

    Parameters
    ----------
    config : dict
        Configuration dictionary (from ``config.load_config``).

    Returns
    -------
    pd.DataFrame
        The enriched papers DataFrame.
    """
    query = config["query"]
    limit = config["limit"]
    base_output_dir = config["output_dir"]
    categories = config["categories"]
    default_cat = config["default_category"]
    
    # New Config Keys
    serp_key = config.get("serp_api_key", "")
    s2_key = config.get("s2_api_key", "")
    unpaywall_email = config.get("unpaywall_email", "")
    sources = config.get("sources", ["openalex", "arxiv", "biorxiv"])
    
    do_download = config.get("download_pdfs", True)
    sort_by = config.get("sort_by", "year")  # "year" or "citations"
    previous_csv = config.get("previous_csv", "")
    min_relevance = config.get("min_relevance", 15)
    
    use_embeddings = config.get("use_embeddings", False)
    search_intent = config.get("search_intent", query)  # fallback to boolean query if not provided
    compare_methods = config.get("compare_methods", False)
    
    run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build a descriptive output subfolder: <base>/<date>_<terms>/
    run_dirname = _build_output_dirname(query)
    output_dir = str(Path(base_output_dir) / run_dirname)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ── 0. Save config snapshot ─────────────────────────────────────────
    _save_config_snapshot(config, output_dir)

    # ── 1. Search (Multi-source) ────────────────────────────────────────
    print(f"\n🚀 Searching: {query}")
    print(f"   Limit: {limit} papers per source\n")

    raw_results = []
    
    # primary: OpenAlex
    if "openalex" in sources:
        print("   [1/3] Querying OpenAlex...")
        oa_res = search_openalex(query, limit)
        print(f"         Found {len(oa_res)} results.")
        raw_results.extend(oa_res)
    else:
        print("   [1/3] Skipping OpenAlex (not in sources)...")
        
    # secondary: arXiv
    if "arxiv" in sources:
         print("   [2/3] Querying arXiv...")
         arxiv_res = search_arxiv(query, limit)
         # Post-filter: check boolean query against title + abstract
         arxiv_res = [p for p in arxiv_res if check_boolean_query(query, f"{p.get('title', '')} {p.get('snippet', '')}")]
         print(f"         Found {len(arxiv_res)} results after boolean filtering.")
         raw_results.extend(arxiv_res)
    else:
         print("   [2/3] Skipping arXiv (not in sources)...")
         
    # tertiary: bioRxiv/medRxiv
    if "biorxiv" in sources:
         print("   [3/3] Querying bioRxiv/medRxiv...")
         bio_res = search_biorxiv(query, limit)
         # Post-filter: check boolean query against title + abstract
         bio_res = [p for p in bio_res if check_boolean_query(query, f"{p.get('title', '')} {p.get('snippet', '')}")]
         print(f"         Found {len(bio_res)} results after boolean filtering.")
         raw_results.extend(bio_res)
    else:
         print("   [3/3] Skipping bioRxiv/medRxiv (not in sources)...")

    if not raw_results:
        print("🛑 No results found across any sources.")
        return pd.DataFrame()

    print(f"\n   Total Raw Results: {len(raw_results)}")
    
    # Deduplicate
    results = deduplicate_papers(raw_results)
    
    print(f"   Total Unique Results: {len(results)}\n")

    # Limit total back down if wanted, but generally we want to process all unique found
    # We will process all of them up to a max safety limit so S2 rate limits don't explode
    MAX_PROCESSING = limit * 3 
    if len(results) > MAX_PROCESSING:
         results = results[:MAX_PROCESSING]

    # ── 2. Enrich & Build DataFrame ─────────────────────────────────────
    papers: list[dict] = []
    
    try:
        for idx, res in enumerate(results, 1):
            title = res.get("title", "Untitled")
            # Safeguard in case title is completely None (has happened with some APIs)
            if title is None:
                title = "Untitled"
                
            print(f"  [{idx}/{len(results)}] 📄 {title[:70]}…")

            # Extract basic info from the source
            pub_summary = res.get("publication_info", {}).get("summary", "")
            year_match = re.search(r"\d{4}", pub_summary)
            year = year_match.group() if year_match else "N/A"
            
            doi = res.get("_openalex_doi", "")

            # Enrich via Semantic Scholar
            meta = get_paper_metadata(title, s2_key, doi=doi)
        
            # Merge Open Access info
            # If openalex/preprints knew it was OA, keep that. Override if Unpaywall/S2 finds it.
            is_oa = "Yes" if res.get("_openalex_is_oa") else meta.get("OpenAccess", "No")
            oa_url = res.get("_openalex_oa_url") or meta.get("OpenAccessURL", "")
            
            final_doi = meta.get("DOI") or doi
            
            # Final safety check with Unpaywall if it's not OA yet
            if is_oa != "Yes" and final_doi:
                 upw_url = get_unpaywall_pdf(final_doi, unpaywall_email)
                 if upw_url:
                      is_oa = "Yes"
                      oa_url = upw_url

            papers.append(
                {
                    "Title": title,
                    "Year": meta.get("S2Year") or year,
                    "Citations": res.get("inline_links", {})
                    .get("cited_by", {})
                    .get("total", 0),
                    "Link": res.get("link", ""),
                    "Search_Query": query,
                    "Search_Timestamp": run_timestamp,
                    "Abstract": meta.get("Abstract", "N/A"),
                    "TLDR": meta.get("TLDR", "N/A"),
                    "OpenAccess": is_oa,
                    "OpenAccessURL": oa_url,
                    "HasCode": meta.get("HasCode", "N/A"),
                    "HasData": meta.get("HasData", "N/A"),
                    "DOI": final_doi,
                    "S2ID": meta.get("S2ID", ""),
                }
            )
    except KeyboardInterrupt:
        print("\n⚠️ Enrichment interrupted by user. Saving partial progress...")
    except Exception as e:
        print(f"\n⚠️ Unexpected error during enrichment: {e}. Saving partial progress...")

    df = pd.DataFrame(papers)

    if df.empty:
        print("🛑 No papers could be processed.")
        return df

    # ── 2b. Relevance scoring & filtering ────────────────────────────────
    model = None
    if use_embeddings or compare_methods:
        try:
            from sentence_transformers import SentenceTransformer
            print("\n⏳ Loading ML model for relevance scoring (this may take a moment)...")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            print("   Model loaded successfully.")
        except ImportError:
            print("\n⚠️  ML dependencies not found. To use embeddings, install with: pip install scholare[ml]")
            print("   Falling back to standard keyword scoring.")
            use_embeddings = False
            compare_methods = False

    df["Relevance_Keyword"] = df.apply(
        lambda row: score_relevance(query, row.get("Title", ""), row.get("Abstract", "")),
        axis=1,
    )

    if use_embeddings or compare_methods:
        print("   Calculating ML embeddings for relevance...")
        df["Relevance_ML"] = df.apply(
            lambda row: score_relevance_embeddings(search_intent, row.get("Title", ""), row.get("Abstract", ""), model),
            axis=1,
        )
    
    if use_embeddings:
        df["Relevance"] = df["Relevance_ML"]
    else:
        df["Relevance"] = df["Relevance_Keyword"]

    if not compare_methods:
        df = df.drop(columns=["Relevance_Keyword", "Relevance_ML"], errors="ignore")

    before_count = len(df)
    df_filtered = df[df["Relevance"] >= min_relevance].reset_index(drop=True)
    df_excluded = df[df["Relevance"] < min_relevance].sort_values("Relevance", ascending=False).reset_index(drop=True)

    if df_filtered.empty and before_count > 0:
        print(f"\n⚠️  Relevance filter would remove ALL {before_count} papers (threshold ≥ {min_relevance}).")
        print(f"    Keeping all papers and sorting by relevance instead.")
        df = df.sort_values("Relevance", ascending=False).reset_index(drop=True)
    else:
        df = df_filtered
        print(f"\n🎯 Relevance filter: kept {len(df)} / {before_count} papers (threshold ≥ {min_relevance})")

    # Save excluded papers for auditing
    if not df_excluded.empty:
        excluded_path = Path(output_dir) / "filtered_out.csv"
        df_excluded.to_csv(excluded_path, index=False)
        print(f"📋 {len(df_excluded)} excluded papers saved to {excluded_path}")

    # ── 3. Categorize ───────────────────────────────────────────────────
    df["Category"] = df.apply(
        lambda row: categorize_paper(row, categories, default_cat), axis=1
    )

    # ── 3b. Sort results ────────────────────────────────────────────────
    if sort_by == "citations":
        df["_SortKey"] = pd.to_numeric(df["Citations"], errors="coerce")
        print(f"   Sorted by: most cited first")
    else:  # default: year
        df["_SortKey"] = pd.to_numeric(df["Year"], errors="coerce")
        print(f"   Sorted by: most recent first")
    df = df.sort_values("_SortKey", ascending=False, na_position="last")
    df = df.drop(columns=["_SortKey"]).reset_index(drop=True)

    # ── 4. Save CSV ─────────────────────────────────────────────────────
    csv_path = Path(output_dir) / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n💾 Results saved to {csv_path}")

    # ── 4b. Export BibTeX ───────────────────────────────────────────────
    generate_bibtex(df, output_dir)

    # ── 5. Download PDFs ────────────────────────────────────────────────
    if do_download:
        download_papers(df, output_dir)

    # ── 6. Visualizations ───────────────────────────────────────────────
    viz_paths = generate_visualizations(df, output_dir)

    # ── 7. Research notes ───────────────────────────────────────────────
    generate_research_notes(df, config, output_dir, viz_paths)

    # ── 8. Compare with previous run ────────────────────────────────────
    if previous_csv and Path(previous_csv).is_file():
        new_df = find_new_discoveries(df, previous_csv)
        if not new_df.empty:
            new_csv = Path(output_dir) / "new_discoveries.csv"
            new_df.to_csv(new_csv, index=False)
            print(f"🆕 New discoveries saved to {new_csv}")

    # ── 9. Run summary ─────────────────────────────────────────────────
    _save_run_summary(df, config, output_dir, run_timestamp)

    # ── Done ────────────────────────────────────────────────────────────
    print(f"\n✅ Pipeline complete — {len(df)} papers processed.")
    print(f"   Output directory: {Path(output_dir).resolve()}")
    return df

