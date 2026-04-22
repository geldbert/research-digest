"""Fetch RSS/Atom feeds and return structured articles using stdlib only."""
from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Article:
    title: str
    link: str
    summary: str
    published: str
    authors: List[str] = field(default_factory=list)
    feed_name: str = ""


# Common RSS/Atom namespace maps
_NS_MAP = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def fetch_feed(url: str, feed_name: str = "", timeout: int = 15) -> List[Article]:
    """Fetch an RSS or Atom feed and return articles."""
    req = urllib.request.Request(url, headers={"User-Agent": "research-digest/0.1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag == "feed":
        return _parse_atom(root, feed_name)
    if tag in ("rss", "Rss"):
        return _parse_rss(root, feed_name)
    # Fallback: try atom then rss
    atom = _parse_atom(root, feed_name)
    return atom if atom else _parse_rss(root, feed_name)


def _parse_atom(root: ET.Element, feed_name: str) -> List[Article]:
    ns = {"a": _NS_MAP["atom"]}
    articles: List[Article] = []
    for entry in root.findall("a:entry", ns):
        title = _text(entry, "a:title", ns)
        link = ""
        for lnk in entry.findall("a:link", ns):
            if lnk.get("rel") in (None, "alternate"):
                link = lnk.get("href", "")
                break
        summary = _text(entry, "a:summary", ns) or _text(entry, "a:content", ns)
        published = _text(entry, "a:published", ns) or _text(entry, "a:updated", ns)
        authors = [
            a.find("a:name", ns).text
            for a in entry.findall("a:author", ns)
            if a.find("a:name", ns) is not None and a.find("a:name", ns).text
        ]
        articles.append(
            Article(
                title=title.strip().replace("\n", " ") if title else "Untitled",
                link=link,
                summary=summary.strip() if summary else "",
                published=published[:10] if published else "",
                authors=authors,
                feed_name=feed_name,
            )
        )
    return articles


def _parse_rss(root: ET.Element, feed_name: str) -> List[Article]:
    articles: List[Article] = []
    channel = root.find("channel")
    if channel is None:
        channel = root
    for item in channel.findall("item"):
        title = _text(item, "title", {})
        link = _text(item, "link", {})
        summary = _text(item, "description", {})
        pubdate = _text(item, "pubDate", {})
        # Atom extension inside RSS
        if not pubdate:
            pubdate = _text(item, "{http://www.w3.org/2005/Atom}updated", {})
        articles.append(
            Article(
                title=title.strip().replace("\n", " ") if title else "Untitled",
                link=link,
                summary=summary.strip() if summary else "",
                published=pubdate[:10] if pubdate else "",
                authors=[],
                feed_name=feed_name,
            )
        )
    return articles


def _text(el: Optional[ET.Element], tag: str, ns: dict) -> str:
    if el is None:
        return ""
    child = el.find(tag, ns)
    if child is not None and child.text:
        return child.text
    return ""


def _ns_tag(prefix: str, tag: str) -> str:
    return "{" + _NS_MAP.get(prefix, "") + "}" + tag
