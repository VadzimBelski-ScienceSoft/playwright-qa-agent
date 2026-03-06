"""WebApplication model for the Playwright QA Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WebApplication:
    """Configuration for the web application under test."""

    url: str
    username: str = field(default="")
    password: str = field(default="")
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

        if self.url and not (self.url.startswith("http://") or self.url.startswith("https://")):
            errors.append(f"url must start with http:// or https://, got: {self.url!r}")

        if self.password and not self.username:
            errors.append("username must not be empty when password is provided")
        if self.username and not self.password:
            errors.append("password must not be empty when username is provided")

        return errors
