"""Summarize paper abstracts and article summaries via local Ollama LLM."""
from __future__ import annotations

import json
import os
import textwrap
import urllib.request
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Summary:
    headline: str
    key_points: List[str]
    relevance: str  # one-sentence why it matters


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def _chat(prompt: str, model: str = "kimi-k2.6:cloud", timeout: int = 60) -> str:
    """Send a prompt to Ollama and return the response text."""
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant. Produce concise, "
                        "structured summaries in plain text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("message", {}).get("content", "")


def summarize_paper(title: str, abstract: str, model: str = "kimi-k2.6:cloud") -> Summary:
    """Generate a structured summary for an academic paper."""
    prompt = textwrap.dedent(
        f"""\
        Title: {title}
        Abstract: {abstract}

        Summarize this paper in the following format:
        HEADLINE: One sentence headline.
        KEY POINTS:
        - Bullet 1
        - Bullet 2
        - Bullet 3
        RELEVANCE: One sentence on why this matters.
        """
    )
    text = _chat(prompt, model=model)
    return _parse_summary(text)


def summarize_article(title: str, text_body: str, model: str = "kimi-k2.6:cloud") -> Summary:
    """Generate a structured summary for a blog/news article."""
    prompt = textwrap.dedent(
        f"""\
        Title: {title}
        Content: {text_body[:4000]}

        Summarize this article in the following format:
        HEADLINE: One sentence headline.
        KEY POINTS:
        - Bullet 1
        - Bullet 2
        - Bullet 3
        RELEVANCE: One sentence on why this matters.
        """
    )
    text = _chat(prompt, model=model)
    return _parse_summary(text)


def _parse_summary(text: str) -> Summary:
    headline = ""
    key_points: List[str] = []
    relevance = ""
    section: Optional[str] = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.upper().startswith("HEADLINE:"):
            headline = line.split(":", 1)[-1].strip()
            section = "headline"
        elif line.upper().startswith("KEY POINTS:"):
            section = "points"
        elif line.upper().startswith("RELEVANCE:"):
            relevance = line.split(":", 1)[-1].strip()
            section = "relevance"
        elif section == "points" and line.startswith("-"):
            key_points.append(line.lstrip("- ").strip())
        elif section == "relevance" and line and not relevance:
            relevance = line
    if not headline:
        headline = text.split("\n")[0][:120]
    if not key_points:
        key_points = [text[:200]]
    if not relevance:
        relevance = "See abstract for details."
    return Summary(headline=headline, key_points=key_points, relevance=relevance)
