"""VerificationResult model for the Playwright QA Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.models.test_step import TestStep

VALID_STATUSES = ["passed", "failed", "needs_clarification", "skipped", "error"]


@dataclass
class VerificationResult:
    """Result of verifying a single requirement against the web application."""

    requirement_id: str
    status: str
    duration: float
    steps: List[TestStep] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    error: Optional[dict] = field(default=None)
    clarification_reason: Optional[str] = field(default=None)
    refinement_suggestion: Optional[str] = field(default=None)
    evidence: Optional[dict] = field(default=None)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}, got: {self.status!r}")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "requirement_id": self.requirement_id,
            "status": self.status,
            "duration": self.duration,
            "steps": [step.to_dict() for step in self.steps],
            "screenshots": self.screenshots,
            "logs": self.logs,
            "error": self.error,
            "clarification_reason": self.clarification_reason,
            "refinement_suggestion": self.refinement_suggestion,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VerificationResult":
        """Create from dictionary."""
        return cls(
            requirement_id=data["requirement_id"],
            status=data["status"],
            duration=data["duration"],
            steps=[TestStep.from_dict(s) for s in data.get("steps", [])],
            screenshots=data.get("screenshots", []),
            logs=data.get("logs", []),
            error=data.get("error"),
            clarification_reason=data.get("clarification_reason"),
            refinement_suggestion=data.get("refinement_suggestion"),
            evidence=data.get("evidence"),
        )

    def validate(self) -> List[str]:
        """
        Validate model constraints.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.status not in VALID_STATUSES:
            errors.append(f"status must be one of {VALID_STATUSES}, got: {self.status!r}")

        if self.duration < 0:
            errors.append(f"duration must be non-negative, got: {self.duration}")

        if self.status == "failed" and not self.error:
            errors.append("error must be present when status is 'failed'")

        if self.status == "needs_clarification" and not self.clarification_reason:
            errors.append(
                "clarification_reason must be present when status is 'needs_clarification'"
            )

        return errors
