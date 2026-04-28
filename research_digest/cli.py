"""Main CLI for research-digest."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure package on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research_digest.arxiv_client import fetch_papers
from research_digest.rss_client import fetch_feed
from research_digest.web_search import fetch_web_results
from research_digest.summarizer import summarize_paper, summarize_article, summarize_web_result
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
            {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml"},
            {"name": "Google Research", "url": "http://feeds.feedburner.com/blogspot/gJZg"},
            {"name": "HN Newest", "url": "https://news.ycombinator.com/rss"},
        ],
        "feed_limits": {
            "max_articles_per_feed": 15,
        },
        "output": {
            "directory": str(Path.home() / "workspace/research-digest/digests"),
            "filename": "digest_{date}.md",
        },
        "summarizer": {
            "model": "llama3.2:latest",
            "enabled": True,
        },
        "web_search": {
            "enabled": False,
            "query": "latest AI research 2026",
            "max_results": 5,
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
        "--web-search",
        action="store_true",
        help="Include web search results (DDGS)",
    )
    parser.add_argument(
        "--web-query",
        default="",
        help="Override web search query",
    )
    parser.add_argument(
        "--web-results",
        type=int,
        default=0,
        help="Override max web results",
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
        version=f"%(prog)s {__import__('research_digest').__version__}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render and print digest to stdout without writing to file",
    )
    parser.add_argument(
        "--quiet",
        "-Q",
        action="store_true",
        help="Suppress all progress output",
    )
    args = parser.parse_args(argv)

    def _log(msg: str) -> None:
        if not args.quiet:
            print(msg, file=sys.stderr)

    cfg = load_config(args.config)
    summarizer_enabled = cfg.get("summarizer", {}).get("enabled", True) and not args.no_summarize
    model = args.model or cfg.get("summarizer", {}).get("model", "kimi-k2.6:cloud")

    # Fetch arXiv papers
    papers = []
    if not args.feeds_only:
        aq = args.arxiv_query or cfg["arxiv"]["query"]
        n = args.max_results or cfg["arxiv"]["max_results"]
        sort_by = cfg["arxiv"]["sort_by"]
        sort_order = cfg["arxiv"]["sort_order"]
        _log(f"Fetching arXiv: {aq} (max {n}) ...")
        try:
            papers = fetch_papers(aq, n, sort_by, sort_order)
            _log(f"  → {len(papers)} papers")
        except Exception as e:
            _log(f"  ✗ arXiv fetch failed: {e}")

    # Fetch RSS feeds
    articles = []
    if not args.arxiv_only:
        for feed in cfg.get("feeds", []):
            name = feed.get("name", "RSS")
            url = feed.get("url", "")
            if not url:
                continue
            _log(f"Fetching RSS: {name} ...")
            try:
                arts = fetch_feed(url, name)
                max_arts = cfg.get("feed_limits", {}).get("max_articles_per_feed")
                if max_arts is not None and len(arts) > max_arts:
                    arts = arts[:max_arts]
                _log(f"  → {len(arts)} articles")
                articles.extend(arts)
            except Exception as e:
                _log(f"  ✗ RSS fetch failed: {e}")

    # Fetch web search
    web_results = []
    if args.web_search or cfg.get("web_search", {}).get("enabled", False):
        wq = args.web_query or cfg.get("web_search", {}).get("query", "latest AI research 2026")
        wr = args.web_results or cfg.get("web_search", {}).get("max_results", 5)
        _log(f"Fetching web: {wq} (max {wr}) ...")
        try:
            web_results = fetch_web_results(wq, wr)
            _log(f"  → {len(web_results)} results")
        except Exception as e:
            _log(f"  ✗ Web search failed: {e}")

    # Summarize
    paper_summaries = []
    article_summaries = []
    web_summaries = []
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
        for w in web_results:
            try:
                s = summarize_web_result(w.title, w.body, model=model)
                web_summaries.append(s)
            except Exception as e:
                print(f"  ✗ Summarize web result failed: {e}", file=sys.stderr)
                from research_digest.summarizer import Summary
                web_summaries.append(
                    Summary(headline=w.title, key_points=[w.body[:200]], relevance="See source.")
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
        for w in web_results:
            web_summaries.append(
                Summary(headline=w.title, key_points=[w.body[:200]], relevance="See source.")
            )

    # Render & save
    md = render_digest(papers, articles, web_results, paper_summaries, article_summaries, web_summaries, date=args.date)
    out_dir = Path(args.output or cfg["output"]["directory"])
    fname = cfg["output"]["filename"].format(date=args.date)
    out_path = out_dir / fname
    if args.dry_run:
        _log(f"\nDigest (dry-run, would write to {out_path}):")
        print(md)
        return 0
    try:
        save_digest(md, out_path)
        _log(f"\nDigest written to {out_path}")
    except Exception as e:
        _log(f"\nFailed to write digest: {e}")
        print(md)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
