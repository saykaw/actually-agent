"""
mcp/openalex_server.py — OpenAlex MCP tools.

Replaces mcp/semantic_scholar_server.py. OpenAlex is free, requires no API key,
and has a much more generous "polite pool" rate limit (~100k requests/day)
when you identify yourself via a mailto param — vs. Semantic Scholar's tight
unauthenticated limits that were bottlenecking investigations.

Interface intentionally mirrors semantic_scholar_server.py's function
signatures and return shapes (paper_id, title, year, citation_count, abstract,
authors, journal, url / abstract_preview / possible_contradiction) so it drops
in without touching prompts.py's field references, tools.py, or the UI layer.

Docs: https://docs.openalex.org
"""

import json
import os
import time
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security import sanitise_tool_output

OA_BASE = "https://api.openalex.org"

# OpenAlex's "polite pool" gives much higher rate limits if you pass a
# contact email. Set OPENALEX_MAILTO in your .env — falls back to the
# anonymous pool (still free, just stricter) if unset.
MAILTO = os.environ.get("OPENALEX_MAILTO", "")
HEADERS = {"User-Agent": "actually-agent/1.0 (kaggle-competition)"}
RATE_SLEEP = 0.15  # OpenAlex's polite pool tolerates ~10 req/sec; this is conservative


def _common_params(extra: dict) -> dict:
    params = dict(extra)
    if MAILTO:
        params["mailto"] = MAILTO
    return params


def _get(url: str, params: dict) -> dict:
    time.sleep(RATE_SLEEP)
    r = requests.get(url, params=_common_params(params), headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def _short_id(openalex_id: str) -> str:
    """OpenAlex IDs come back as full URLs (https://openalex.org/W123...).
    Normalise to the bare W-id for storage/graph nodes, but keep full ID
    for API calls that need it."""
    if not openalex_id:
        return ""
    return openalex_id.rstrip("/").split("/")[-1]


def _reconstruct_abstract(inverted_index: dict | None, max_chars: int = 800) -> str:
    """OpenAlex stores abstracts as an inverted index (word -> [positions])
    instead of plain text, to sidestep publisher copyright on abstract text
    reproduction. Rebuild a plain-text version for our own internal use."""
    if not inverted_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort(key=lambda x: x[0])
    text = " ".join(w for _, w in positions)
    return text[:max_chars]


def _extract_journal(work: dict) -> str:
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    return source.get("display_name", "Unknown")


def _extract_authors(work: dict, limit: int = 3) -> list[str]:
    names = []
    for a in (work.get("authorships") or [])[:limit]:
        author = a.get("author") or {}
        name = author.get("display_name")
        if name:
            names.append(name)
    return names


def _work_to_result(work: dict, abstract_chars: int = 800) -> dict:
    paper_id = _short_id(work.get("id", ""))
    abstract = sanitise_tool_output(
        _reconstruct_abstract(work.get("abstract_inverted_index"), abstract_chars),
        source="openalex",
    )
    return {
        "paper_id": paper_id,
        "title": work.get("title") or work.get("display_name", ""),
        "year": work.get("publication_year"),
        "citation_count": work.get("cited_by_count", 0),
        "abstract": abstract,
        "authors": _extract_authors(work),
        "journal": _extract_journal(work),
        "url": f"https://openalex.org/{paper_id}",
    }


def openalex_search(query: str, max_results: int = 5) -> str:
    """
    Search OpenAlex for academic papers across all fields (broader than
    PubMed — covers CS, social science, economics, etc, same role
    semantic_search used to play).
    Returns paper ID, title, year, citation count, abstract, authors, journal.
    Use for finding contradicting studies or replication attempts.
    """
    try:
        data = _get(f"{OA_BASE}/works", {
            "search": query,
            "per-page": min(max_results, 10),
        })
        results = [_work_to_result(w) for w in data.get("results", [])]
        return json.dumps({"results": results}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def openalex_get_citations(paper_id: str, max_results: int = 10) -> str:
    """
    Get papers that CITE a specific OpenAlex work. Core tool for finding
    contradicting evidence — papers that engaged with the original study but
    reached different conclusions.
    Flags abstracts containing contradiction signals automatically.
    """
    try:
        pid = _short_id(paper_id)
        data = _get(f"{OA_BASE}/works", {
            "filter": f"cites:{pid}",
            "per-page": min(max_results, 50),
        })
        results = []
        for w in data.get("results", []):
            base = _work_to_result(w, abstract_chars=600)
            abstract_lower = base["abstract"].lower()
            contradiction_signals = any(
                phrase in abstract_lower for phrase in [
                    "however", "contrary to", "did not replicate", "failed to confirm",
                    "no association", "we found no", "inconsistent with",
                    "could not confirm", "null result", "no significant",
                ]
            )
            results.append({
                "paper_id": base["paper_id"],
                "title": base["title"],
                "year": base["year"],
                "abstract_preview": base["abstract"],
                "possible_contradiction": contradiction_signals,
                "authors": base["authors"],
                "journal": base["journal"],
                "citation_count": base["citation_count"],
            })
        results.sort(key=lambda x: (-x["possible_contradiction"], -x["citation_count"]))
        return json.dumps({
            "total": len(results),
            "possible_contradictions": sum(1 for r in results if r["possible_contradiction"]),
            "results": results,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def openalex_get_paper(paper_id: str) -> str:
    """
    Get full metadata for a specific OpenAlex work by ID (accepts bare
    W-ids or full https://openalex.org/W... URLs).
    Use after openalex_search or openalex_get_citations to get the complete
    abstract and details.
    """
    try:
        pid = _short_id(paper_id)
        data = _get(f"{OA_BASE}/works/{pid}", {})
        abstract = sanitise_tool_output(
            _reconstruct_abstract(data.get("abstract_inverted_index"), max_chars=2000)
            or "No abstract available",
            source="openalex",
        )
        concepts = [c.get("display_name") for c in (data.get("concepts") or [])[:6]]
        return json.dumps({
            "paper_id": pid,
            "title": data.get("title") or data.get("display_name", ""),
            "year": data.get("publication_year"),
            "abstract": abstract,
            "authors": _extract_authors(data, limit=5),
            "journal": _extract_journal(data),
            "citation_count": data.get("cited_by_count", 0),
            "fields": concepts,
            "is_retracted": data.get("is_retracted", False),
            "url": f"https://openalex.org/{pid}",
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


OPENALEX_TOOLS = [openalex_search, openalex_get_citations, openalex_get_paper]


if __name__ == "__main__":
    result = openalex_search("smoking lung cancer epidemiology", max_results=2)
    for p in json.loads(result).get("results", []):
        print(f"[{p['paper_id']}] {p['title']} ({p['year']}) — {p['citation_count']} citations")
    print("OpenAlex MCP OK")