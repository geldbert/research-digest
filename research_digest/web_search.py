"""Web search source using DuckDuckGo (free, no API key)."""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WebResult:
    title: str
    href: str
    body: str
    source: str = "web"


def _fetch_via_ddgs(query: str, max_results: int = 5) -> List[WebResult]:
    """Use the installed duckduckgo_search library."""
    from duckduckgo_search import DDGS
    results: List[WebResult] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                WebResult(
                    title=r.get("title", "Untitled"),
                    href=r.get("href", ""),
                    body=r.get("body", ""),
                    source="web",
                )
            )
    return results


def _fetch_via_bing(query: str, max_results: int = 5) -> List[WebResult]:
    """Fallback using DuckDuckGo HTML (no JS) scraping via urllib."""
    encoded = urllib.parse.quote(query)
    url = f"https://duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    results: List[WebResult] = []
    import re
    # DDG HTML: result titles + snippets
    # Capture result blocks
    blocks = re.findall(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        html,
        re.S,
    )
    for href, title_raw, snippet_raw in blocks[:max_results]:
        title = re.sub(r"<[^>]+>", "", title_raw)
        snippet = re.sub(r"<[^>]+>", "", snippet_raw)
        results.append(
            WebResult(
                title=title.strip(),
                href=href.strip(),
                body=snippet.strip(),
                source="web",
            )
        )
    return results


def fetch_web_results(
    query: str,
    max_results: int = 5,
    backend: Optional[str] = None,
) -> List[WebResult]:
    """Fetch web search results. Defaults to DDGS if available.

    Args:
        query: Search query string.
        max_results: Maximum results to return.
        backend: 'ddgs' or 'bing'. Auto-detected if None.
    """
    if backend is None:
        try:
            import duckduckgo_search  # noqa: F401
            backend = "ddgs"
        except Exception:
            backend = "bing"

    if backend == "ddgs":
        return _fetch_via_ddgs(query, max_results)
    return _fetch_via_bing(query, max_results)


def fetch_trending_in_tech(max_results: int = 5) -> List[WebResult]:
    """Heuristic trending tech query for research discovery."""
    return fetch_web_results(
        "latest AI research 2026 "
        "llm transformer neural network paper",
        max_results=max_results,
    )
