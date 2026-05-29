.PHONY: help test lint typecheck quality verification docs-build docs-serve

help:
	@echo "Targets:"
	@echo "  test         - run pytest"
	@echo "  lint         - run ruff"
	@echo "  typecheck    - run mypy"
	@echo "  quality      - run lint, typecheck, and test"
	@echo "  verification - alias for quality (schema + pytest gate)"
	@echo "  docs-build   - build MkDocs site"
	@echo "  docs-serve   - serve MkDocs site locally"

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy host/m5resolver

quality: lint typecheck test

verification: quality

docs-build:
	mkdocs build

docs-serve:
	mkdocs serve
