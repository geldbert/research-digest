# Changelog

## [0.1.5] — 2026-04-24
### Fixed
- CHANGELOG deduplicated and corrected ordering

### Maintenance
- Sprint Mode Phase 5 cadence cycle: version bump + rebuild verified

## [0.1.4] — 2026-04-24
### Added
- `health_check.py` script — grade-A system smoke test (arXiv, feeds, Ollama, tests)
- HTTP 405 GET fallback for feed health checks (RSS endpoints that reject HEAD)
- Hacker News official RSS endpoint (replaces deprecated hnrss)
- `tests/test_health_check.py` — mocked health-check suite
- Auto-cap `max_articles_per_feed` (default 15) to prevent digest bloat

### Changed
- Default Ollama model: `kimi-k2.6:cloud` (discovered via `/api/tags` at runtime)
- Sprint Mode documentation in cycle framework (reconnect every cycle, P5/P7 every 5)

### Fixed
- Google Research Blog feed URL updated to stable feedburner endpoint (avoids 302 loop)
- RSS date normalization: RFC 2822 → YYYY-MM-DD (prevents truncated dates in digest)

## [0.1.3] — 2026-04-23
### Fixed
- Normalize RSS/Atom article dates to YYYY-MM-DD
- Verified wheel and sdist build pipeline; all tests pass with stdlib only

## [0.1.2] — 2026-04-22
### Fixed
- README default model corrected to `kimi-k2.6:cloud`
- Added missing `urllib.parse` import in `arxiv_client.py`
- Version synced across `__init__.py`, `pyproject.toml`, and `setup.py`

### Added
- GitHub Actions CI workflow (`python3.11`–`3.14`)
- `__main__.py` entry point for `python -m research_digest`

## [0.1.0] — 2026-04-21
### Added
- Initial release
- arXiv search via Atom XML / REST API (stdlib only)
- RSS/Atom feed polling with `urllib`
- Optional local LLM summarization via Ollama `/api/chat`
- Markdown digest generation
- CLI with argparse (`--arxiv-only`, `--feeds-only`, `--no-summarize`, etc.)
- Comprehensive test suite (15 tests, stdlib only, all mocked — no network deps)
