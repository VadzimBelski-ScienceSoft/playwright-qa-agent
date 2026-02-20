"""TestReport model for the Playwright QA Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from src.models.test_summary import TestSummary
from src.models.verification_result import VerificationResult


@dataclass
class TestReport:
    """Consolidated output containing all verification results and metadata."""

    session_id: str
    created: datetime
    duration: float
    summary: TestSummary
    requirements_tested: int
    results: List[VerificationResult]
    environment: dict
    files: dict = field(default_factory=dict)

    @classmethod
    def from_results(
        cls,
        session_id: str,
        duration: float,
        results: List[VerificationResult],
        environment: dict,
        files: dict | None = None,
    ) -> "TestReport":
        """Create a TestReport from a list of VerificationResult objects."""
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        needs_clarification = sum(1 for r in results if r.status == "needs_clarification")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")
        total = len(results)
        pass_rate = passed / total if total > 0 else 0.0

        summary = TestSummary(
            total=total,
            passed=passed,
            failed=failed,
            needs_clarification=needs_clarification,
            skipped=skipped,
            errors=errors,
            pass_rate=pass_rate,
        )

        return cls(
            session_id=session_id,
            created=datetime.now(timezone.utc),
            duration=duration,
            summary=summary,
            requirements_tested=total,
            results=results,
            environment=environment,
            files=files or {},
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "created": self.created.isoformat(),
            "duration": self.duration,
            "summary": {
                "total": self.summary.total,
                "passed": self.summary.passed,
                "failed": self.summary.failed,
                "needs_clarification": self.summary.needs_clarification,
                "skipped": self.summary.skipped,
                "errors": self.summary.errors,
                "pass_rate": self.summary.pass_rate,
            },
            "requirements_tested": self.requirements_tested,
            "results": [r.to_dict() for r in self.results],
            "environment": self.environment,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TestReport":
        """Create from dictionary."""
        summary_data = data["summary"]
        summary = TestSummary(
            total=summary_data["total"],
            passed=summary_data["passed"],
            failed=summary_data["failed"],
            needs_clarification=summary_data["needs_clarification"],
            skipped=summary_data["skipped"],
            errors=summary_data["errors"],
            pass_rate=summary_data["pass_rate"],
        )
        return cls(
            session_id=data["session_id"],
            created=datetime.fromisoformat(data["created"]),
            duration=data["duration"],
            summary=summary,
            requirements_tested=data["requirements_tested"],
            results=[VerificationResult.from_dict(r) for r in data.get("results", [])],
            environment=data.get("environment", {}),
            files=data.get("files", {}),
        )

    def validate(self) -> List[str]:
        """Validate model constraints.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        if not self.session_id:
            errors.append("session_id must be non-empty")

        if self.duration < 0:
            errors.append(f"duration must be non-negative, got: {self.duration}")

        if self.requirements_tested < 0:
            errors.append(
                f"requirements_tested must be non-negative, got: {self.requirements_tested}"
            )

        summary_errors = self.summary.validate()
        errors.extend(summary_errors)

        return errors
