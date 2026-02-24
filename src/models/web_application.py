"""WebApplication model for the Playwright QA Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WebApplication:
    """Configuration for the web application under test."""

    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    login_url: Optional[str] = field(default=None)
    login_selectors: dict = field(default_factory=lambda: {
        "username": "#username, input[name='username'], input[type='email']",
        "password": "#password, input[name='password'], input[type='password']",
        "submit": "button[type='submit'], input[type='submit']",
    })
    session_storage: Optional[str] = field(default=None)

    def get_login_url(self) -> Optional[str]:
        """Return login URL, defaulting to base URL + /login."""
        if not self.url:
            return None
        if self.login_url:
            return self.login_url
        return self.url.rstrip("/") + "/login"

    def validate(self) -> List[str]:
        """Validate model constraints.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        # Only validate URL format if provided
        if self.url:
            if not (self.url.startswith("http://") or self.url.startswith("https://")):
                errors.append(f"url must start with http:// or https://, got: {self.url!r}")

        # username and password are optional - no validation required

        return errors
