.PHONY: help test test-verbose test-coverage benchmark-small benchmark benchmark-large clean install dev-install format lint venv

PYTHON := ./env/bin/python3
PIP := $(PYTHON) -m pip

help:
	@echo "Available targets:"
	@echo "  make test             - Run all tests"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make benchmark-small  - Run small benchmark suite (fast)"
	@echo "  make benchmark        - Run medium benchmark suite (default)"
	@echo "  make benchmark-large  - Run large benchmark suite (comprehensive)"
	@echo "  make install          - Install dependencies"
	@echo "  make dev-install      - Install development dependencies"
	@echo "  make clean            - Clean up generated files"
	@echo "  make venv             - Create virtual environment"

venv:
	@if [ ! -d "./env" ]; then \
		python3 -m venv ./env; \
		echo "Virtual environment created at ./env"; \
	else \
		echo "Virtual environment already exists"; \
	fi

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install pytest

dev-install: install
	$(PIP) install pytest-cov black isort mypy

test:
	$(PYTHON) -m pytest hamt/__tests__/

test-verbose:
	$(PYTHON) -m pytest -v hamt/__tests__/

test-coverage:
	$(PYTHON) -m pytest --cov=hamt --cov-report=term-missing --cov-report=html hamt/__tests__/
	@echo "Coverage report generated in htmlcov/index.html"

benchmark-small:
	$(PYTHON) tools/benchmark_hamt.py --size small

benchmark:
	$(PYTHON) tools/benchmark_hamt.py --size medium

benchmark-large:
	$(PYTHON) tools/benchmark_hamt.py --size large

format:
	$(PYTHON) -m black hamt/ tools/
	$(PYTHON) -m isort hamt/ tools/

lint:
	$(PYTHON) -m black --check hamt/ tools/
	$(PYTHON) -m isort --check-only hamt/ tools/
	$(PYTHON) -m mypy hamt/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
