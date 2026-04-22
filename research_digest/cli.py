"""Main CLI for research-digest."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure package on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research_digest.arxiv_client import fetch_papers
from research_digest.rss_client import fetch_feed
from research_digest.summarizer import summarize_paper, summarize_article
from research_digest.digest import render_digest, save_digest


def load_config(path: str) -> dict:
    p = Path(path)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
    else:
        data = default_config()
    return data


def default_config() -> dict:
    return {
        "arxiv": {
            "query": "cat:cs.CL",
            "max_results": 5,
            "sort_by": "submittedDate",
            "sort_order": "descending",
        },
        "feeds": [
            {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
            {"name": "Google AI Blog", "url": "https://ai.googleblog.com/feeds/posts/default"},
            {"name": "Distill", "url": "https://distill.pub/rss.xml"},
        ],
        "output": {
            "directory": str(Path.home() / "workspace/research-digest/digests"),
            "filename": "digest_{date}.md",
        },
        "summarizer": {
            "model": "llama3.2:latest",
            "enabled": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="research-digest",
        description="Generate curated research digests from arXiv and RSS feeds.",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=str(Path.home() / ".config/research-digest/config.json"),
        help="Path to JSON config file",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="",
        help="Override output directory",
    )
    parser.add_argument(
        "--no-summarize",
        action="store_true",
        help="Skip LLM summarization (faster, raw abstracts only)",
    )
    parser.add_argument(
        "--arxiv-query",
        "-q",
        default="",
        help="Override arXiv search query",
    )
    parser.add_argument(
        "--max-results",
        "-n",
        type=int,
        default=0,
        help="Override max arXiv results",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="",
        help="Override Ollama model name",
    )
    parser.add_argument(
        "--feeds-only",
        action="store_true",
        help="Skip arXiv, only poll RSS feeds",
    )
    parser.add_argument(
        "--arxiv-only",
        action="store_true",
        help="Skip RSS feeds, only fetch arXiv",
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date stamp for digest filename",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    summarizer_enabled = cfg.get("summarizer", {}).get("enabled", True) and not args.no_summarize
    model = args.model or cfg.get("summarizer", {}).get("model", "llama3.2:latest")

    # Fetch arXiv papers
    papers = []
    if not args.feeds_only:
        aq = args.arxiv_query or cfg["arxiv"]["query"]
        n = args.max_results or cfg["arxiv"]["max_results"]
        sort_by = cfg["arxiv"]["sort_by"]
        sort_order = cfg["arxiv"]["sort_order"]
        print(f"Fetching arXiv: {aq} (max {n}) ...", file=sys.stderr)
        try:
            papers = fetch_papers(aq, n, sort_by, sort_order)
            print(f"  → {len(papers)} papers", file=sys.stderr)
        except Exception as e:
            print(f"  ✗ arXiv fetch failed: {e}", file=sys.stderr)

    # Fetch RSS feeds
    articles = []
    if not args.arxiv_only:
        for feed in cfg.get("feeds", []):
            name = feed.get("name", "RSS")
            url = feed.get("url", "")
            if not url:
                continue
            print(f"Fetching RSS: {name} ...", file=sys.stderr)
            try:
                arts = fetch_feed(url, name)
                print(f"  → {len(arts)} articles", file=sys.stderr)
                articles.extend(arts)
            except Exception as e:
                print(f"  ✗ RSS fetch failed: {e}", file=sys.stderr)

    # Summarize
    paper_summaries = []
    article_summaries = []
    if summarizer_enabled:
        for p in papers:
            try:
                s = summarize_paper(p.title, p.summary, model=model)
                paper_summaries.append(s)
            except Exception as e:
                print(f"  ✗ Summarize paper failed: {e}", file=sys.stderr)
                from research_digest.summarizer import Summary
                paper_summaries.append(
                    Summary(headline=p.title, key_points=[p.summary[:200]], relevance="See abstract.")
                )
        for a in articles:
            try:
                s = summarize_article(a.title, a.summary, model=model)
                article_summaries.append(s)
            except Exception as e:
                print(f"  ✗ Summarize article failed: {e}", file=sys.stderr)
                from research_digest.summarizer import Summary
                article_summaries.append(
                    Summary(headline=a.title, key_points=[a.summary[:200]], relevance="See article.")
                )
    else:
        from research_digest.summarizer import Summary
        for p in papers:
            paper_summaries.append(
                Summary(headline=p.title, key_points=[p.summary[:200]], relevance="See abstract.")
            )
        for a in articles:
            article_summaries.append(
                Summary(headline=a.title, key_points=[a.summary[:200]], relevance="See article.")
            )

    # Render & save
    md = render_digest(papers, articles, paper_summaries, article_summaries, date=args.date)
    out_dir = Path(args.output or cfg["output"]["directory"])
    fname = cfg["output"]["filename"].format(date=args.date)
    out_path = out_dir / fname
    try:
        save_digest(md, out_path)
        print(f"\nDigest written to {out_path}", file=sys.stderr)
    except Exception as e:
        print(f"\nFailed to write digest: {e}", file=sys.stderr)
        print(md)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
