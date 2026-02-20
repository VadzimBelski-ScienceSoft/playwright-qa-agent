#!/usr/bin/env bash
# Install Playwright browser binaries with cross-platform support
#
# Usage:
#   ./scripts/install_browsers.sh           # Auto-detect platform
#   ./scripts/install_browsers.sh --with-deps  # Force install system deps (Linux)
#
# Browsers installed: Chromium, Firefox, WebKit

set -euo pipefail

WITH_DEPS=false

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --with-deps)
            WITH_DEPS=true
            ;;
        --help|-h)
            echo "Usage: $0 [--with-deps]"
            echo ""
            echo "Options:"
            echo "  --with-deps    Install system dependencies (Linux only)"
            echo "  --help         Show this help message"
            exit 0
            ;;
    esac
done

echo "Installing Playwright browser binaries (Chromium, Firefox, WebKit)..."

OS="$(uname -s 2>/dev/null || echo 'Unknown')"

if [[ "$WITH_DEPS" == "true" ]] || [[ "$OS" == "Linux" ]]; then
    echo "Installing browsers with system dependencies..."
    playwright install --with-deps
else
    playwright install
fi

echo ""
echo "Verifying installation..."
playwright --version

echo ""
echo "Browser installation complete."
echo "Cache directory: $HOME/.cache/ms-playwright (Linux/macOS) or %USERPROFILE%\\AppData\\Local\\ms-playwright (Windows)"
