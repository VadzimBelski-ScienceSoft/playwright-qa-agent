"""Unit tests for the VerificationResult model."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.models.test_step import TestStep
from src.models.verification_result import VALID_STATUSES, VerificationResult


def _make_step(**kwargs) -> TestStep:
    defaults = {
        "action": "navigate",
        "target": "login page",
        "value": "",
        "selector": "",
        "success": True,
        "timestamp": datetime(2026, 2, 20, 14, 30, 45),
        "duration": 0.5,
        "error_message": "",
    }
    defaults.update(kwargs)
    return TestStep(**defaults)


def _make_result(**kwargs) -> VerificationResult:
    defaults = {
        "requirement_id": "REQ-001",
        "status": "passed",
        "duration": 2.34,
        "steps": [_make_step()],
    }
    defaults.update(kwargs)
    return VerificationResult(**defaults)


class TestVerificationResultCreation:
    def test_create_minimal(self) -> None:
        result = _make_result()
        assert result.requirement_id == "REQ-001"
        assert result.status == "passed"
        assert result.duration == 2.34
        assert len(result.steps) == 1
        assert result.screenshots == []
        assert result.logs == []
        assert result.error is None
        assert result.clarification_reason is None
        assert result.refinement_suggestion is None
        assert result.evidence is None

    def test_create_with_all_fields(self) -> None:
        result = VerificationResult(
            requirement_id="REQ-002",
            status="failed",
            duration=1.0,
            steps=[_make_step()],
            screenshots=["screenshots/req_002.png"],
            logs=["[14:30:46] step executed"],
            error={"message": "Element not found"},
            clarification_reason=None,
            refinement_suggestion="Add selector hint",
            evidence={"dom": "<html/>"},
        )
        assert result.error == {"message": "Element not found"}
        assert result.screenshots == ["screenshots/req_002.png"]
        assert result.evidence == {"dom": "<html/>"}

    @pytest.mark.parametrize("status", VALID_STATUSES)
    def test_all_valid_statuses(self, status: str) -> None:
        kwargs: dict = {"status": status}
        if status == "failed":
            kwargs["error"] = {"message": "fail"}
        if status == "needs_clarification":
            kwargs["clarification_reason"] = "Ambiguous"
        result = _make_result(**kwargs)
        assert result.status == status

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValueError, match="status must be one of"):
            _make_result(status="unknown")


class TestVerificationResultValidate:
    def test_valid_passed(self) -> None:
        result = _make_result(status="passed")
        assert result.validate() == []

    def test_valid_failed_with_error(self) -> None:
        result = _make_result(status="failed", error={"message": "fail"})
        assert result.validate() == []

    def test_valid_needs_clarification(self) -> None:
        result = _make_result(
            status="needs_clarification", clarification_reason="Requirement is ambiguous"
        )
        assert result.validate() == []

    def test_failed_without_error(self) -> None:
        result = _make_result(status="failed", error={"message": "fail"})
        result.error = None  # bypass __post_init__
        errors = result.validate()
        assert any("error" in e for e in errors)

    def test_needs_clarification_without_reason(self) -> None:
        result = _make_result(
            status="needs_clarification", clarification_reason="reason"
        )
        result.clarification_reason = None  # bypass __post_init__
        errors = result.validate()
        assert any("clarification_reason" in e for e in errors)

    def test_negative_duration(self) -> None:
        result = _make_result(duration=2.0)
        result.duration = -1.0
        errors = result.validate()
        assert any("duration" in e for e in errors)

    def test_valid_skipped(self) -> None:
        result = _make_result(status="skipped")
        assert result.validate() == []

    def test_valid_error_status(self) -> None:
        result = _make_result(status="error")
        assert result.validate() == []


class TestVerificationResultSerialization:
    def test_to_dict(self) -> None:
        result = _make_result()
        d = result.to_dict()
        assert d["requirement_id"] == "REQ-001"
        assert d["status"] == "passed"
        assert d["duration"] == 2.34
        assert isinstance(d["steps"], list)
        assert len(d["steps"]) == 1

    def test_round_trip(self) -> None:
        original = _make_result(
            status="failed",
            error={"message": "fail"},
            screenshots=["req_001.png"],
            logs=["log line"],
            refinement_suggestion="hint",
            evidence={"key": "val"},
        )
        d = original.to_dict()
        restored = VerificationResult.from_dict(d)
        assert restored.requirement_id == original.requirement_id
        assert restored.status == original.status
        assert restored.duration == original.duration
        assert restored.error == original.error
        assert restored.screenshots == original.screenshots
        assert restored.logs == original.logs
        assert restored.refinement_suggestion == original.refinement_suggestion
        assert restored.evidence == original.evidence
        assert len(restored.steps) == len(original.steps)
