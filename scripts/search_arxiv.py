#!/usr/bin/env python3
"""Helper script to search arXiv from the command line."""
import argparse
import sys
import time
import xml.etree.ElementTree as ET
from urllib.error import HTTPError
from urllib.request import urlopen, quote


def search(query: str, max_results: int = 5, sort_by: str = "submittedDate", sort_order: str = "descending"):
    q = quote(query, safe="")
    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={q}&max_results={max_results}&sortBy={sort_by}&sortOrder={sort_order}"
    )
    for attempt in range(3):
        try:
            with urlopen(url) as resp:
                data = resp.read()
            break
        except HTTPError as exc:
            if exc.code == 429 and attempt < 2:
                time.sleep(3 + attempt * 2)
                continue
            raise
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(data)
    results = []
    for entry in root.findall("a:entry", ns):
        title = (entry.find("a:title", ns).text or "").strip().replace("\n", " ")
        arxiv_id = (entry.find("a:id", ns).text or "").strip().split("/abs/")[-1]
        published = (entry.find("a:published", ns).text or "")[:10]
        authors = ", ".join(
            (a.find("a:name", ns).text or "") for a in entry.findall("a:author", ns)
        )
        summary = (entry.find("a:summary", ns).text or "").strip()[:200]
        cats = ", ".join(c.get("term", "") for c in entry.findall("a:category", ns))
        results.append({
            "id": arxiv_id,
            "title": title,
            "published": published,
            "authors": authors,
            "categories": cats,
            "abstract": summary + "...",
            "pdf": f"https://arxiv.org/pdf/{arxiv_id}",
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Search arXiv via CLI")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--max-results", type=int, default=5)
    parser.add_argument("--sort-by", default="submittedDate", choices=["relevance", "lastUpdatedDate", "submittedDate"])
    parser.add_argument("--sort-order", default="descending", choices=["ascending", "descending"])
    args = parser.parse_args()

    for i, paper in enumerate(search(args.query, args.max_results, args.sort_by, args.sort_order), 1):
        print(f"{i}. [{paper['id']}] {paper['title']}")
        print(f"   Authors: {paper['authors']}")
        print(f"   Published: {paper['published']} | Categories: {paper['categories']}")
        print(f"   Abstract: {paper['abstract']}")
        print(f"   PDF: {paper['pdf']}")
        print()


if __name__ == "__main__":
    main()
