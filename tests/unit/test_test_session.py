"""Unit tests for the TestSession model."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.models.requirement import Requirement
from src.models.requirements_document import RequirementsDocument
from src.models.test_session import VALID_BROWSER_TYPES, TestSession
from src.models.test_step import TestStep
from src.models.verification_result import VerificationResult


def _make_req() -> Requirement:
    return Requirement(id="REQ-001", number=1, title="Login", description="User can login")


def _make_req_doc(tmp_path: Path) -> RequirementsDocument:
    f = tmp_path / "requirements.md"
    f.write_text("1. User can login")
    return RequirementsDocument(
        file_path=f,
        format="md",
        raw_content="1. User can login",
        requirements=[_make_req()],
    )


def _make_step() -> TestStep:
    return TestStep(
        action="navigate",
        target="login page",
        value="",
        selector="",
        success=True,
        timestamp=datetime(2026, 2, 20, 14, 30, 45, tzinfo=timezone.utc),
        duration=0.5,
        error_message="",
    )


def _make_result() -> VerificationResult:
    return VerificationResult(
        requirement_id="REQ-001",
        status="passed",
        duration=2.34,
        steps=[_make_step()],
    )


def _make_session(tmp_path: Path, **kwargs) -> TestSession:
    defaults = {
        "requirements_doc": _make_req_doc(tmp_path),
        "browser_type": "chromium",
        "headless": True,
        "output_dir": tmp_path / "output",
        "environment": {"python_version": "3.11.0", "platform": "Linux"},
        "app_url": "https://app.example.com",
        "username": "testuser",
    }
    defaults.update(kwargs)
    return TestSession(**defaults)


class TestTestSessionCreation:
    def test_create_minimal(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        assert session.app_url == "https://app.example.com"
        assert session.username == "testuser"
        assert session.browser_type == "chromium"
        assert session.headless is True
        assert session.status == "running"
        assert session.end_time is None
        assert session.duration is None
        assert session.results == []

    def test_session_id_auto_generated(self, tmp_path: Path) -> None:
        s1 = _make_session(tmp_path)
        s2 = _make_session(tmp_path)
        assert s1.session_id != s2.session_id
        # UUID format: 8-4-4-4-12 hex chars
        assert len(s1.session_id) == 36

    def test_start_time_auto_set(self, tmp_path: Path) -> None:
        before = datetime.now(timezone.utc)
        session = _make_session(tmp_path)
        after = datetime.now(timezone.utc)
        assert before <= session.start_time <= after

    def test_create_with_explicit_session_id(self, tmp_path: Path) -> None:
        sid = "550e8400-e29b-41d4-a716-446655440000"
        session = _make_session(tmp_path, session_id=sid)
        assert session.session_id == sid

    def test_invalid_status_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="status must be one of"):
            _make_session(tmp_path, status="invalid")

    def test_invalid_browser_type_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="browser_type must be one of"):
            _make_session(tmp_path, browser_type="ie")

    def test_all_valid_browser_types(self, tmp_path: Path) -> None:
        for bt in VALID_BROWSER_TYPES:
            s = _make_session(tmp_path, browser_type=bt)
            assert s.browser_type == bt

    def test_create_with_results(self, tmp_path: Path) -> None:
        results = [_make_result()]
        session = _make_session(tmp_path, results=results)
        assert len(session.results) == 1


class TestTestSessionStateTransitions:
    def test_complete_transition(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        assert session.status == "running"
        before = datetime.now(timezone.utc)
        session.complete()
        after = datetime.now(timezone.utc)
        assert session.status == "completed"
        assert session.end_time is not None
        assert before <= session.end_time <= after
        assert session.duration is not None
        assert session.duration >= 0

    def test_fail_transition(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        assert session.status == "running"
        session.fail()
        assert session.status == "failed"
        assert session.end_time is not None
        assert session.duration is not None
        assert session.duration >= 0

    def test_duration_calculated_correctly(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        time.sleep(0.05)
        session.complete()
        assert session.duration is not None
        assert session.duration >= 0.04


class TestTestSessionSerialization:
    def test_to_dict_running(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        d = session.to_dict()
        assert d["app_url"] == "https://app.example.com"
        assert d["username"] == "testuser"
        assert d["browser_type"] == "chromium"
        assert d["headless"] is True
        assert d["status"] == "running"
        assert d["end_time"] is None
        assert d["duration"] is None
        assert d["results"] == []

    def test_to_dict_completed(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        session.complete()
        d = session.to_dict()
        assert d["status"] == "completed"
        assert d["end_time"] is not None
        assert d["duration"] is not None

    def test_from_dict_roundtrip(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        session.complete()
        d = session.to_dict()
        restored = TestSession.from_dict(d)
        assert restored.session_id == session.session_id
        assert restored.app_url == session.app_url
        assert restored.username == session.username
        assert restored.browser_type == session.browser_type
        assert restored.headless == session.headless
        assert restored.status == session.status
        assert restored.duration == session.duration

    def test_output_dir_serialized_as_string(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        d = session.to_dict()
        assert isinstance(d["output_dir"], str)


class TestTestSessionValidation:
    def test_validate_valid_session(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        assert session.validate() == []

    def test_validate_empty_app_url_is_valid(self, tmp_path: Path) -> None:
        # app_url is optional - empty string or None is valid
        session = _make_session(tmp_path, app_url="")
        assert session.validate() == []

    def test_validate_none_app_url_is_valid(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path, app_url=None)
        assert session.validate() == []

    def test_validate_empty_username_is_valid(self, tmp_path: Path) -> None:
        # username is optional - empty string or None is valid
        session = _make_session(tmp_path, username="")
        assert session.validate() == []

    def test_create_without_url_and_username(self, tmp_path: Path) -> None:
        # Session can be created without app_url and username
        session = _make_session(tmp_path, app_url=None, username=None)
        assert session.app_url is None
        assert session.username is None
        assert session.validate() == []

    def test_validate_negative_duration(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        session.duration = -1.0
        errors = session.validate()
        assert any("duration" in e for e in errors)

    def test_validate_end_before_start(self, tmp_path: Path) -> None:
        session = _make_session(tmp_path)
        # Manually set end_time before start_time
        session.end_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        errors = session.validate()
        assert any("end_time" in e for e in errors)
