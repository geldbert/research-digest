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
