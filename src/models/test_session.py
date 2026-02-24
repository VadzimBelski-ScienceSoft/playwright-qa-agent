"""TestSession model for the Playwright QA Agent."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.models.requirements_document import RequirementsDocument
from src.models.verification_result import VerificationResult

VALID_STATUSES = ["running", "completed", "failed"]
VALID_BROWSER_TYPES = ["chromium", "firefox", "webkit"]


@dataclass
class TestSession:
    """Represents a single execution of the QA agent against a web application."""

    requirements_doc: RequirementsDocument
    browser_type: str
    headless: bool
    output_dir: Path
    environment: dict
    app_url: Optional[str] = field(default=None)
    username: Optional[str] = field(default=None)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = field(default=None)
    duration: Optional[float] = field(default=None)
    results: List[VerificationResult] = field(default_factory=list)
    status: str = field(default="running")

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}, got: {self.status!r}")
        if self.browser_type not in VALID_BROWSER_TYPES:
            raise ValueError(
                f"browser_type must be one of {VALID_BROWSER_TYPES}, got: {self.browser_type!r}"
            )

    def complete(self) -> None:
        """Transition session to completed state."""
        self.end_time = datetime.now(timezone.utc)
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "completed"

    def fail(self) -> None:
        """Transition session to failed state."""
        self.end_time = datetime.now(timezone.utc)
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "failed"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "requirements_doc": self.requirements_doc.to_dict(),
            "app_url": self.app_url,
            "username": self.username,
            "browser_type": self.browser_type,
            "headless": self.headless,
            "results": [r.to_dict() for r in self.results],
            "status": self.status,
            "output_dir": str(self.output_dir),
            "environment": self.environment,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TestSession":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration=data.get("duration"),
            requirements_doc=RequirementsDocument.from_dict(data["requirements_doc"]),
            app_url=data.get("app_url"),
            username=data.get("username"),
            browser_type=data["browser_type"],
            headless=data["headless"],
            results=[VerificationResult.from_dict(r) for r in data.get("results", [])],
            status=data["status"],
            output_dir=Path(data["output_dir"]),
            environment=data.get("environment", {}),
        )

    def validate(self) -> List[str]:
        """Validate model constraints.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        if self.status not in VALID_STATUSES:
            errors.append(f"status must be one of {VALID_STATUSES}, got: {self.status!r}")

        if self.browser_type not in VALID_BROWSER_TYPES:
            errors.append(
                f"browser_type must be one of {VALID_BROWSER_TYPES}, got: {self.browser_type!r}"
            )

        if self.end_time is not None and self.end_time < self.start_time:
            errors.append("end_time must not be before start_time")

        if self.duration is not None and self.duration < 0:
            errors.append(f"duration must be non-negative, got: {self.duration}")

        return errors
