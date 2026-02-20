"""Requirement model for the Playwright QA Agent."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

_ID_PATTERN = re.compile(r"^REQ-\d{3}$")


@dataclass
class Requirement:
    """Individual requirement extracted from a requirements document."""

    id: str
    number: int
    title: str = ""
    description: str = ""
    given: str = ""
    when: str = ""
    then: str = ""
    priority: str = ""
    category: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "given": self.given,
            "when": self.when,
            "then": self.then,
            "priority": self.priority,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Requirement":
        """Create a Requirement instance from a dictionary."""
        return cls(
            id=data["id"],
            number=data["number"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            given=data.get("given", ""),
            when=data.get("when", ""),
            then=data.get("then", ""),
            priority=data.get("priority", ""),
            category=data.get("category", ""),
        )

    def validate(self) -> List[str]:
        """Validate model constraints.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        if not _ID_PATTERN.match(self.id):
            errors.append(
                f"id must match pattern REQ-\\d{{3}} (e.g. REQ-001), got: {self.id!r}"
            )

        if self.number <= 0:
            errors.append(f"number must be greater than 0, got: {self.number}")

        if not self.title.strip():
            errors.append("title must not be empty")

        return errors
