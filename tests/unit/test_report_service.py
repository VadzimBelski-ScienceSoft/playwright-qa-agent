"""Unit tests for the report service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.models.test_report import TestReport
from src.models.test_step import TestStep
from src.models.verification_result import VerificationResult
from src.services.report_service import ReportService


def _make_step() -> TestStep:
    return TestStep(
        action="navigate",
        target="page",
        value="",
        selector="",
        success=True,
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        error_message="",
    )


def _make_result(status: str = "passed", req_id: str = "REQ-001") -> VerificationResult:
    kwargs = {
        "requirement_id": req_id,
        "status": status,
        "duration": 1.0,
        "steps": [_make_step()],
        "logs": ["[12:00:00] Step executed"],
        "screenshots": [],
    }
    if status == "failed":
        kwargs["error"] = {"message": "Element not found", "type": "NotFoundError"}
    if status == "needs_clarification":
        kwargs["clarification_reason"] = "Ambiguous requirement"
    return VerificationResult(**kwargs)


def _make_report(results=None) -> TestReport:
    if results is None:
        results = [_make_result("passed"), _make_result("failed", "REQ-002")]
    return TestReport.from_results(
        session_id="test-session-123",
        duration=5.0,
        results=results,
        environment={"python_version": "3.11", "playwright_version": "1.58.0", "platform": "Linux"},
    )


class TestGenerateJsonReport:
    def test_creates_file(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "report.json"
        svc.generate_json_report(report, output)
        assert output.exists()

    def test_valid_json(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "report.json"
        svc.generate_json_report(report, output)
        data = json.loads(output.read_text())
        assert "session_id" in data
        assert "summary" in data
        assert "results" in data

    def test_json_schema_fields(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "report.json"
        svc.generate_json_report(report, output)
        data = json.loads(output.read_text())
        assert data["session_id"] == "test-session-123"
        assert data["summary"]["total"] == 2
        assert data["summary"]["passed"] == 1
        assert data["summary"]["failed"] == 1
        assert len(data["results"]) == 2

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "deep" / "nested" / "report.json"
        svc.generate_json_report(report, output)
        assert output.exists()


class TestGenerateJunitXml:
    def test_creates_file(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "junit.xml"
        svc.generate_junit_xml(report, output)
        assert output.exists()

    def test_valid_xml(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "junit.xml"
        svc.generate_junit_xml(report, output)
        content = output.read_text()
        assert "<?xml" in content or "<testsuites" in content or "<testsuite" in content

    def test_contains_test_cases(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "junit.xml"
        svc.generate_junit_xml(report, output)
        content = output.read_text()
        assert "testcase" in content.lower() or "REQ-001" in content


class TestGenerateHtmlReport:
    def test_creates_file(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "report.html"
        svc.generate_html_report(report, output)
        assert output.exists()

    def test_valid_html(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "report.html"
        svc.generate_html_report(report, output)
        content = output.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "REQ-001" in content

    def test_contains_summary(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        output = tmp_path / "report.html"
        svc.generate_html_report(report, output)
        content = output.read_text()
        assert "passed" in content.lower()
        assert "failed" in content.lower()


class TestGenerateAll:
    def test_generates_all_formats(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        files = svc.generate_all(report, tmp_path)
        assert (tmp_path / "report.json").exists()
        assert (tmp_path / "junit.xml").exists()
        assert (tmp_path / "report.html").exists()
        assert "json" in files
        assert "junit_xml" in files
        assert "html" in files

    def test_generates_only_json(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        files = svc.generate_all(report, tmp_path, formats=["json"])
        assert (tmp_path / "report.json").exists()
        assert not (tmp_path / "junit.xml").exists()
        assert "json" in files
        assert "junit_xml" not in files

    def test_generates_junit_only(self, tmp_path: Path) -> None:
        report = _make_report()
        svc = ReportService()
        svc.generate_all(report, tmp_path, formats=["junit"])
        assert (tmp_path / "junit.xml").exists()
        assert not (tmp_path / "report.json").exists()
