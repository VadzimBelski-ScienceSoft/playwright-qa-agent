"""Unit tests for data models (TestReport, WebApplication, TestSummary)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.models.test_report import TestReport
from src.models.test_step import TestStep
from src.models.test_summary import TestSummary
from src.models.verification_result import VerificationResult
from src.models.web_application import WebApplication


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


def _make_result(status: str = "passed", **kwargs) -> VerificationResult:
    defaults = {
        "requirement_id": "REQ-001",
        "status": status,
        "duration": 1.0,
        "steps": [_make_step()],
    }
    if status == "failed":
        defaults["error"] = {"message": "fail"}
    if status == "needs_clarification":
        defaults["clarification_reason"] = "reason"
    defaults.update(kwargs)
    return VerificationResult(**defaults)


class TestTestSummary:
    def test_calculate_pass_rate_normal(self) -> None:
        s = TestSummary(total=10, passed=8, failed=2,
                        needs_clarification=0, skipped=0, errors=0, pass_rate=0.8)
        assert s.calculate_pass_rate() == pytest.approx(0.8)

    def test_calculate_pass_rate_zero_total(self) -> None:
        s = TestSummary(total=0, passed=0, failed=0,
                        needs_clarification=0, skipped=0, errors=0, pass_rate=0.0)
        assert s.calculate_pass_rate() == 0.0

    def test_validate_valid(self) -> None:
        s = TestSummary(total=3, passed=2, failed=1,
                        needs_clarification=0, skipped=0, errors=0, pass_rate=2/3)
        assert s.validate() == []

    def test_validate_counts_dont_match_total(self) -> None:
        s = TestSummary(total=5, passed=2, failed=1,
                        needs_clarification=0, skipped=0, errors=0, pass_rate=0.4)
        errors = s.validate()
        assert any("sum" in e or "total" in e for e in errors)

    def test_validate_negative_count(self) -> None:
        s = TestSummary(total=0, passed=-1, failed=1,
                        needs_clarification=0, skipped=0, errors=0, pass_rate=0.0)
        errors = s.validate()
        assert any("passed" in e for e in errors)

    def test_validate_pass_rate_out_of_range(self) -> None:
        s = TestSummary(total=1, passed=1, failed=0,
                        needs_clarification=0, skipped=0, errors=0, pass_rate=1.5)
        errors = s.validate()
        assert any("pass_rate" in e for e in errors)


class TestWebApplication:
    def test_create_minimal(self) -> None:
        app = WebApplication(url="https://app.com", username="user", password="pass")
        assert app.url == "https://app.com"
        assert app.username == "user"

    def test_get_login_url_default(self) -> None:
        app = WebApplication(url="https://app.com", username="u", password="p")
        assert app.get_login_url() == "https://app.com/login"

    def test_get_login_url_custom(self) -> None:
        app = WebApplication(
            url="https://app.com",
            username="u",
            password="p",
            login_url="https://app.com/auth",
        )
        assert app.get_login_url() == "https://app.com/auth"

    def test_validate_valid(self) -> None:
        app = WebApplication(url="https://app.com", username="u", password="p")
        assert app.validate() == []

    def test_validate_empty_url(self) -> None:
        app = WebApplication(url="", username="u", password="p")
        errors = app.validate()
        assert any("url" in e for e in errors)

    def test_validate_invalid_url_scheme(self) -> None:
        app = WebApplication(url="ftp://app.com", username="u", password="p")
        errors = app.validate()
        assert any("url" in e for e in errors)

    def test_validate_empty_username(self) -> None:
        app = WebApplication(url="https://app.com", username="", password="p")
        errors = app.validate()
        assert any("username" in e for e in errors)

    def test_validate_empty_password(self) -> None:
        app = WebApplication(url="https://app.com", username="u", password="")
        errors = app.validate()
        assert any("password" in e for e in errors)


class TestTestReport:
    def test_from_results_all_passed(self) -> None:
        results = [
            _make_result("passed", requirement_id="REQ-001"),
            _make_result("passed", requirement_id="REQ-002"),
        ]
        report = TestReport.from_results(
            session_id="test-session-id",
            duration=5.0,
            results=results,
            environment={"python_version": "3.11"},
        )
        assert report.summary.total == 2
        assert report.summary.passed == 2
        assert report.summary.failed == 0
        assert report.summary.pass_rate == 1.0

    def test_from_results_mixed(self) -> None:
        results = [
            _make_result("passed", requirement_id="REQ-001"),
            _make_result("failed", requirement_id="REQ-002"),
            _make_result("needs_clarification", requirement_id="REQ-003"),
        ]
        report = TestReport.from_results(
            session_id="sid",
            duration=10.0,
            results=results,
            environment={},
        )
        assert report.summary.total == 3
        assert report.summary.passed == 1
        assert report.summary.failed == 1
        assert report.summary.needs_clarification == 1
        assert report.summary.pass_rate == pytest.approx(1 / 3)

    def test_from_results_empty(self) -> None:
        report = TestReport.from_results(
            session_id="sid", duration=0.0, results=[], environment={}
        )
        assert report.summary.total == 0
        assert report.summary.pass_rate == 0.0

    def test_to_dict_roundtrip(self) -> None:
        results = [_make_result("passed", requirement_id="REQ-001")]
        report = TestReport.from_results(
            session_id="abc-123",
            duration=2.5,
            results=results,
            environment={"python_version": "3.11"},
            files={"json": "report.json"},
        )
        d = report.to_dict()
        restored = TestReport.from_dict(d)
        assert restored.session_id == report.session_id
        assert restored.duration == report.duration
        assert restored.summary.total == report.summary.total
        assert len(restored.results) == len(report.results)

    def test_validate_valid(self) -> None:
        report = TestReport.from_results(
            session_id="sid", duration=1.0,
            results=[_make_result("passed")], environment={}
        )
        assert report.validate() == []

    def test_validate_negative_duration(self) -> None:
        report = TestReport.from_results(
            session_id="sid", duration=1.0, results=[], environment={}
        )
        report.duration = -1.0
        errors = report.validate()
        assert any("duration" in e for e in errors)
