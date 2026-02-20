"""File utilities for the Playwright QA Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def create_timestamped_dir(base_dir: Path | str, prefix: str = "") -> Path:
    """Create a timestamped output directory.

    Args:
        base_dir: Parent directory under which to create the new directory.
        prefix: Optional prefix for the directory name.

    Returns:
        Path to the newly created directory.
    """
    base_dir = Path(base_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    dir_name = f"{prefix}{timestamp}" if prefix else timestamp
    output_dir = base_dir / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def create_latest_symlink(target: Path, link_name: str = "latest") -> Optional[Path]:
    """Create or update a 'latest' symlink pointing to the given directory.

    Args:
        target: Directory to link to.
        link_name: Name of the symlink (default: "latest").

    Returns:
        Path to the symlink, or None if symlinks are not supported.
    """
    try:
        link = target.parent / link_name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(target.name)
        return link
    except (OSError, NotImplementedError):
        # Symlinks may not be supported on all platforms/filesystems
        return None


def ensure_dir(path: Path | str) -> Path:
    """Ensure a directory exists, creating it and parents if necessary.

    Args:
        path: Directory path to create.

    Returns:
        Path to the directory.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def relative_path(path: Path | str, base: Path | str) -> str:
    """Return a relative path string from base to path.

    Falls back to absolute path string if path is not relative to base.

    Args:
        path: Target path.
        base: Base directory.

    Returns:
        Relative path string, or absolute path string if not under base.
    """
    path = Path(path)
    base = Path(base)
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def read_file(path: Path | str) -> str:
    """Read file content as a string.

    Args:
        path: File path to read.

    Returns:
        File content as string.

    Raises:
        FileNotFoundError: If file does not exist.
        PermissionError: If file cannot be read.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Requirements file '{path}' not found. "
            "Please provide a valid .txt or .md file."
        )
    if not path.is_file():
        raise ValueError(f"'{path}' is not a file.")
    return path.read_text(encoding="utf-8")


def get_environment_info() -> dict:
    """Collect current environment information.

    Returns:
        Dictionary with Python version, platform, and other info.
    """
    import platform
    import sys

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            pw_version = p.chromium.name  # just to check it works
        pw_version = "installed"
    except Exception:
        pw_version = "unknown"

    return {
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "platform_version": platform.version(),
        "playwright_version": pw_version,
    }
