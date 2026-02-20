"""Integration test for the full Playwright QA Agent workflow.

Tests the end-to-end pipeline without requiring a live web application:
- Requirements parsing (both .txt and .md formats)
- Report generation (JSON, JUnit XML, HTML)
- CLI argument parsing and validation
- Model serialization round-trips
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Sample requirements documents
# ---------------------------------------------------------------------------

PLAIN_TEXT_REQUIREMENTS = """\
1. **Login**: User can log in with valid credentials
   - Given: User is on the login page
   - When: User enters valid username and password
   - Then: User is redirected to the dashboard

2. **Dashboard**: Dashboard shows the user name after login
   - Given: User is logged in
   - When: User views the dashboard
   - Then: The page displays the user name

3. User can log out
   - Given: User is logged in
   - When: User clicks the Logout button
   - Then: User is returned to the login page
"""

MARKDOWN_REQUIREMENTS = """\
## REQ-001: User Authentication

User can log in with valid credentials.

**Given**: User is on the login page
**When**: User enters valid username and password and clicks Login
**Then**: User is redirected to the dashboard

## REQ-002: Dashboard Display

Dashboard shows the logged-in user's name.

**Given**: User is authenticated
**When**: User navigates to the dashboard
**Then**: The dashboard displays the user's full name

## REQ-003: Logout

User can securely log out.

**Given**: User is logged in
**When**: User clicks the Logout button
**Then**: Session is terminated and user returns to login page
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Provide a temporary output directory."""
    out = tmp_path / "test-results"
    out.mkdir()
    return out


@pytest.fixture
def txt_requirements_file(tmp_path: Path) -> Path:
    """Write and return a plain text requirements file."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text(PLAIN_TEXT_REQUIREMENTS, encoding="utf-8")
    return req_file


@pytest.fixture
def md_requirements_file(tmp_path: Path) -> Path:
    """Write and return a markdown requirements file."""
    req_file = tmp_path / "requirements.md"
    req_file.write_text(MARKDOWN_REQUIREMENTS, encoding="utf-8")
    return req_file


# ---------------------------------------------------------------------------
# Parser integration tests
# ---------------------------------------------------------------------------


class TestParserWorkflow:
    """Test the parsing phase of the workflow."""

    def test_parse_plain_text_requirements(self, txt_requirements_file: Path) -> None:
        from src.services.parser_service import ParserService

        svc = ParserService()
        doc = svc.parse_requirements(txt_requirements_file)

        assert doc.format == "txt"
        assert len(doc.requirements) == 3
        assert doc.requirements[0].id == "REQ-001"
        assert doc.requirements[0].title == "Login"
        assert "valid credentials" in doc.requirements[0].description
        assert "login page" in doc.requirements[0].given.lower()
        assert "valid username" in doc.requirements[0].when.lower()
        assert "dashboard" in doc.requirements[0].then.lower()

    def test_parse_markdown_requirements(self, md_requirements_file: Path) -> None:
        from src.services.parser_service import ParserService

        svc = ParserService()
        doc = svc.parse_requirements(md_requirements_file)

        assert doc.format == "md"
        assert len(doc.requirements) == 3
        assert doc.requirements[0].id == "REQ-001"
        assert "Authentication" in doc.requirements[0].title
        assert "login page" in doc.requirements[0].given.lower()

    def test_parse_all_requirements_have_ids(self, txt_requirements_file: Path) -> None:
        from src.services.parser_service import ParserService

        svc = ParserService()
        doc = svc.parse_requirements(txt_requirements_file)

        for req in doc.requirements:
            assert req.id.startswith("REQ-"), f"Expected REQ- prefix, got: {req.id}"
            assert req.number > 0

    def test_unsupported_format_raises_error(self, tmp_path: Path) -> None:
        from src.services.parser_service import ParserService

        bad_file = tmp_path / "requirements.csv"
        bad_file.write_text("col1,col2\nval1,val2")

        svc = ParserService()
        with pytest.raises(ValueError, match="Unsupported"):
            svc.parse_requirements(bad_file)

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        from src.services.parser_service import ParserService

        svc = ParserService()
        with pytest.raises(FileNotFoundError):
            svc.parse_requirements(tmp_path / "nonexistent.txt")


# ---------------------------------------------------------------------------
# Report generation integration tests
# ---------------------------------------------------------------------------


