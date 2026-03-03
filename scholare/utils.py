"""
Utility helpers — categorization, comparison, filename sanitization.
"""

import os
import re

import pandas as pd


def categorize_paper(row, categories: dict[str, list[str]], default_category: str) -> str:
    """
    Assign a category to a paper based on keyword matching in Title + Abstract.

    Parameters
    ----------
    row : pd.Series
        A row from the papers DataFrame (must have 'Title' and 'Abstract').
    categories : dict
        Mapping of category_name → list of keywords.
        The entry whose key equals *default_category* is used as fallback
        (its keyword list may be empty).
    default_category : str
        Category to return if no keywords match.

    Returns
    -------
    str
        Matched category name.
    """
    text = f"{row.get('Title', '')} {row.get('Abstract', '')}".lower()

    for cat_name, keywords in categories.items():
        if not keywords:  # skip the default/catch-all bucket
            continue
        if any(kw.lower() in text for kw in keywords):
            return cat_name

    return default_category


def find_new_discoveries(new_df: pd.DataFrame, previous_csv_path: str) -> pd.DataFrame:
    """
    Compare new results against a previous CSV; return only new papers.
    """
    if not os.path.exists(previous_csv_path):
        print("⚠️  No previous file found — all papers are treated as new.")
        return new_df

    old_df = pd.read_csv(previous_csv_path)
    merged = new_df.merge(
        old_df[["Title"]], on="Title", how="left", indicator=True
    )
    new_discoveries = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])

    print(
        f"✨ New papers discovered: {len(new_discoveries)} / {len(new_df)} total."
    )
    return new_discoveries


def deduplicate_papers(papers: list[dict]) -> list[dict]:
    """
    Remove duplicates from a list of paper dicts.
    Matches primarily on DOI, fallback to lowercase title matching.
    """
    seen_dois = set()
    seen_titles = set()
    unique_papers = []

    for p in papers:
        doi = p.get("_openalex_doi") or p.get("DOI") or p.get("link") or ""
        # Sometimes links are DOIs, let's just make it lower and strip
        doi = str(doi).lower().strip()
        
        title = p.get("title") or p.get("Title") or ""
        title = str(title).lower().strip()
        
        # Strip prefixes from titles (e.g. [arXiv])
        title_stripped = re.sub(r'^\[.*?\]\s*', '', title)

        is_dup = False
        
        if doi and doi in seen_dois:
            is_dup = True
        elif title_stripped and title_stripped in seen_titles:
            is_dup = True
            
        if not is_dup:
            if doi:
                seen_dois.add(doi)
            if title_stripped:
                seen_titles.add(title_stripped)
            unique_papers.append(p)
            
    return unique_papers


def check_boolean_query(query: str, text: str) -> bool:
    """
    Evaluates a complex boolean search query against a given text block.
    Supports AND, OR, NOT, parentheses, and quoted phrases.
    """
    if not text or not query:
        return False
        
    text_lower = text.lower()
    
    # 1. Normalize whitespace around parentheses to make tokenization easier
    q = query.replace("(", " ( ").replace(")", " ) ")
    q = " " + q + " "
    
    # 2. Extract tokens (quoted strings, AND/OR/NOT, parens, or bare words)
    tokens = re.findall(r'"[^"]+"|AND|OR|NOT|\(|\)|[^\s()"]+', q)
    
    eval_str = []
    for t in tokens:
        if t == "AND": eval_str.append("and")
        elif t == "OR":  eval_str.append("or")
        elif t == "NOT": eval_str.append("not")
        elif t == "(":   eval_str.append("(")
        elif t == ")":   eval_str.append(")")
        else:
            # It's a search term
            term = t.strip('"').lower()
            if not term:
                continue
            # If the literal word/phrase is in the text, evaluate to True
            eval_str.append("True" if term in text_lower else "False")
            
    try:
        # Evaluate the resulting python boolean expression
        return eval(" ".join(eval_str))
    except Exception:
        # If parsing completely fails (e.g. malformed user query), fail open
        return True


def sanitize_filename(name: str, max_len: int = 100) -> str:
    """
    Turn an arbitrary string into a safe filename.
    """
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = name.strip().replace(" ", "_")
    if len(name) > max_len:
        name = name[:max_len]
    return name
