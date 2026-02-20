from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

VALID_ACTIONS = ["navigate", "fill", "click", "wait", "verify", "screenshot"]


@dataclass
class TestStep:
    action: str
    target: str
    value: str
    selector: str
    success: bool
    timestamp: datetime
    duration: float
    error_message: str

    def __post_init__(self) -> None:
        if self.action not in VALID_ACTIONS:
            raise ValueError(f"action must be one of {VALID_ACTIONS}, got: {self.action!r}")

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
            value=data["value"],
            selector=data["selector"],
            success=data["success"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration=data["duration"],
            error_message=data["error_message"],
        )

    def validate(self) -> List[str]:
        """
        Validate model constraints.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.action not in VALID_ACTIONS:
            errors.append(f"action must be one of {VALID_ACTIONS}, got: {self.action!r}")

        if self.duration < 0:
            errors.append(f"duration must be non-negative, got: {self.duration}")

        return errors