def _make_sample_results() -> list:
    """Create a list of sample VerificationResult objects."""
    from src.models.verification_result import VerificationResult

    return [
        VerificationResult(
            requirement_id="REQ-001",
            status="passed",
            duration=1.23,
            logs=["Navigated to login page", "Filled credentials", "Clicked submit"],
        ),
        VerificationResult(
            requirement_id="REQ-002",
            status="failed",
            duration=0.89,
            logs=["Navigated to dashboard"],
            error={"type": "AssertionError", "message": "User name not found on page"},
        ),
        VerificationResult(
            requirement_id="REQ-003",
            status="needs_clarification",
            duration=0.45,
            clarification_reason="Requirement is ambiguous: 'log out' could mean multiple actions",
            refinement_suggestion="Specify which logout button: top-nav 'Logout' or user-menu 'Sign out'",
        ),
    ]


class TestReportGeneration:
    """Test the report generation phase of the workflow."""

    def test_generate_json_report(self, tmp_output: Path) -> None:
        from src.models.test_report import TestReport
        from src.services.report_service import ReportService

        results = _make_sample_results()
        report = TestReport.from_results(
            session_id="test-session-001",
            duration=2.57,
            results=results,
            environment={"python_version": "3.11", "platform": "Linux"},
        )

        svc = ReportService()
        out_path = svc.generate_json_report(report, tmp_output / "report.json")

        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert data["session_id"] == "test-session-001"
        assert data["summary"]["total"] == 3
        assert data["summary"]["passed"] == 1
        assert data["summary"]["failed"] == 1
        assert data["summary"]["needs_clarification"] == 1
        assert len(data["results"]) == 3

    def test_generate_junit_xml(self, tmp_output: Path) -> None:
        from src.models.test_report import TestReport
        from src.services.report_service import ReportService

        results = _make_sample_results()
        report = TestReport.from_results(
            session_id="test-session-002",
            duration=2.57,
            results=results,
            environment={},
        )

        svc = ReportService()
        out_path = svc.generate_junit_xml(report, tmp_output / "junit.xml")

        assert out_path.exists()
        xml_content = out_path.read_text()
        assert "testsuites" in xml_content or "testsuite" in xml_content
        assert "REQ-001" in xml_content
        assert "REQ-002" in xml_content
        assert "REQ-003" in xml_content
        assert "failure" in xml_content.lower() or "failed" in xml_content.lower()

    def test_generate_html_report(self, tmp_output: Path) -> None:
        from src.models.test_report import TestReport
        from src.services.report_service import ReportService

        results = _make_sample_results()
        report = TestReport.from_results(
            session_id="test-session-003",
            duration=2.57,
            results=results,
            environment={},
        )

        svc = ReportService()
        out_path = svc.generate_html_report(report, tmp_output / "report.html")

        assert out_path.exists()
        html = out_path.read_text()
        assert "<!DOCTYPE html>" in html
        assert "REQ-001" in html
        assert "passed" in html
        assert "failed" in html
        assert "needs_clarification" in html

    def test_generate_all_formats(self, tmp_output: Path) -> None:
        from src.models.test_report import TestReport
        from src.services.report_service import ReportService

        results = _make_sample_results()
        report = TestReport.from_results(
            session_id="test-session-all",
            duration=2.57,
            results=results,
            environment={},
        )

        svc = ReportService()
        generated = svc.generate_all(report, tmp_output)

        assert "json" in generated
        assert "junit_xml" in generated
        assert "html" in generated
        assert Path(generated["json"]).exists()
        assert Path(generated["junit_xml"]).exists()
        assert Path(generated["html"]).exists()

    def test_json_report_round_trip(self, tmp_output: Path) -> None:
        """Verify JSON report can be deserialized back into a TestReport."""
        from src.models.test_report import TestReport
        from src.services.report_service import ReportService

        results = _make_sample_results()
        original = TestReport.from_results(
            session_id="round-trip-test",
            duration=1.5,
            results=results,
            environment={"platform": "Linux"},
        )

        svc = ReportService()
        out_path = svc.generate_json_report(original, tmp_output / "rt_report.json")

        data = json.loads(out_path.read_text())
        restored = TestReport.from_dict(data)

        assert restored.session_id == original.session_id
        assert restored.summary.total == original.summary.total
        assert restored.summary.passed == original.summary.passed
        assert len(restored.results) == len(original.results)


# ---------------------------------------------------------------------------
# CLI argument parsing integration tests
# ---------------------------------------------------------------------------


