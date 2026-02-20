"""WebApplication model for the Playwright QA Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WebApplication:
    """Configuration for the web application under test."""

    url: str
    username: str
    password: str
    login_url: Optional[str] = field(default=None)
    login_selectors: dict = field(default_factory=lambda: {
        "username": "#username, input[name='username'], input[type='email']",
        "password": "#password, input[name='password'], input[type='password']",
        "submit": "button[type='submit'], input[type='submit']",
    })
    session_storage: Optional[str] = field(default=None)

    def get_login_url(self) -> str:
        """Return login URL, defaulting to base URL + /login."""
        if self.login_url:
            return self.login_url
        return self.url.rstrip("/") + "/login"

    def validate(self) -> List[str]:
        """Validate model constraints.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        if not self.url:
            errors.append("url must be non-empty")
        elif not (self.url.startswith("http://") or self.url.startswith("https://")):
            errors.append(f"url must start with http:// or https://, got: {self.url!r}")

        if not self.username:
            errors.append("username must be non-empty")

        if not self.password:
            errors.append("password must be non-empty")

        return errors
