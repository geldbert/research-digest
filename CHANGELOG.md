# Changelog

## [0.1.3] - 2026-04-23
### Fixed
- Normalize RSS/Atom article dates to YYYY-MM-DD (was rendering truncated RFC 2822 dates like "Thu, 23 Ap")
### Infrastructure
- Verified wheel and sdist build pipeline; all 11 tests pass with stdlib only

## [0.1.2] - 2026-04-22
### Fixed
- Google Research RSS feed URL updated to stable feedburner endpoint (avoids 302 redirect loop)
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

## [0.1.3] - 2026-04-23
### Fixed
- Normalize RSS/Atom article dates to YYYY-MM-DD
- Build verified: wheel + sdist OK
