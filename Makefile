.PHONY: install test lint typecheck check help

help:
	@echo "Targets:"
	@echo "  install    Install package in editable mode with dev dependencies"
	@echo "  test       Run pytest"
	@echo "  lint       Run ruff"
	@echo "  typecheck  Run mypy"
	@echo "  check      Run lint, typecheck, and tests"

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy src

check: lint typecheck test

