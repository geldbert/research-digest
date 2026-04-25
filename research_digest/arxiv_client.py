"""Fetch and parse arXiv papers using only stdlib + urllib."""
from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import List

ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"


@dataclass
class Paper:
    arxiv_id: str
    title: str
    summary: str
    authors: List[str]
    published: str  # ISO date
    primary_category: str
    pdf_url: str
    comment: str = ""


def fetch_papers(
    query: str = "cat:cs.AI",
    max_results: int = 10,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
) -> List[Paper]:
    """Query arXiv API and return a list of Paper objects."""
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query={urllib.parse.quote(query)}"
        f"&max_results={max_results}"
        f"&sortBy={sort_by}"
        f"&sortOrder={sort_order}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "research-digest/0.1.8"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()

    root = ET.fromstring(data)
    ns = {"a": ATOM_NS, "arxiv": ARXIV_NS}
    papers: List[Paper] = []
    for entry in root.findall("a:entry", ns):
        arxiv_id = _text(entry, "a:id", ns, default="").split("/abs/")[-1]
        title = _text(entry, "a:title", ns, default="").strip().replace("\n", " ")
        summary = _text(entry, "a:summary", ns, default="").strip()
        published = _text(entry, "a:published", ns, default="")[:10]
        authors = [
            a.find("a:name", ns).text for a in entry.findall("a:author", ns)
            if a.find("a:name", ns) is not None
        ]
        primary = ""
        cat = entry.find("arxiv:primary_category", ns)
        if cat is not None:
            primary = cat.get("term", "")
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        comment = ""
        comment_el = entry.find("arxiv:comment", ns)
        if comment_el is not None and comment_el.text:
            comment = comment_el.text.strip()
        papers.append(
            Paper(
                arxiv_id=arxiv_id,
                title=title,
                summary=summary,
                authors=authors,
                published=published,
                primary_category=primary,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return papers


def _text(element, tag: str, ns, default: str = "") -> str:
    el = element.find(tag, ns)
    return el.text if el is not None and el.text else default


if __name__ == "__main__":
    ps = fetch_papers("all:transformer", max_results=2)
    for p in ps:
        print(p.arxiv_id, p.title)
