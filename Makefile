# Install targets use $(PIP) (default: python3 -m pip), not uv, so wheels go to that interpreter.
.PHONY: help install install-dev build uninstall clean format lint test check

PYTHON ?= python3
PIP = $(PYTHON) -m pip

help:
	@echo "openrouter-usage — common targets"
	@echo ""
	@echo "  make build         - sdist + wheel into dist/ (needs: $(PIP) install build)"
	@echo "  make install       - rebuild wheel, uninstall, then pip install dist/*.whl (global pip)"
	@echo "  make install-dev   - pip install -e \".[dev]\" (editable + dev tools)"
	@echo "  make uninstall     - pip uninstall openrouter-usage"
	@echo "  make clean         - remove build artifacts"
	@echo ""
	@echo "  make format        - ruff format (uses PYTHON make variable)"
	@echo "  make lint          - ruff check"
	@echo "  make test          - pytest"
	@echo "  make check         - lint + test"
	@echo ""
	@echo "Variables: PYTHON=python3.12  PIP=...  override as needed."

install: build uninstall
	@echo "Installing built wheel with $(PIP) (not uv)..."
	$(PIP) install dist/*.whl

install-dev: uninstall
	@echo "Editable install with dev extras..."
	$(PIP) install -e ".[dev]"

build: clean
	@echo "Building distribution..."
	$(PYTHON) -m build

uninstall:
	@echo "Uninstalling openrouter-usage..."
	-$(PIP) uninstall -y openrouter-usage

clean:
	rm -rf build dist *.egg-info openrouter_usage.egg-info
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest

check: lint test
