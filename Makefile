.PHONY: install test clean build lint fmt upload

PYTHON ?= python3
VENV   ?= .venv
BIN    ?= $(VENV)/bin

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -e .
	$(BIN)/pip install build twine

test:
	PYTHONPATH=. $(PYTHON) -m unittest discover -s tests -v

clean:
	rm -rf build/ dist/ *.egg-info/ .venv/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	$(PYTHON) -m build

lint:
	$(BIN)/python -m py_compile research_digest/*.py tests/*.py

upload:
	$(BIN)/twine upload dist/*

rotate-digests:
	$(BIN)/python scripts/rotate_digests.py --keep-days 3 --archive-dir digests/archive/

rotate-reports:
	$(BIN)/python scripts/rotate_reports.py --keep-days 30 --archive-dir ~/.hermes/cron/output/archive/

status:
	@echo "=== research-digest status ==="
	@echo "Version:  $$(git describe --tags --always 2>/dev/null || echo 'no-tag')"
	@echo "Branch:   $$(git rev-parse --abbrev-ref HEAD)"
	@echo "Commits:  $$(git log --oneline -5)"
	@echo "Tests:    $$(PYTHONPATH=. $(PYTHON) -m unittest discover -s tests 2>&1 | grep -E 'Ran [0-9]+ tests' || echo 'unknown')"
	@echo "Health:   $$(cat health_report.json 2>/dev/null | head -5 || echo 'N/A')"
