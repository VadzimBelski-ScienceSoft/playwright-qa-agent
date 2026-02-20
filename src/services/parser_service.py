"""Parser service for requirements documents."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from src.lib.file_utils import read_file
from src.lib.logger import get_logger
from src.models.requirement import Requirement
from src.models.requirements_document import RequirementsDocument

logger = get_logger(__name__)

# Regex patterns for plain text parsing
_REQUIREMENT_LINE = re.compile(r"^(\d+)\.\s+(?:\*\*([^*]+)\*\*:\s+)?(.+)$")
_GWT_GIVEN = re.compile(r"[-*]\s*[Gg]iven:\s*(.+)")
_GWT_WHEN = re.compile(r"[-*]\s*[Ww]hen:\s*(.+)")
_GWT_THEN = re.compile(r"[-*]\s*[Tt]hen:\s*(.+)")

# Patterns for markdown GWT in bold markers
_MD_GIVEN = re.compile(r"\*\*[Gg]iven\*\*:?\s*(.+)")
_MD_WHEN = re.compile(r"\*\*[Ww]hen\*\*:?\s*(.+)")
_MD_THEN = re.compile(r"\*\*[Tt]hen\*\*:?\s*(.+)")

# Markdown section header (## REQ-001: Title or ## Title)
_MD_HEADER = re.compile(r"^#{1,3}\s+(?:REQ-\d{3}:\s*)?(.+)$")
_MD_REQ_HEADER = re.compile(r"^#{1,3}\s+(REQ-\d{3}):\s*(.+)$")


def _make_req_id(number: int) -> str:
    return f"REQ-{number:03d}"


def parse_plain_text(content: str) -> List[Requirement]:
    """Parse a plain text requirements document.

    Supports numbered list format:
      1. Title: Description
      1. Description
      - Given: precondition
      - When: trigger
      - Then: expected outcome

    Args:
        content: Raw file content.

    Returns:
        List of Requirement instances.
    """
    requirements: List[Requirement] = []
    lines = content.splitlines()
    current_req: dict | None = None

    for line in lines:
        line_stripped = line.strip()

        req_match = _REQUIREMENT_LINE.match(line_stripped)
        if req_match:
            # Save previous requirement
            if current_req is not None:
                requirements.append(_build_requirement(current_req))

            number = int(req_match.group(1))
            title = req_match.group(2) or ""
            description = req_match.group(3) or ""

            # If no explicit title, use first part of description as title
            if not title and description:
                # Use up to 60 chars as title if no title/colon separator
                title = description[:60].strip()

            current_req = {
                "number": number,
                "id": _make_req_id(number),
                "title": title,
                "description": description,
                "given": "",
                "when": "",
                "then": "",
            }
            continue

        if current_req is not None:
            given_match = _GWT_GIVEN.match(line_stripped)
            if given_match:
                current_req["given"] = given_match.group(1).strip()
                continue

            when_match = _GWT_WHEN.match(line_stripped)
            if when_match:
                current_req["when"] = when_match.group(1).strip()
                continue

            then_match = _GWT_THEN.match(line_stripped)
            if then_match:
                current_req["then"] = then_match.group(1).strip()
                continue

            # Append additional lines to description
            if line_stripped and not line_stripped.startswith("#"):
                current_req["description"] = (
                    current_req["description"] + " " + line_stripped
                ).strip()

    if current_req is not None:
        requirements.append(_build_requirement(current_req))

    logger.debug("Parsed %d requirements from plain text", len(requirements))
    return requirements


def _build_requirement(data: dict) -> Requirement:
    return Requirement(
        id=data["id"],
        number=data["number"],
        title=data["title"],
        description=data["description"],
        given=data.get("given", ""),
        when=data.get("when", ""),
        then=data.get("then", ""),
    )


def parse_markdown(content: str) -> List[Requirement]:
    """Parse a markdown requirements document.

    Supports:
    - Section headers: ## REQ-001: Title or ## Title
    - Numbered lists at the top level
    - Given/When/Then in bold: **Given**: ...

    Args:
        content: Raw markdown file content.

    Returns:
        List of Requirement instances.
    """
    # First try section-based format (## headers)
    section_reqs = _parse_markdown_sections(content)
    if section_reqs:
        logger.debug("Parsed %d requirements from markdown sections", len(section_reqs))
        return section_reqs

    # Fall back to numbered list format (same as plain text but strip markdown)
    plain_content = _strip_markdown(content)
    reqs = parse_plain_text(plain_content)
    logger.debug("Parsed %d requirements from markdown numbered list", len(reqs))
    return reqs


def _parse_markdown_sections(content: str) -> List[Requirement]:
    """Parse markdown requirements organized as sections (## headers)."""
    requirements: List[Requirement] = []
    lines = content.splitlines()
    current_req: dict | None = None
    auto_number = 0

    for line in lines:
        stripped = line.strip()

        # Check for section header
        req_match = _MD_REQ_HEADER.match(stripped)
        header_match = _MD_HEADER.match(stripped) if not req_match else None

        if req_match or header_match:
            # Save previous
            if current_req is not None:
                requirements.append(_build_requirement(current_req))

            auto_number += 1
            if req_match:
                req_id = req_match.group(1)
                title = req_match.group(2).strip()
                number = int(req_id.replace("REQ-", ""))
            else:
                title = header_match.group(1).strip()  # type: ignore[union-attr]
                number = auto_number
                req_id = _make_req_id(number)

            current_req = {
                "number": number,
                "id": req_id,
                "title": title,
                "description": "",
                "given": "",
                "when": "",
                "then": "",
            }
            continue

        if current_req is not None:
            given_match = _MD_GIVEN.match(stripped) or _GWT_GIVEN.match(stripped)
            if given_match:
                current_req["given"] = given_match.group(1).strip()
                continue

            when_match = _MD_WHEN.match(stripped) or _GWT_WHEN.match(stripped)
            if when_match:
                current_req["when"] = when_match.group(1).strip()
                continue

            then_match = _MD_THEN.match(stripped) or _GWT_THEN.match(stripped)
            if then_match:
                current_req["then"] = then_match.group(1).strip()
                continue

            if stripped and not stripped.startswith("#"):
                # Remove markdown formatting for description
                clean = re.sub(r"\*+([^*]+)\*+", r"\1", stripped)
                clean = re.sub(r"`([^`]+)`", r"\1", clean)
                if current_req["description"]:
                    current_req["description"] += " " + clean
                else:
                    current_req["description"] = clean

    if current_req is not None:
        requirements.append(_build_requirement(current_req))

    return requirements


def _strip_markdown(content: str) -> str:
    """Remove markdown formatting to get plain text."""
    # Remove headers (#)
    content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
    # Remove bold/italic
    content = re.sub(r"\*+([^*]+)\*+", r"\1", content)
    content = re.sub(r"_+([^_]+)_+", r"\1", content)
    # Remove inline code
    content = re.sub(r"`([^`]+)`", r"\1", content)
    # Remove links
    content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)
    return content


class ParserService:
    """Service for parsing requirements documents from .txt or .md files."""

    def parse_requirements(self, file_path: Path) -> RequirementsDocument:
        """Parse a requirements file into a RequirementsDocument.

        Args:
            file_path: Path to the requirements file (.txt or .md).

        Returns:
            RequirementsDocument with parsed requirements.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported.
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if suffix not in (".txt", ".md"):
            raise ValueError(
                f"Unsupported requirements file format: '{suffix}'. "
                "Please provide a .txt or .md file."
            )

        logger.info("Loading requirements from: %s", file_path)
        raw_content = read_file(file_path)

        if suffix == ".md":
            requirements = parse_markdown(raw_content)
        else:
            requirements = parse_plain_text(raw_content)

        doc = RequirementsDocument(
            file_path=file_path,
            format=suffix.lstrip("."),
            raw_content=raw_content,
            requirements=requirements,
            metadata={},
        )

        logger.info("Found %d requirements", len(requirements))
        return doc
