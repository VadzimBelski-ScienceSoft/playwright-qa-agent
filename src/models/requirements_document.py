from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from src.models.requirement import Requirement

VALID_FORMATS = ["txt", "md"]


@dataclass
class RequirementsDocument:
    file_path: Path
    format: str
    raw_content: str
    requirements: List[Requirement]
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": str(self.file_path),
            "format": self.format,
            "raw_content": self.raw_content,
            "requirements": [req.to_dict() for req in self.requirements],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RequirementsDocument":
        """Create from dictionary."""
        return cls(
            file_path=Path(data["file_path"]),
            format=data["format"],
            raw_content=data["raw_content"],
            requirements=[Requirement.from_dict(r) for r in data.get("requirements", [])],
            metadata=data.get("metadata", {}),
        )

    def validate(self) -> List[str]:
        """
        Validate model constraints.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.file_path.exists():
            errors.append(f"file_path does not exist: {self.file_path}")

        if self.format not in VALID_FORMATS:
            errors.append(f"format must be one of {VALID_FORMATS}, got: {self.format!r}")

        if not self.raw_content:
            errors.append("raw_content must be non-empty")

        return errors
