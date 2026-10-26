"""Web search tool using DuckDuckGo for live reputable research."""

import logging
import warnings
from typing import List, Dict

# Suppress package rename and third-party runtime warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Execute a web search query and return formatted results.
    
    Returns an empty list on failure to prevent hallucinated URLs.
    """
    results = []
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        ddgs = DDGS()
        raw_results = list(ddgs.text(query, max_results=max_results))
        for item in raw_results:
            url = item.get("href") or item.get("link") or ""
            if url:
                results.append({
                    "title": item.get("title", "Source"),
                    "url": url,
                    "snippet": item.get("body", "").strip(),
                })
    except Exception as e:
        logger.warning(f"DuckDuckGo search error for query '{query}': {e}")
        # Return empty list — never invent fake URLs like 'https://official.info/verify'
        return []

    return results


def run_research_queries(queries: List[str], max_per_query: int = 3) -> List[Dict[str, str]]:
    """Run a batch of 3-6 queries, deduplicating results by URL."""
    seen_urls = set()
    aggregated = []

    for q in queries:
        query_results = search_web(q, max_results=max_per_query)
        for res in query_results:
            url = res.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                aggregated.append(res)

    return aggregated
