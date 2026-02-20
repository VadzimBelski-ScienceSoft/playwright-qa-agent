"""Browser service for Playwright-based web application interaction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.lib.logger import get_logger
from src.models.web_application import WebApplication

logger = get_logger(__name__)


class BrowserService:
    """Manages Playwright browser lifecycle and web application interactions."""

    def __init__(self, browser_type: str = "chromium", headless: bool = True) -> None:
        """Initialize BrowserService.

        Args:
            browser_type: Browser to use: chromium, firefox, or webkit.
            headless: Whether to run in headless mode.
        """
        self.browser_type = browser_type
        self.headless = headless
        self._playwright = None
        self._browser = None

    def launch(self):
        """Launch the Playwright browser.

        Returns:
            The browser instance.
        """
        from playwright.sync_api import sync_playwright

        logger.info("Launching %s browser (headless=%s)", self.browser_type, self.headless)
        self._playwright = sync_playwright().start()

        browser_map = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "webkit": self._playwright.webkit,
        }

        if self.browser_type not in browser_map:
            raise ValueError(
                f"Unsupported browser type: {self.browser_type!r}. "
                "Choose from: chromium, firefox, webkit."
            )

        self._browser = browser_map[self.browser_type].launch(headless=self.headless)
        logger.debug("Browser launched successfully")
        return self._browser

    def close(self) -> None:
        """Close the browser and stop Playwright."""
        if self._browser is not None:
            try:
                self._browser.close()
                logger.debug("Browser closed")
            except Exception as exc:
                logger.warning("Error closing browser: %s", exc)
            finally:
                self._browser = None

        if self._playwright is not None:
            try:
                self._playwright.stop()
                logger.debug("Playwright stopped")
            except Exception as exc:
                logger.warning("Error stopping Playwright: %s", exc)
            finally:
                self._playwright = None

    def new_context(self, storage_state: Optional[dict] = None):
        """Create a new browser context.

        Args:
            storage_state: Optional auth state dict (from load_auth_state).

        Returns:
            BrowserContext instance.
        """
        if self._browser is None:
            raise RuntimeError("Browser not launched. Call launch() first.")

        kwargs = {}
        if storage_state:
            kwargs["storage_state"] = storage_state

        context = self._browser.new_context(**kwargs)
        return context

    def authenticate(self, page, app_config: WebApplication) -> bool:
        """Authenticate to the web application.

        Navigates to the login page, fills credentials, and submits the form.
        Password is NEVER logged.

        Args:
            page: Playwright Page instance.
            app_config: WebApplication configuration with credentials and selectors.

        Returns:
            True if authentication succeeded, False otherwise.
        """
        login_url = app_config.get_login_url()
        logger.info("Authenticating user '%s' at %s", app_config.username, login_url)

        try:
            page.goto(login_url, wait_until="networkidle", timeout=30000)
        except Exception as exc:
            logger.error("Failed to load login page %s: %s", login_url, exc)
            return False

        selectors = app_config.login_selectors or {}
        username_sel = selectors.get(
            "username",
            "#username, input[name='username'], input[type='email']",
        )
        password_sel = selectors.get(
            "password",
            "#password, input[name='password'], input[type='password']",
        )
        submit_sel = selectors.get(
            "submit",
            "button[type='submit'], input[type='submit']",
        )

        try:
            page.fill(username_sel, app_config.username)
            logger.debug("Filled username field")
            page.fill(password_sel, app_config.password)
            logger.debug("Filled password field")  # Do NOT log the password value
        except Exception as exc:
            logger.error("Failed to fill credentials: %s", exc)
            return False

        try:
            page.click(submit_sel)
            page.wait_for_load_state("networkidle", timeout=30000)
            logger.info("Login submitted, waiting for navigation")
        except Exception as exc:
            logger.error("Failed to submit login form: %s", exc)
            return False

        # Verify we moved away from login page
        current_url = page.url
        if "login" in current_url.lower() or "signin" in current_url.lower():
            logger.warning("Still on login page after submit - credentials may be invalid")
            return False

        logger.info("Authentication successful")
        return True

    def save_auth_state(self, context, file_path: Path) -> None:
        """Save Playwright authentication state to a JSON file.

        Args:
            context: Playwright BrowserContext instance.
            file_path: Path to save the state JSON file.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(file_path))
        logger.debug("Auth state saved to %s", file_path)

    def load_auth_state(self, file_path: Path) -> Optional[dict]:
        """Load Playwright authentication state from a JSON file.

        Args:
            file_path: Path to the saved state JSON file.

        Returns:
            Storage state dict, or None if file does not exist.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.debug("Auth state file not found: %s", file_path)
            return None

        with open(file_path, encoding="utf-8") as f:
            state = json.load(f)

        logger.debug("Auth state loaded from %s", file_path)
        return state

    def navigate_to(self, page, url: str, wait_for: str = "load") -> bool:
        """Navigate to a URL.

        Args:
            page: Playwright Page instance.
            url: Target URL.
            wait_for: Wait condition: load, networkidle, or domcontentloaded.

        Returns:
            True if navigation succeeded, False otherwise.
        """
        logger.debug("Navigating to %s (wait_for=%s)", url, wait_for)

        valid_wait = ("load", "networkidle", "domcontentloaded")
        if wait_for not in valid_wait:
            wait_for = "load"

        try:
            page.goto(url, wait_until=wait_for, timeout=30000)
            logger.debug("Navigation to %s complete", url)
            return True
        except Exception as exc:
            logger.warning("Navigation to %s failed: %s", url, exc)
            return False

    def verify_element(self, page, selector: str, timeout: int = 30000) -> dict:
        """Wait for an element and verify it exists.

        Args:
            page: Playwright Page instance.
            selector: CSS/XPath selector or Playwright locator expression.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Dict with keys:
              - success (bool): Whether element was found.
              - visible (bool): Whether element is visible.
              - text (str | None): Element text content if found.
              - error (str | None): Error message if failed.
        """
        logger.debug("Verifying element: %s", selector)

        try:
            element = page.wait_for_selector(selector, timeout=timeout)
            is_visible = element.is_visible() if element else False
            text = element.inner_text() if element else None
            logger.debug("Element found: %s (visible=%s)", selector, is_visible)
            return {
                "success": element is not None,
                "visible": is_visible,
                "text": text,
                "error": None,
            }
        except Exception as exc:
            logger.debug("Element not found: %s — %s", selector, exc)
            return {
                "success": False,
                "visible": False,
                "text": None,
                "error": str(exc),
            }

    def capture_screenshot(self, page, output_path: Path) -> Optional[str]:
        """Capture a screenshot of the current page.

        Args:
            page: Playwright Page instance.
            output_path: Path where the screenshot PNG will be saved.

        Returns:
            String path to screenshot file, or None if capture failed.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            page.screenshot(path=str(output_path), full_page=True)
            logger.debug("Screenshot saved: %s", output_path)
            return str(output_path)
        except Exception as exc:
            logger.warning("Screenshot capture failed: %s", exc)
            return None
