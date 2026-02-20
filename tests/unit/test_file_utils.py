"""Unit tests for file utility functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.lib.file_utils import (
    create_timestamped_dir,
    ensure_dir,
    read_file,
    relative_path,
)


class TestCreateTimestampedDir:
    def test_creates_directory(self, tmp_path: Path) -> None:
        base = tmp_path / "output"
        base.mkdir()
        result = create_timestamped_dir(base)
        assert result.exists()
        assert result.is_dir()

    def test_directory_name_contains_timestamp(self, tmp_path: Path) -> None:
        base = tmp_path / "output"
        base.mkdir()
        result = create_timestamped_dir(base)
        # Timestamp format YYYY-MM-DD_HH-MM-SS
        name = result.name
        assert len(name) >= 19
        assert name[4] == "-"
        assert name[7] == "-"

    def test_with_prefix(self, tmp_path: Path) -> None:
        base = tmp_path / "output"
        base.mkdir()
        result = create_timestamped_dir(base, prefix="run-")
        assert result.name.startswith("run-")

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        base = tmp_path / "deep" / "nested" / "output"
        result = create_timestamped_dir(base)
        assert result.exists()

    def test_returns_path_object(self, tmp_path: Path) -> None:
        base = tmp_path / "output"
        result = create_timestamped_dir(base)
        assert isinstance(result, Path)


class TestEnsureDir:
    def test_creates_new_dir(self, tmp_path: Path) -> None:
        target = tmp_path / "newdir"
        result = ensure_dir(target)
        assert target.exists()
        assert target.is_dir()
        assert result == target

    def test_no_error_on_existing(self, tmp_path: Path) -> None:
        target = tmp_path / "existing"
        target.mkdir()
        result = ensure_dir(target)
        assert result == target

    def test_creates_nested_dirs(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c"
        ensure_dir(target)
        assert target.exists()

    def test_accepts_string(self, tmp_path: Path) -> None:
        target = str(tmp_path / "strpath")
        result = ensure_dir(target)
        assert isinstance(result, Path)
        assert result.exists()


class TestRelativePath:
    def test_relative_under_base(self, tmp_path: Path) -> None:
        base = tmp_path
        path = tmp_path / "reports" / "report.json"
        result = relative_path(path, base)
        assert result == "reports/report.json"

    def test_falls_back_to_absolute(self, tmp_path: Path) -> None:
        base = Path("/some/other/dir")
        path = tmp_path / "file.txt"
        result = relative_path(path, base)
        assert str(path) in result

    def test_returns_string(self, tmp_path: Path) -> None:
        result = relative_path(tmp_path / "x.txt", tmp_path)
        assert isinstance(result, str)


class TestReadFile:
    def test_reads_content(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        assert read_file(f) == "hello world"

    def test_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            read_file(tmp_path / "nonexistent.txt")

    def test_reads_utf8(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("héllo wörld", encoding="utf-8")
        assert read_file(f) == "héllo wörld"
