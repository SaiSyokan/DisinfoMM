.PHONY: install test lint

install:
	python -m pip install -e '.[dev]'

test:
	python -m pytest -q

lint:
	python -m ruff check src tests
