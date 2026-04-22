# Changelog

## 0.1.1 — 2026-04-22
### Fixed
- README default feed URL corrected to `https://openai.com/news/rss.xml`
- README default model corrected to `kimi-k2.6:cloud`
- Added missing `urllib.parse` import in `arxiv_client.py`
- Version synced across `__init__.py`, `pyproject.toml`, and `setup.py`

### Added
- GitHub Actions CI workflow (`python3.11`–`3.14`)
- `__main__.py` entry point for `python -m research_digest`

## 0.1.0 — 2026-04-21
### Added
- Initial release
- arXiv search via Atom XML / REST API (stdlib only)
- RSS/Atom feed polling
- Optional local LLM summarization via Ollama
- Markdown digest generation
- CLI with argparse (`--arxiv-only`, `--feeds-only`, `--no-summarize`, etc.)
- 7 unit tests