class TestCLIArgumentParsing:
    """Test the CLI argument parser."""

    def test_parser_shows_all_options(self) -> None:
        from src.cli.main import build_parser

        parser = build_parser()
        # Verify all critical arguments exist
        actions = {a.dest: a for a in parser._actions}
        assert "requirements_file" in actions
        assert "url" in actions
        assert "username" in actions
        assert "password" in actions
        assert "browser" in actions
        assert "headless" in actions
        assert "output" in actions
        assert "format" in actions
        assert "log_level" in actions
        assert "timeout" in actions

    def test_parse_basic_args(self, txt_requirements_file: Path) -> None:
        from src.cli.main import build_parser

        parser = build_parser()
        args = parser.parse_args([
            str(txt_requirements_file),
            "--url", "https://example.com",
            "--username", "user",
            "--password", "pass",
        ])

        assert args.url == "https://example.com"
        assert args.username == "user"
        assert args.password == "pass"
        assert args.browser == "chromium"
        assert args.headless is True

    def test_headed_flag(self, txt_requirements_file: Path) -> None:
        from src.cli.main import build_parser

        parser = build_parser()
        args = parser.parse_args([
            str(txt_requirements_file),
            "--url", "https://example.com",
            "--username", "user",
            "--password", "pass",
            "--headed",
        ])
        assert args.headless is False

    def test_validate_args_missing_url(self, txt_requirements_file: Path) -> None:
        from src.cli.main import build_parser, validate_args

        parser = build_parser()
        args = parser.parse_args([
            str(txt_requirements_file),
            "--username", "user",
            "--password", "pass",
        ])
        # url defaults to empty string from env
        args.url = ""
        error = validate_args(args)
        assert error is not None
        assert "url" in error.lower()

    def test_validate_args_invalid_url_scheme(self, txt_requirements_file: Path) -> None:
        from src.cli.main import build_parser, validate_args

        parser = build_parser()
        args = parser.parse_args([
            str(txt_requirements_file),
            "--url", "ftp://example.com",
            "--username", "user",
            "--password", "pass",
        ])
        error = validate_args(args)
        assert error is not None
        assert "http" in error.lower()

    def test_validate_args_missing_file(self, tmp_path: Path) -> None:
        from src.cli.main import build_parser, validate_args

        nonexistent = tmp_path / "no_file.txt"
        parser = build_parser()
        args = parser.parse_args([
            str(nonexistent),
            "--url", "https://example.com",
            "--username", "user",
            "--password", "pass",
        ])
        error = validate_args(args)
        assert error is not None
        assert "not found" in error.lower()

    def test_format_parsing(self, txt_requirements_file: Path) -> None:
        from src.cli.main import _parse_formats

        assert sorted(_parse_formats("all")) == sorted(["json", "junit", "html"])
        assert _parse_formats("json") == ["json"]
        assert sorted(_parse_formats("json,html")) == sorted(["json", "html"])
        assert sorted(_parse_formats("junit,json,html")) == sorted(["junit", "json", "html"])


# ---------------------------------------------------------------------------
# Model serialization integration tests
# ---------------------------------------------------------------------------


class TestModelSerialization:
    """Test model to_dict / from_dict round-trips."""

    def test_verification_result_round_trip(self) -> None:
        from src.models.verification_result import VerificationResult

        original = VerificationResult(
            requirement_id="REQ-001",
            status="passed",
            duration=1.5,
            logs=["step 1", "step 2"],
            screenshots=["screenshots/req001.png"],
        )
        restored = VerificationResult.from_dict(original.to_dict())
        assert restored.requirement_id == original.requirement_id
        assert restored.status == original.status
        assert restored.logs == original.logs

    def test_test_report_summary_counts(self) -> None:
        from src.models.test_report import TestReport

        results = _make_sample_results()
        report = TestReport.from_results(
            session_id="summary-test",
            duration=3.0,
            results=results,
            environment={},
        )

        assert report.summary.total == 3
        assert report.summary.passed == 1
        assert report.summary.failed == 1
        assert report.summary.needs_clarification == 1
        assert report.summary.errors == 0
        assert report.summary.pass_rate == pytest.approx(1 / 3)

    def test_requirements_document_format_detection(
        self,
        txt_requirements_file: Path,
        md_requirements_file: Path,
    ) -> None:
        from src.services.parser_service import ParserService

        svc = ParserService()

        txt_doc = svc.parse_requirements(txt_requirements_file)
        assert txt_doc.format == "txt"

        md_doc = svc.parse_requirements(md_requirements_file)
        assert md_doc.format == "md"
