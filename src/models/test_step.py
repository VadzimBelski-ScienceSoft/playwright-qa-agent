from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

VALID_ACTION_TYPES = ["navigate", "fill", "click", "wait", "verify", "screenshot"]


@dataclass
class TestStep:
    action: str
    target: str
    success: bool
    timestamp: datetime
    value: Optional[str] = None
    selector: Optional[str] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "action": self.action,
            "target": self.target,
            "value": self.value,
            "selector": self.selector,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TestStep":
        """Create from dictionary."""
        return cls(
            action=data["action"],
            target=data["target"],
            success=data["success"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            value=data.get("value"),
            selector=data.get("selector"),
            duration=data.get("duration"),
            error_message=data.get("error_message"),
        )

    def validate(self) -> List[str]:
        """
        Validate model constraints.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.action not in VALID_ACTION_TYPES:
            errors.append(f"action must be one of {VALID_ACTION_TYPES}, got: {self.action!r}")

        if not self.target:
            errors.append("target must be non-empty")

        return errors
