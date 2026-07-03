"""
mcp/pubmed_server.py — PubMed MCP tools.
Wraps NCBI E-utilities (free, no key needed).
"""

import json
import re
import xml.etree.ElementTree as ET
import requests
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  

from security import sanitise_tool_output

SEARCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
FETCH_URL   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
HEADERS     = {"User-Agent": "actually-agent/1.0 (kaggle-competition)"}


def _search_ids(query: str, max_results: int) -> list[str]:
    time.sleep(1.5)
    r = requests.get(SEARCH_URL, params={
        "db": "pubmed", "term": query,
        "retmax": max_results, "retmode": "json", "sort": "relevance",
    }, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json().get("esearchresult", {}).get("idlist", [])


def _fetch_papers(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    r = requests.get(FETCH_URL, params={
        "db": "pubmed", "id": ",".join(pmids),
        "retmode": "xml", "rettype": "abstract",
    }, headers=HEADERS, timeout=15)
    r.raise_for_status()

    results = []
    for article in ET.fromstring(r.text).findall(".//PubmedArticle"):
        def _text(path):
            el = article.find(path)
            return el.text if el is not None else ""

        abstract = sanitise_tool_output(_text(".//AbstractText"), source="pubmed")
        results.append({
            "pmid":     _text(".//PMID"),
            "title":    _text(".//ArticleTitle"),
            "abstract": abstract[:800],
            "journal":  _text(".//Journal/Title"),
            "year":     _text(".//PubDate/Year"),
            "authors":  [a.text for a in article.findall(".//Author/LastName")[:3]],
            "url":      f"https://pubmed.ncbi.nlm.nih.gov/{_text('.//PMID')}/",
        })
    return results


def pubmed_search(query: str, max_results: int = 5) -> str:
    """
    Search PubMed for peer-reviewed studies.
    Use specific queries with MeSH terms, e.g. 'acrylamide carcinogenicity humans cohort'.
    Returns title, abstract, journal, year, authors, URL for each result.
    """
    try:
        pmids = _search_ids(query, min(max_results, 10))
        if not pmids:
            return json.dumps({"results": [], "message": "No PubMed results found."})
        return json.dumps({"results": _fetch_papers(pmids)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def pubmed_get_paper(pmid: str) -> str:
    """
    Fetch full metadata for a specific PubMed paper by PMID.
    Use when a search result looks promising and you need the complete abstract.
    """
    try:
        papers = _fetch_papers([re.sub(r"[^0-9]", "", pmid)])
        return json.dumps(papers[0] if papers else {"error": "Not found"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def pubmed_check_retraction(pmid: str) -> str:
    """
    Check whether a PubMed paper has been retracted or corrected.
    Always call this for the primary study behind a claim.
    """
    try:
        pmid_clean = re.sub(r"[^0-9]", "", pmid)
        retraction_pmids = _search_ids(
            f"{pmid_clean}[Associated with Retracted Publication] OR "
            f"{pmid_clean}[Retracted Publication]",
            max_results=3,
        )
        return json.dumps({
            "pmid": pmid_clean,
            "retracted": len(retraction_pmids) > 0,
            "retraction_pmids": retraction_pmids,
            "note": (
                "Retraction notice found — this study has been withdrawn."
                if retraction_pmids
                else "No retraction found in PubMed. Also check retractionwatch.com."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


PUBMED_TOOLS = [pubmed_search, pubmed_get_paper, pubmed_check_retraction]


if __name__ == "__main__":
    result = pubmed_search("smoking lung cancer cohort", max_results=2)
    for p in json.loads(result).get("results", []):
        print(f"[{p['pmid']}] {p['title']} ({p['year']})")
    print("PubMed MCP OK")