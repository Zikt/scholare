"""
Module for exporting research data into various reference manager formats.
"""

import re
from pathlib import Path
import pandas as pd


def _generate_bibtex_key(author_str: str, year: str, title: str) -> str:
    """
    Generate a clean BibTeX citation key: e.g., 'Smith2024Attention'
    """
    # 1. Extract first author's last name
    first_author = ""
    if author_str and author_str.lower() != "n/a":
        # Handle "First Last and First Last" format
        first_person = author_str.split(" and ")[0].strip()
        # Assume last word is the last name
        first_author = first_person.split()[-1]
    
    first_author = re.sub(r"[^A-Za-z]", "", first_author).capitalize()
    if not first_author:
        first_author = "Unknown"

    # 2. Year
    safe_year = str(year) if str(year).isdigit() else "0000"

    # 3. First meaningful word from title
    safe_title_word = ""
    if title and title.lower() != "untitled":
        # Remove brackets and punctuation
        clean_title = re.sub(r"[\[\]\(\):,'\"\.]", "", str(title))
        words = clean_title.split()
        stop_words = {"a", "an", "the", "in", "on", "of", "and", "or", "for", "with", "to"}
        for word in words:
            if word.lower() not in stop_words and len(word) > 2:
                safe_title_word = re.sub(r"[^A-Za-z]", "", word).capitalize()
                break
                
    if not safe_title_word:
        safe_title_word = "Paper"

    return f"{first_author}{safe_year}{safe_title_word}"


def generate_bibtex(df: pd.DataFrame, output_dir: str) -> str:
    """
    Convert a Scholare DataFrame into a standard .bib file.
    
    Parameters
    ----------
    df : pd.DataFrame
        The fully enriched Pandas DataFrame containing all research papers.
    output_dir : str
        The path to the output directory where results.bib will be saved.
        
    Returns
    -------
    str
        Path to the generated results.bib file.
    """
    bib_entries = []
    seen_keys = set()
    
    for idx, row in df.iterrows():
        # Clean inputs
        title = str(row.get("Title", "")).replace("{", "\\{").replace("}", "\\}")
        year = str(row.get("Year", ""))
        authors = str(row.get("Authors", ""))
        abstract = str(row.get("Abstract", "")).replace("{", "\\{").replace("}", "\\}")
        link = str(row.get("Link", ""))
        doi = str(row.get("DOI", ""))
        
        # Don't export empty/failed rows
        if not title or title.lower() == "untitled":
            continue
            
        # Generate globally unique key
        base_key = _generate_bibtex_key(authors, year, title)
        key = base_key
        counter = 1
        while key in seen_keys:
            key = f"{base_key}{chr(96+counter)}"  # append a, b, c...
            counter += 1
        seen_keys.add(key)
        
        # Construct BibTeX @article block
        lines = [
            f"@article{{{key},",
            f"  title = {{{title}}},"
        ]
        
        if authors and authors.lower() != "n/a":
            lines.append(f"  author = {{{authors}}},")
            
        if year and year.lower() != "n/a":
            lines.append(f"  year = {{{year}}},")
            
        if doi and doi.lower() != "n/a":
            lines.append(f"  doi = {{{doi}}},")
            
        if link and link.lower() != "n/a":
            lines.append(f"  url = {{{link}}},")
            
        if abstract and abstract.lower() != "n/a":
            lines.append(f"  abstract = {{{abstract}}},")
            
        lines.append("}\n")
        bib_entries.append("\n".join(lines))
        
    # Write to file
    out_path = Path(output_dir) / "results.bib"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(bib_entries))
        
    print(f"📚 BibTeX export saved to {out_path}")
    return str(out_path)
