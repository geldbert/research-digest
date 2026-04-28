# research-digest 🦑

Generate curated research digests from **arXiv** and **RSS feeds** using only Python's standard library.

## Features

- **arXiv search** — Query any arXiv category or keyword; fetch latest papers via the free REST API.
- **RSS/Atom feeds** — Poll any number of feeds and aggregate articles.
- **Local LLM summaries** — Optional summarization via [Ollama](https://ollama.com/) (zero external API keys).
- **Web search** — Optional DuckDuckGo web search (zero API keys).
- **Pure stdlib** — No pip dependencies beyond Python itself.
- **Markdown output** — Clean, shareable `.md` files.

## Install

```bash
git clone https://github.com/geldbert/research-digest.git
cd research-digest
pip install -e .
```

Or run directly without installing:

```bash
python -m research_digest.cli --help
```

## Quick Start

```bash
# Fetch latest cs.CL papers + summarize with Ollama
research-digest --arxiv-only -n 5

# Fetch only RSS feeds
research-digest --feeds-only

# Skip LLM summarization (fast, raw abstracts only)
research-digest --no-summarize -n 10
```

## Configuration

Create `~/.config/research-digest/config.json`:

```json
{
  "arxiv": {
    "query": "cat:cs.CL",
    "max_results": 5,
    "sort_by": "submittedDate",
    "sort_order": "descending"
  },
  "feeds": [
    {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml"},
    {"name": "Distill", "url": "https://distill.pub/rss.xml"}
  ],
  "output": {
    "directory": "~/digests",
    "filename": "digest_{date}.md"
  },
  "summarizer": {
    "model": "kimi-k2.6:cloud",
    "enabled": true
  }
}
```

## CLI Options

```bash
research-digest [-c CONFIG] [-o DIR] [-q QUERY] [-n N]
                [--no-summarize] [--feeds-only] [--arxiv-only]
                [--web-search] [--web-query QUERY] [--web-results N]
                [-m MODEL] [--date DATE] [--version]
```

| Flag | Description |
|------|-------------|
| `-c, --config` | Path to JSON config |
| `-o, --output` | Override output directory |
| `-q, --arxiv-query` | Override arXiv search query |
| `-n, --max-results` | Max arXiv results |
| `--no-summarize` | Skip LLM (raw abstracts) |
| `--feeds-only` | Skip arXiv, RSS only |
| `--arxiv-only` | Skip RSS, arXiv only |
| `--web-search` | Include DuckDuckGo web results |
| `--web-query` | Override search query |
| `--web-results` | Max web results |
| `-m, --model` | Ollama model name |
| `--date` | Date stamp for filename |
| `--version` | Show version |

## Requirements

- Python ≥ 3.10
- (Optional) Ollama running on `localhost:11434` for summarization

## Related Projects

- **[RustChain](https://github.com/Scottcjn/Rustchain)** — Proof-of-Antiquity blockchain that rewards older hardware, creating sustainable on-chain incentives for vintage computing hardware.

## License

MIT — see [LICENSE](./LICENSE).
