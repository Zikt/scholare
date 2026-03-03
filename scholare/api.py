"""
API clients — SerpAPI (Google Scholar) and Semantic Scholar.
"""

import random
import re
import time
import urllib.parse
from datetime import datetime

import requests


# ── Semantic Scholar ────────────────────────────────────────────────────────


def s2_request(
    url: str,
    s2_api_key: str = "",
    method: str = "GET",
    params: dict | None = None,
    json_data: dict | None = None,
    max_retries: int = 5,
):
    """
    Make a request to the Semantic Scholar API with exponential backoff.
    """
    headers = {"x-api-key": s2_api_key} if s2_api_key else {}
    base_delay = 1.1 if s2_api_key else 3.1  # authenticated is faster

    for attempt in range(max_retries):
        try:
            if method == "POST":
                response = requests.post(
                    url, params=params, json=json_data, headers=headers, timeout=20
                )
            else:
                response = requests.get(
                    url, params=params, headers=headers, timeout=20
                )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:  # rate-limited
                wait = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                print(f"  ⏳ Rate limit hit. Waiting {wait:.1f}s …")
                time.sleep(wait)
            else:
                print(f"  ❌ S2 API error {response.status_code}")
                break
        except Exception as exc:
            print(f"  📡 Network error: {exc}")
            time.sleep(base_delay)

    return None


# ── OpenAlex (Direct Replacement for SerpAPI) ───────────────────────────────

def search_openalex(query: str, limit: int = 50) -> list[dict]:
    """
    Search OpenAlex via their free, open API.
    Does a full-text search against paper metadata.

    Returns a list of organic-style result dicts to mimic SerpAPI output structure
    so the rest of the pipeline works seamlessly, but injected with rich data.
    """
    # OpenAlex expects a 'mailto' for the polite pool, though not mandatory, it's good practice.
    url = "https://api.openalex.org/works"
    
    all_results = []
    per_page = min(50, limit)
    page = 1

    while len(all_results) < limit:
        params = {
            "search": query,
            "per-page": per_page,
            "page": page,
            "sort": "publication_date:desc", 
        }

        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code != 200:
                print(f"  ❌ OpenAlex API error {resp.status_code}")
                break
                
            data = resp.json()
            works = data.get("results", [])
            if not works:
                break
                
            for w in works:
                doi = w.get("doi", "")
                if doi:
                    doi = doi.replace("https://doi.org/", "")
                    
                oa_dict = w.get("open_access", {})
                is_oa = oa_dict.get("is_oa", False)
                oa_url = oa_dict.get("oa_url", "")
                
                # Format to match what the pipeline historically expects from Serp
                result = {
                    "title": w.get("title", "Untitled"),
                    "link": doi, # We store DOI in link if available
                    "publication_info": {"summary": w.get("publication_date", "")[:4]},
                    "inline_links": {"cited_by": {"total": w.get("cited_by_count", 0)}},
                    # Additional fields we pass along to save S2 lookups
                    "_openalex_is_oa": is_oa,
                    "_openalex_oa_url": oa_url,
                    "_openalex_doi": doi,
                    "_openalex_abstract": w.get("abstract_inverted_index") # OA returns inverted, we'd have to parse it, skipping for now
                }
                all_results.append(result)

            page += 1
            if len(all_results) < limit:
                time.sleep(0.5)

        except Exception as exc:
            print(f"  📡 OpenAlex Network error: {exc}")
            break

    return all_results[:limit]


# ── Preprint Sources ────────────────────────────────────────────────────────

def search_arxiv(query: str, limit: int = 20) -> list[dict]:
    """
    Search arXiv export API for latest preprints matching query.
    """
    # Simple query mapping, arXiv expects specific formatting, we will just pass all terms
    # removing logical operators for simplicity
    cleaned = query.replace(" AND ", " ").replace(" OR ", " ").replace(" NOT ", " ").strip()
    search_query = f"all:{urllib.parse.quote(cleaned)}"
    
    url = f"http://export.arxiv.org/api/query?search_query={search_query}&start=0&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
    
    all_results = []
    try:
        import defusedxml.ElementTree as ET
    except ImportError:
        import xml.etree.ElementTree as ET # Fallback if defusedxml is not installed
        
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            # define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                title_text = title.text.replace("\n", " ").strip() if title is not None else "Untitled"
                
                published = entry.find('atom:published', ns)
                year = published.text[:4] if published is not None else ""
                
                id_node = entry.find('atom:id', ns)
                link = id_node.text if id_node is not None else ""
                
                pdf_link = link.replace("abs", "pdf") if link else ""
                
                all_results.append({
                    "title": f"[arXiv] {title_text}",
                    "link": link,
                    "publication_info": {"summary": year},
                    "inline_links": {"cited_by": {"total": 0}},
                    "_openalex_is_oa": True,
                    "_openalex_oa_url": pdf_link,
                    "_openalex_doi": "",
                })
    except Exception as exc:
        print(f"  📡 arXiv error: {exc}")
        
    return all_results

