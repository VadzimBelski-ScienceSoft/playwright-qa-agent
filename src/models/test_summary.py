from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class TestSummary:
    total: int
    passed: int
    failed: int
    needs_clarification: int
    skipped: int
    errors: int
    pass_rate: float

    def calculate_pass_rate(self) -> float:
        """Return passed / total if total > 0, else 0.0."""
        if self.total > 0:
            return self.passed / self.total
        return 0.0

    def validate(self) -> List[str]:
        """
        Validate model constraints.

        Returns:
            List of validation error messages (empty if valid)
        """
        validation_errors = []

        counts = {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "needs_clarification": self.needs_clarification,
            "skipped": self.skipped,
            "errors": self.errors,
        }
        for name, value in counts.items():
            if value < 0:
                validation_errors.append(f"{name} must be >= 0, got: {value}")

        if not (0.0 <= self.pass_rate <= 1.0):
            validation_errors.append(
                f"pass_rate must be between 0.0 and 1.0, got: {self.pass_rate}"
            )

        count_sum = (
            self.passed
            + self.failed
            + self.needs_clarification
            + self.skipped
            + self.errors
        )
        if count_sum != self.total:
            validation_errors.append(
                f"sum of counts ({count_sum}) must equal total ({self.total})"
            )

        return validation_errors
