"""
mcp/semantic_scholar_server.py — Semantic Scholar MCP tools.
Free API, no key needed for basic use.
"""

import json
import time
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  

from security import sanitise_tool_output

SS_BASE    = "https://api.semanticscholar.org/graph/v1"
HEADERS    = {"User-Agent": "actually-agent/1.0 (kaggle-competition)"}
RATE_SLEEP = 3.0   # respectful pacing for free tier


def _get(url: str, params: dict) -> dict:
    time.sleep(RATE_SLEEP)
    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def semantic_search(query: str, max_results: int = 5) -> str:
    """
    Search Semantic Scholar for academic papers.
    Broader than PubMed — covers CS, social science, economics too.
    Returns paper ID, title, year, citation count, abstract, authors, journal.
    Use for finding contradicting studies or replication attempts.
    """
    try:
        data = _get(f"{SS_BASE}/paper/search", {
            "query": query,
            "limit": min(max_results, 10),
            "fields": "paperId,title,year,citationCount,abstract,authors,journal,isOpenAccess",
        })
        results = []
        for p in data.get("data", []):
            abstract = sanitise_tool_output(
                (p.get("abstract") or "")[:800], source="semantic_scholar"
            )
            results.append({
                "paper_id":      p.get("paperId", ""),
                "title":         p.get("title", ""),
                "year":          p.get("year"),
                "citation_count": p.get("citationCount", 0),
                "abstract":      abstract,
                "authors":       [a["name"] for a in p.get("authors", [])[:3]],
                "journal":       (p.get("journal") or {}).get("name", "Unknown"),
                "url":           f"https://www.semanticscholar.org/paper/{p.get('paperId','')}",
            })
        return json.dumps({"results": results}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def semantic_get_citations(paper_id: str, max_results: int = 10) -> str:
    """
    Get papers that CITE a specific paper on Semantic Scholar.
    Core tool for finding contradicting evidence — papers that engaged with
    the original study but reached different conclusions.
    Flags abstracts containing contradiction signals automatically.
    """
    try:
        data = _get(f"{SS_BASE}/paper/{paper_id}/citations", {
            "limit": min(max_results, 50),
            "fields": "title,year,abstract,authors,journal,citationCount",
        })
        results = []
        for c in data.get("data", []):
            paper = c.get("citingPaper", {})
            abstract = sanitise_tool_output(
                (paper.get("abstract") or "")[:600], source="semantic_scholar"
            )
            contradiction_signals = any(
                phrase in abstract.lower() for phrase in [
                    "however", "contrary to", "did not replicate", "failed to confirm",
                    "no association", "we found no", "inconsistent with",
                    "could not confirm", "null result", "no significant",
                ]
            )
            results.append({
                "paper_id":             paper.get("paperId", ""),
                "title":                paper.get("title", ""),
                "year":                 paper.get("year"),
                "abstract_preview":     abstract,
                "possible_contradiction": contradiction_signals,
                "authors":              [a["name"] for a in paper.get("authors", [])[:3]],
                "journal":              (paper.get("journal") or {}).get("name", "Unknown"),
                "citation_count":       paper.get("citationCount", 0),
            })
        # Contradictions first, then by citation count
        results.sort(key=lambda x: (-x["possible_contradiction"], -x["citation_count"]))
        return json.dumps({
            "total": len(results),
            "possible_contradictions": sum(1 for r in results if r["possible_contradiction"]),
            "results": results,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def semantic_get_paper(paper_id: str) -> str:
    """
    Get full metadata for a specific Semantic Scholar paper by ID.
    Use after semantic_search or semantic_get_citations to get the complete abstract.
    """
    try:
        data = _get(f"{SS_BASE}/paper/{paper_id}", {
            "fields": "title,year,abstract,authors,journal,citationCount,referenceCount,fieldsOfStudy",
        })
        abstract = sanitise_tool_output(
            data.get("abstract", "No abstract available"), source="semantic_scholar"
        )
        return json.dumps({
            "paper_id":       paper_id,
            "title":          data.get("title", ""),
            "year":           data.get("year"),
            "abstract":       abstract,
            "authors":        [a["name"] for a in data.get("authors", [])[:5]],
            "journal":        (data.get("journal") or {}).get("name", "Unknown"),
            "citation_count": data.get("citationCount", 0),
            "fields":         data.get("fieldsOfStudy", []),
            "url":            f"https://www.semanticscholar.org/paper/{paper_id}",
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


SEMANTIC_TOOLS = [semantic_search, semantic_get_citations, semantic_get_paper]


if __name__ == "__main__":
    result = semantic_search("smoking lung cancer epidemiology", max_results=2)
    for p in json.loads(result).get("results", []):
        print(f"[{p['paper_id'][:8]}] {p['title']} ({p['year']}) — {p['citation_count']} citations")
    print("Semantic Scholar MCP OK")