def search_biorxiv(query: str, limit: int = 20) -> list[dict]:
    """
    Search bioRxiv/medRxiv.
    Note: Their API is date-range driven rather than query driven for the main endpoints.
    To simulate a search, we'll hit the Crossref API specifically for the bioRxiv DOI prefix (10.1101)
    """
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "filter": "member:246", # 246 is Cold Spring Harbor Laboratory (bioRxiv/medRxiv)
        "rows": limit,
        "sort": "published"
    }
    all_results = []
    try:
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json().get("message", {}).get("items", [])
            for w in data:
                title = w.get("title", ["Untitled"])[0]
                doi = w.get("DOI", "")
                year = ""
                # Crossref date parsing
                try:
                    year = str(w.get("published", {}).get("date-parts", [[None]])[0][0])
                except:
                    pass
                
                all_results.append({
                    "title": f"[bioRxiv] {title}",
                    "link": w.get("URL", ""),
                    "publication_info": {"summary": year},
                    "inline_links": {"cited_by": {"total": w.get("is-referenced-by-count", 0)}},
                    "_openalex_is_oa": True,
                    "_openalex_oa_url": f"https://www.biorxiv.org/content/{doi}.full.pdf", # heuristic
                    "_openalex_doi": doi,
                })
    except Exception as exc:
        print(f"  📡 bioRxiv (Crossref) error: {exc}")
        
    return all_results

# ── Unpaywall ───────────────────────────────────────────────────────────────

def get_unpaywall_pdf(doi: str, email: str = "") -> str:
    """
    Lookup an open-access PDF link for a DOI using Unpaywall.
    """
    if not doi:
        return ""
    
    url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": email} if email else {"email": "anonymous@example.com"}
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("is_oa"):
                best_loc = data.get("best_oa_location", {})
                if best_loc:
                    return best_loc.get("url_for_pdf") or best_loc.get("url") or ""
    except Exception:
        pass
        
    return ""

def search_google_scholar(query: str, api_key: str, limit: int = 50) -> list[dict]:
    """
    Search Google Scholar via SerpAPI with automatic pagination.

    Parameters
    ----------
    query : str
        The search query string.
    api_key : str
        SerpAPI API key.
    limit : int
        Maximum number of results to retrieve.

    Returns
    -------
    list[dict]
        List of organic result dicts from SerpAPI.
    """
    from serpapi import GoogleSearch

    all_results: list[dict] = []
    per_page = min(20, limit)  # SerpAPI max per page is 20
    start = 0

    while len(all_results) < limit:
        search = GoogleSearch(
            {
                "engine": "google_scholar",
                "q": query,
                "api_key": api_key,
                "num": per_page,
                "start": start,
            }
        )
        data = search.get_dict()
        organic = data.get("organic_results", [])
        if not organic:
            break

        all_results.extend(organic)
        start += per_page

        # small politeness delay between pages
        if len(all_results) < limit:
            time.sleep(1)

    return all_results[:limit]


# ── Paper metadata enrichment ──────────────────────────────────────────────


def get_paper_metadata(title: str, s2_api_key: str = "", doi: str = "") -> dict:
    """
    Look up a paper on Semantic Scholar by DOI (preferred) or title and return enriched metadata.
    """
    
    fields = "title,abstract,tldr,openAccessPdf,year,citationCount,externalIds,publicationTypes,authors"
    data = None
    
    # Priority 1: Search by DOI if available
    if doi:
        search_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
        params = {"fields": fields}
        direct_data = s2_request(search_url, s2_api_key=s2_api_key, params=params)
        if direct_data and direct_data.get("paperId"):
             data = {"data": [direct_data]}
             
    # Priority 2: Fallback to Title Search
    if not data or not data.get("data"):
        search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": title, "limit": 1, "fields": fields}
        data = s2_request(search_url, s2_api_key=s2_api_key, params=params)

    empty = {
        "Abstract": "N/A",
        "TLDR": "N/A",
        "OpenAccess": "N/A",
        "OpenAccessURL": "",
        "HasCode": "N/A",
        "HasData": "N/A",
        "DOI": doi, # Keep whatever DOI we passed in at least
        "S2ID": "",
        "S2Year": "",
        "Authors": "",
    }

    if not data or not data.get("data"):
        return empty

    paper = data["data"][0]
    if paper is None:
        return empty

    abstract = paper.get("abstract") or ""
    tldr = (paper.get("tldr") or {}).get("text") or ""
    oa_pdf = paper.get("openAccessPdf") or {}
    external_ids = paper.get("externalIds") or {}
    
    # Process authors into BibTeX standard "Last, First and Last, First" or just comma separated
    authors_raw = paper.get("authors") or []
    author_names = [a.get("name", "") for a in authors_raw if a.get("name")]
    authors_str = " and ".join(author_names) # BibTeX format uses 'and' to separate authors

    # heuristic code/data discovery
    blob = (abstract + " " + tldr).lower()
    has_code = "YES" if any(
        kw in blob for kw in ["github", "gitlab", "code available", "repository"]
    ) else "No"
    has_data = "YES" if any(
        kw in blob for kw in ["dataset", "zenodo", "data available", "figshare"]
    ) else "No"

    return {
        "Abstract": abstract,
        "TLDR": tldr,
        "OpenAccess": "Yes" if oa_pdf.get("url") else "No",
        "OpenAccessURL": oa_pdf.get("url", ""),
        "HasCode": has_code,
        "HasData": has_data,
        "DOI": external_ids.get("DOI", ""),
        "S2ID": paper.get("paperId", ""),
        "S2Year": str(paper.get("year", "")),
        "Authors": authors_str,
    }
