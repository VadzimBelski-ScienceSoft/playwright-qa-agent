.PHONY: install install-browsers install-browsers-deps setup verify lint test clean

# Install Python dependencies using UV
install:
	uv sync

# Install dev dependencies (pytest, ruff)
install-dev:
	uv sync --extra dev

# Install Playwright browser binaries (Chromium, Firefox, WebKit)
install-browsers:
	uv run playwright install

# Install Playwright browsers with system dependencies (recommended for Linux CI)
install-browsers-deps:
	uv run playwright install --with-deps

# Full project setup: installs Python deps and browser binaries
# On Linux, automatically installs system dependencies
setup: install
	@if [ "$$(uname -s)" = "Linux" ]; then \
		echo "Linux detected - installing browsers with system dependencies..."; \
		uv run playwright install --with-deps; \
	else \
		echo "Installing browser binaries (Chromium, Firefox, WebKit)..."; \
		uv run playwright install; \
	fi
	@echo "Setup complete."

# Verify Playwright installation
verify:
	uv run playwright --version
	@echo "Playwright installation verified."

# Run linting
lint:
	uv run ruff check .

# Run tests
test:
	uv run pytest

# Remove build artifacts and virtual environment
clean:
	rm -rf .venv __pycache__ .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
