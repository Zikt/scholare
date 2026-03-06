"""
Utility helpers — categorization, comparison, filename sanitization.
"""

import os
import re

import pandas as pd


def score_relevance(query: str, title: str, abstract: str) -> int:
    """
    Score a paper's relevance to the search query (0–100).

    Handles complex Boolean queries like:
        (EEG OR electroencephalography) AND (bias OR disparity) AND (electrode OR gel)

    Scoring logic:
    1. Split the query on AND into groups. Each group may contain OR alternatives.
    2. For each AND-group, check if ANY term from the group matches the text.
       - Title match earns the group 3 pts; abstract-only match earns 1 pt.
    3. Score = (earned group points / max group points) * 85.
    4. Bonus +15 if any multi-word phrase appears verbatim.
    5. Clamped to 0–100.

    A paper matching at least one term from EVERY AND-group will score ≥ 63.

    Parameters
    ----------
    query : str
        The user's boolean search query string.
    title : str
        Paper title.
    abstract : str
        Paper abstract.

    Returns
    -------
    int
        Relevance score between 0 and 100.
    """
    if not query:
        return 0

    title_lower = (title or "").lower()
    abstract_lower = (abstract or "").lower()
    combined = title_lower + " " + abstract_lower

    # ── 1. Split on AND into groups ──────────────────────────────────
    # e.g. "(EEG OR electroencephalography) AND (bias OR disparity)"
    #  → ["(EEG OR electroencephalography)", "(bias OR disparity)"]
    and_groups = re.split(r'\bAND\b', query, flags=re.IGNORECASE)

    if not and_groups:
        return 0

    # ── 2. Score each AND-group ──────────────────────────────────────
    raw_score = 0
    max_possible = len(and_groups) * 3  # best case: every group matches title

    quoted_phrases = re.findall(r'"([^"]+)"', query)
    skip = {"or", "not", "(", ")"}

    for group in and_groups:
        # Extract terms from this group (bare words + quoted phrases)
        tokens = re.findall(r'"([^"]+)"|(\S+)', group)
        terms = []
        for phrase, word in tokens:
            if phrase:
                terms.append(phrase.lower())
            elif word.lower() not in skip:
                terms.append(word.lower())

        if not terms:
            continue

        # Check if ANY term from this OR-group matches
        title_hit = any(t in title_lower for t in terms)
        abstract_hit = any(t in abstract_lower for t in terms)

        if title_hit:
            raw_score += 3
        elif abstract_hit:
            raw_score += 1

    # ── 3. Phrase bonus ──────────────────────────────────────────────
    phrase_bonus = 0
    for phrase in quoted_phrases:
        if " " in phrase and phrase.lower() in combined:
            phrase_bonus = 15
            break

    # ── 4. Normalize to 0–100 ────────────────────────────────────────
    normalized = int((raw_score / max_possible) * 85) + phrase_bonus if max_possible > 0 else 0
    return min(normalized, 100)


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
