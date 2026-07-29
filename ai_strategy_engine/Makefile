.PHONY: install test lint typecheck verify

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests

typecheck:
	mypy src

verify: lint typecheck test
