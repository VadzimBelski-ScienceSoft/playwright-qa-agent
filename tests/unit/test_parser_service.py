"""Unit tests for parser service."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.parser_service import ParserService, parse_markdown, parse_plain_text


class TestParsePlainText:
    def test_simple_numbered_list(self) -> None:
        content = "1. User can login with valid credentials\n2. Dashboard shows statistics"
        reqs = parse_plain_text(content)
        assert len(reqs) == 2
        assert reqs[0].id == "REQ-001"
        assert reqs[1].id == "REQ-002"

    def test_with_given_when_then(self) -> None:
        content = (
            "1. User login\n"
            "- Given: User is on login page\n"
            "- When: User enters credentials\n"
            "- Then: User is redirected to dashboard"
        )
        reqs = parse_plain_text(content)
        assert len(reqs) == 1
        assert reqs[0].given == "User is on login page"
        assert reqs[0].when == "User enters credentials"
        assert reqs[0].then == "User is redirected to dashboard"

    def test_empty_content(self) -> None:
        reqs = parse_plain_text("")
        assert reqs == []

    def test_generates_sequential_ids(self) -> None:
        content = "1. First\n2. Second\n3. Third"
        reqs = parse_plain_text(content)
        assert [r.id for r in reqs] == ["REQ-001", "REQ-002", "REQ-003"]

    def test_title_from_description(self) -> None:
        content = "1. This is a requirement about user authentication"
        reqs = parse_plain_text(content)
        assert reqs[0].title != ""


class TestParseMarkdown:
    def test_section_headers(self) -> None:
        content = (
            "## REQ-001: User Login\n"
            "User can login with valid credentials.\n\n"
            "## REQ-002: Dashboard\n"
            "Dashboard shows user statistics."
        )
        reqs = parse_markdown(content)
        assert len(reqs) == 2
        assert reqs[0].id == "REQ-001"
        assert reqs[0].title == "User Login"
        assert reqs[1].id == "REQ-002"

    def test_with_gwt_in_markdown(self) -> None:
        content = (
            "## REQ-001: User Login\n"
            "**Given**: User is on login page\n"
            "**When**: User enters credentials\n"
            "**Then**: User is redirected"
        )
        reqs = parse_markdown(content)
        assert len(reqs) == 1
        assert reqs[0].given == "User is on login page"

    def test_falls_back_to_numbered_list(self) -> None:
        content = "1. Login works\n2. Dashboard loads"
        reqs = parse_markdown(content)
        assert len(reqs) == 2

    def test_empty_content(self) -> None:
        reqs = parse_markdown("")
        assert reqs == []


class TestParserService:
    def test_parse_txt_file(self, tmp_path: Path) -> None:
        f = tmp_path / "reqs.txt"
        f.write_text("1. User can login\n2. Dashboard works")
        svc = ParserService()
        doc = svc.parse_requirements(f)
        assert doc.format == "txt"
        assert len(doc.requirements) == 2
        assert doc.file_path == f

    def test_parse_md_file(self, tmp_path: Path) -> None:
        f = tmp_path / "reqs.md"
        f.write_text("## REQ-001: Login\nUser can login.")
        svc = ParserService()
        doc = svc.parse_requirements(f)
        assert doc.format == "md"
        assert len(doc.requirements) == 1

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "reqs.pdf"
        f.write_text("content")
        svc = ParserService()
        with pytest.raises(ValueError, match="Unsupported"):
            svc.parse_requirements(f)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        svc = ParserService()
        with pytest.raises(FileNotFoundError):
            svc.parse_requirements(tmp_path / "nonexistent.txt")

    def test_raw_content_preserved(self, tmp_path: Path) -> None:
        content = "1. Requirement one\n2. Requirement two"
        f = tmp_path / "reqs.txt"
        f.write_text(content)
        svc = ParserService()
        doc = svc.parse_requirements(f)
        assert doc.raw_content == content
