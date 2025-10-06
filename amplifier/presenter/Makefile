.PHONY: install test lint format check clean dev setup

# Install production dependencies
install:
	uv sync

# Install development dependencies
dev:
	uv sync --all-extras

# Run all tests
test:
	uv run pytest

# Run unit tests only
test-unit:
	uv run pytest -m unit

# Run integration tests only
test-integration:
	uv run pytest -m integration

# Run tests with coverage
test-cov:
	uv run pytest --cov=presenter --cov-report=html --cov-report=term

# Run linting
lint:
	uv run ruff check presenter tests

# Format code
format:
	uv run black presenter tests
	uv run ruff check --fix presenter tests

# Run type checking
type:
	uv run mypy presenter

# Run all checks (lint, format, type, test)
check: lint type test

# Clean up generated files
clean:
	rm -rf dist build *.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf **/__pycache__ **/*.pyc
	rm -rf data/presentations/* data/assets/cache/*

# Setup development environment
setup: dev
	mkdir -p data/presentations data/assets data/themes data/assets/cache
	mkdir -p tests/fixtures/sample_outlines
	@echo "Development environment ready!"

# Quick test during development
quick:
	uv run pytest tests/test_parser.py -v

# Run specific test
test-one:
	@echo "Usage: make test-one TEST=tests/test_parser.py::test_parse_simple"
	uv run pytest $(TEST) -v

# Watch tests (requires pytest-watch)
watch:
	uv run ptw -- -v