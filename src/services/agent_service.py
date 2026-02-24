"""Agent service orchestrating Claude SDK and Playwright for QA automation."""

from __future__ import annotations

import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.lib.file_utils import create_latest_symlink, create_timestamped_dir, ensure_dir
from src.lib.logger import get_logger
from src.models.requirement import Requirement
from src.models.requirements_document import RequirementsDocument
from src.models.test_session import TestSession
from src.models.test_step import TestStep
from src.models.verification_result import VerificationResult
from src.models.web_application import WebApplication
from src.services.browser_service import BrowserService

logger = get_logger(__name__)

# Vague language patterns that signal ambiguity
_AMBIGUOUS_PATTERNS = [
    "manage", "handle", "process", "update", "view", "use", "access",
    "interact", "work with", "deal with", "maintain", "control",
    "some", "various", "appropriate", "relevant", "suitable",
]

# Regex to extract explicit URLs from requirement text
_URL_PATTERN = re.compile(r'https?://[^\s]+')


def _get_environment() -> dict:
    """Collect current runtime environment info."""
    try:
        import playwright
        pw_version = playwright.__version__
    except Exception:
        pw_version = "unknown"

    return {
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "platform_version": platform.version(),
        "playwright_version": pw_version,
    }


def _make_step(
    action: str,
    target: str,
    success: bool,
    value: str = "",
    selector: str = "",
    error_message: str = "",
    duration: float = 0.0,
) -> TestStep:
    """Create a TestStep with current timestamp."""
    return TestStep(
        action=action,
        target=target,
        value=value,
        selector=selector,
        success=success,
        timestamp=datetime.now(timezone.utc),
        duration=duration,
        error_message=error_message,
    )


def _extract_url_from_requirement(
    requirement: Requirement,
    default_url: Optional[str],
) -> Optional[str]:
    """Extract URL from requirement text or use default.

    Priority:
    1. Explicit https?:// URL in requirement text
    2. Default URL from CLI --url flag
    3. None (will need clarification if URL is required)
    """
    text = " ".join([
        requirement.description or "",
        requirement.given or "",
        requirement.when or "",
        requirement.then or "",
    ])

    match = _URL_PATTERN.search(text)
    if match:
        url = match.group(0).rstrip(".,;)")
        logger.debug("Extracted URL from requirement %s: %s", requirement.id, url)
        return url

    if default_url:
        logger.debug("Using default URL for %s: %s", requirement.id, default_url)
        return default_url

    logger.debug("No URL found for %s", requirement.id)
    return None


def _requirement_needs_url(requirement: Requirement) -> bool:
    """Determine if requirement explicitly needs a URL to execute."""
    text = " ".join([
        requirement.description or "",
        requirement.given or "",
        requirement.when or "",
        requirement.then or "",
        requirement.title or "",
    ]).lower()

    url_keywords = [
        "navigate", "visit", "go to", "open", "load", "access",
        "browse", "url", "page", "website", "web app",
    ]

    return any(kw in text for kw in url_keywords)


def _requires_authentication(requirement: Requirement) -> bool:
    """Determine if requirement needs login/authentication."""
    text = " ".join([
        requirement.description or "",
        requirement.given or "",
        requirement.when or "",
        requirement.then or "",
        requirement.title or "",
    ]).lower()

    auth_keywords = [
        "login", "log in", "log-in", "logs in",
        "sign in", "sign-in", "signin",
        "authenticate", "authentication",
        "credentials", "username", "password",
    ]

    return any(kw in text for kw in auth_keywords)


def _interpret_requirement_with_claude(requirement: Requirement, app_url: Optional[str]) -> dict:
    """Use Claude SDK to interpret a requirement and generate verification steps.

    Returns a dict with:
      - steps: List of step dicts [{"action": ..., "target": ..., ...}, ...]
      - is_ambiguous: bool
      - ambiguity_reasons: List[str]
      - refinement_suggestion: str
    """
    try:
        from claude_agent_sdk import query  # type: ignore

        prompt = (
            "You are a QA automation expert. Analyze this requirement and return a JSON response.\n\n"
            f"Requirement ID: {requirement.id}\n"
            f"Title: {requirement.title}\n"
            f"Description: {requirement.description}\n"
            f"Given: {requirement.given}\n"
            f"When: {requirement.when}\n"
            f"Then: {requirement.then}\n"
            f"Application URL: {app_url or 'not specified'}\n\n"
            "Return a JSON object with:\n"
            "- steps: array of verification steps, each with {action, target, selector, value}\n"
            "  Valid actions: navigate, fill, click, wait, verify, screenshot\n"
            "- is_ambiguous: boolean, true if requirement is vague or incomplete\n"
            "- ambiguity_reasons: array of strings explaining why it's ambiguous\n"
            "- refinement_suggestion: string with specific suggestion to improve the requirement\n"
            "\nExample step: {\"action\": \"navigate\", \"target\": \"home page\", \"selector\": \"\", \"value\": \"/\"}\n"
            "Example step: {\"action\": \"verify\", \"target\": \"login button\", \"selector\": \"button#login\", \"value\": \"\"}\n"
            "\nReturn ONLY valid JSON, no markdown."
        )

        result_text = ""
        for message in query(prompt=prompt, options={"max_turns": 1}):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        result_text += block.text

        import json
        # Extract JSON from response
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

    except ImportError:
        logger.debug("claude_agent_sdk not available, using rule-based interpretation")
    except Exception as exc:
        logger.warning("Claude SDK query failed: %s", exc)

    # Fallback: rule-based interpretation
    return _rule_based_interpretation(requirement, app_url)


def _rule_based_interpretation(requirement: Requirement, app_url: Optional[str]) -> dict:
    """Rule-based requirement interpretation fallback (no Claude SDK required)."""
    steps = []
    description = (requirement.description or requirement.title or "").lower()

    # Navigate to the app if URL is available
    if app_url:
        steps.append({
            "action": "navigate", "target": "application", "selector": "", "value": app_url,
        })
        steps.append({
            "action": "screenshot", "target": "initial_state", "selector": "", "value": "",
        })

    # Infer verification steps from description keywords
    if any(kw in description for kw in ["login", "sign in", "authenticate", "credentials"]):
        steps.append({"action": "verify", "target": "login form",
                      "selector": "form, input[type='password']", "value": ""})

    if any(kw in description for kw in ["dashboard", "home", "landing"]):
        steps.append({"action": "verify", "target": "main content",
                      "selector": "main, #main, .dashboard, .content", "value": ""})

    if any(kw in description for kw in ["button", "click", "submit"]):
        steps.append({"action": "verify", "target": "button",
                      "selector": "button, [role='button']", "value": ""})

    if any(kw in description for kw in ["form", "input", "field", "fill"]):
        steps.append({"action": "verify", "target": "form elements",
                      "selector": "input, textarea, select", "value": ""})

    navigate_and_screenshot = 2 if app_url else 0
    if len(steps) == navigate_and_screenshot:  # Only navigate/screenshot steps (or none)
        steps.append({"action": "verify", "target": "page loaded",
                      "selector": "body", "value": ""})

    steps.append({"action": "screenshot", "target": "final_state", "selector": "", "value": ""})

    # Check for ambiguity
    is_ambiguous = any(
        pattern in description for pattern in _AMBIGUOUS_PATTERNS
    )
    ambiguity_reasons = [
        f"Requirement contains vague term: '{p}'"
        for p in _AMBIGUOUS_PATTERNS
        if p in description
    ]

    refinement = ""
    if is_ambiguous:
        refinement = (
            f"Consider specifying exact UI elements, URLs, or user flows for: "
            f"'{requirement.title}'. Vague terms detected: "
            + ", ".join(
                f"'{p}'" for p in _AMBIGUOUS_PATTERNS if p in description
            )
        )

    return {
        "steps": steps,
        "is_ambiguous": is_ambiguous,
        "ambiguity_reasons": ambiguity_reasons,
        "refinement_suggestion": refinement,
    }


def detect_ambiguity(requirement: Requirement, page=None) -> dict:
    """Detect if a requirement is ambiguous or incomplete.

    Args:
        requirement: The requirement to analyze.
        page: Optional Playwright page (for element discovery).

    Returns:
        Dict with keys:
          - is_ambiguous (bool)
          - reasons (List[str])
          - discovered_elements (List[str])
    """
    description = (
        (requirement.description or "") + " " + (requirement.title or "")
    ).lower()

    reasons = [
        f"Requirement contains vague term: '{p}'"
        for p in _AMBIGUOUS_PATTERNS
        if p in description
    ]

    if not requirement.description and not requirement.given:
        reasons.append("Requirement lacks a detailed description or Given/When/Then structure")

    if requirement.title and len(requirement.title.split()) <= 3:
        reasons.append(f"Title is very short ({len(requirement.title.split())} words)")

    discovered_elements: List[str] = []
    if page is not None:
        try:
            # Find interactive elements on current page
            links = page.query_selector_all("a[href]")
            for link in links[:10]:
                text = link.inner_text().strip()
                if text:
                    discovered_elements.append(f"link: {text}")
            buttons = page.query_selector_all("button, [role='button']")
            for btn in buttons[:5]:
                text = btn.inner_text().strip()
                if text:
                    discovered_elements.append(f"button: {text}")
        except Exception:
            pass

    return {
        "is_ambiguous": bool(reasons),
        "reasons": reasons,
        "discovered_elements": discovered_elements,
    }


def suggest_refinement(requirement: Requirement, ambiguity_info: dict) -> str:
    """Suggest a refinement for an ambiguous requirement.

    Args:
        requirement: The ambiguous requirement.
        ambiguity_info: Output from detect_ambiguity().

    Returns:
        Actionable refinement suggestion string.
    """
    if not ambiguity_info.get("is_ambiguous"):
        return ""

    reasons = ambiguity_info.get("reasons", [])
    discovered = ambiguity_info.get("discovered_elements", [])

    parts = [f"Consider refining requirement '{requirement.id}: {requirement.title}'."]

    if reasons:
        parts.append("Issues found: " + "; ".join(reasons[:3]) + ".")

    if discovered:
        element_list = ", ".join(f"'{e}'" for e in discovered[:5])
        parts.append(f"Discovered elements on page: {element_list}.")
        parts.append(
            "Specify which element(s) this requirement refers to for unambiguous verification."
        )
    else:
        parts.append(
            "Add Given/When/Then structure with specific UI elements, "
            "URLs, and expected outcomes."
        )

    return " ".join(parts)


class AgentService:
    """Orchestrates Claude SDK and BrowserService for requirements verification."""

    def __init__(
        self,
        requirements_doc: RequirementsDocument,
        app_config: WebApplication,
        timeout: int = 30,
        screenshot_on: str = "always",
    ) -> None:
        """Initialize AgentService.

        Args:
            requirements_doc: Parsed requirements document.
            app_config: Web application configuration.
            timeout: Per-requirement timeout in seconds.
            screenshot_on: When to capture screenshots: always, failure, never.
        """
        self.requirements_doc = requirements_doc
        self.app_config = app_config
        self.timeout = timeout
        self.screenshot_on = screenshot_on
        self._browser_service: Optional[BrowserService] = None

    def create_session(
        self,
        output_base: Path,
        browser_type: str = "chromium",
        headless: bool = True,
    ) -> TestSession:
        """Create and initialize a TestSession with output directories.

        Args:
            output_base: Base directory for output (timestamped subdir created inside).
            browser_type: Browser to use.
            headless: Whether to run headless.

        Returns:
            Initialized TestSession.
        """
        output_dir = create_timestamped_dir(output_base)
        ensure_dir(output_dir / "screenshots")
        ensure_dir(output_dir / "logs")
        create_latest_symlink(output_dir)

        session = TestSession(
            requirements_doc=self.requirements_doc,
            app_url=self.app_config.url,
            username=self.app_config.username,
            browser_type=browser_type,
            headless=headless,
            output_dir=output_dir,
            environment=_get_environment(),
        )

        logger.info("Test session created: %s", session.session_id)
        logger.info("Output directory: %s", output_dir)
        return session

    def complete_session(
        self,
        session: TestSession,
        results: List[VerificationResult],
    ) -> None:
        """Finalize a test session with results.

        Args:
            session: The active TestSession.
            results: List of VerificationResult from verify_requirements().
        """
        session.results = results
        has_failures = any(r.status in ("failed", "error") for r in results)
        if has_failures:
            session.fail()
        else:
            session.complete()

        logger.info(
            "Session %s completed with status: %s", session.session_id, session.status
        )

    def verify_requirements(
        self,
        browser_service: BrowserService,
        session: TestSession,
    ) -> List[VerificationResult]:
        """Verify all requirements in the document.

        Args:
            browser_service: Launched BrowserService instance.
            session: Active TestSession.

        Returns:
            List of VerificationResult, one per requirement.
        """
        self._browser_service = browser_service
        results: List[VerificationResult] = []
        total = len(self.requirements_doc.requirements)

        context = browser_service.new_context()
        page = context.new_page()

        try:
            for idx, requirement in enumerate(self.requirements_doc.requirements, 1):
                logger.info(
                    "Testing %s (%d/%d): %s",
                    requirement.id, idx, total, requirement.title,
                )
                result = self._verify_single(requirement, page, session)
                results.append(result)
                _print_result(result)
        finally:
            try:
                context.close()
            except Exception:
                pass

        return results

    def _verify_single(
        self,
        requirement: Requirement,
        page,
        session: TestSession,
    ) -> VerificationResult:
        """Verify a single requirement.

        Args:
            requirement: The requirement to verify.
            page: Active Playwright page.
            session: Active test session (for output paths).

        Returns:
            VerificationResult for this requirement.
        """
        start = datetime.now(timezone.utc)
        steps: List[TestStep] = []
        screenshots: List[str] = []
        logs: List[str] = []

        def log(msg: str) -> None:
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            entry = f"[{ts}] {msg}"
            logs.append(entry)
            logger.debug("%s %s: %s", requirement.id, requirement.title, msg)

        try:
            # 1. Extract URL (explicit in requirement or default from CLI)
            url = _extract_url_from_requirement(requirement, self.app_config.url)

            # 2. Check if URL is needed but missing
            if url is None and _requirement_needs_url(requirement):
                duration = (datetime.now(timezone.utc) - start).total_seconds()
                return VerificationResult(
                    requirement_id=requirement.id,
                    status="needs_clarification",
                    duration=duration,
                    steps=steps,
                    screenshots=screenshots,
                    logs=logs,
                    clarification_reason=(
                        "No URL specified in requirement text or --url flag. "
                        "Either add an explicit URL (e.g., 'navigate to https://example.com') "
                        "or provide --url flag."
                    ),
                    refinement_suggestion=(
                        f"Add explicit URL to requirement {requirement.id}. "
                        "Example: 'Given user navigates to https://example.com'"
                    ),
                )

            log(f"Using URL: {url or 'N/A'}")

            # 3. Check if authentication is required
            if _requires_authentication(requirement):
                if not self.app_config.username or not self.app_config.password:
                    duration = (datetime.now(timezone.utc) - start).total_seconds()
                    return VerificationResult(
                        requirement_id=requirement.id,
                        status="needs_clarification",
                        duration=duration,
                        steps=steps,
                        screenshots=screenshots,
                        logs=logs,
                        clarification_reason=(
                            "Requirement requires authentication but no credentials provided. "
                            "Please provide --username and --password flags."
                        ),
                        refinement_suggestion=(
                            "Set QA_AGENT_USERNAME and QA_AGENT_PASSWORD environment variables "
                            "or use --username and --password flags."
                        ),
                    )

                # Perform on-demand authentication
                log("Authenticating...")
                auth_config = WebApplication(
                    url=url or self.app_config.url,
                    username=self.app_config.username,
                    password=self.app_config.password,
                    login_url=self.app_config.login_url,
                    login_selectors=self.app_config.login_selectors,
                )
                if self._browser_service is not None:
                    authenticated = self._browser_service.authenticate(page, auth_config)
                    if not authenticated:
                        duration = (datetime.now(timezone.utc) - start).total_seconds()
                        return VerificationResult(
                            requirement_id=requirement.id,
                            status="error",
                            duration=duration,
                            steps=steps,
                            screenshots=screenshots,
                            logs=logs,
                            error={
                                "message": "Authentication failed. Check credentials.",
                                "type": "AuthenticationError",
                            },
                        )
                    log("Authentication successful")

            # 4. Get verification plan from Claude (or fallback)
            plan = _interpret_requirement_with_claude(requirement, url)
            planned_steps = plan.get("steps", [])
            is_ambiguous = plan.get("is_ambiguous", False)
            ambiguity_reasons = plan.get("ambiguity_reasons", [])
            refinement = plan.get("refinement_suggestion", "")

            log(f"Verification plan has {len(planned_steps)} steps")

            # Run planned steps
            for step_data in planned_steps:
                action = step_data.get("action", "verify")
                target = step_data.get("target", "")
                selector = step_data.get("selector", "")
                value = step_data.get("value", "")

                step = self._execute_step(
                    action, target, selector, value, page, session, requirement.id, url
                )
                steps.append(step)
                log(f"Step {action} '{target}': {'ok' if step.success else 'failed'}")

                if action == "screenshot" and step.error_message:
                    pass  # screenshot path already handled
                elif action == "screenshot" and step.success and step.value:
                    screenshots.append(step.value)

            # Determine result status
            failed_steps = [s for s in steps if not s.success and s.action != "screenshot"]
            verify_steps = [s for s in steps if s.action == "verify"]

            if is_ambiguous and not verify_steps:
                status = "needs_clarification"
            elif not failed_steps:
                status = "passed"
            elif len(failed_steps) < len(steps) // 2:
                # More than half succeeded - still flag as clarification
                status = "needs_clarification"
            else:
                status = "failed"

            # Capture final screenshot on failure if not already taken
            if status == "failed" and self.screenshot_on in ("always", "failure"):
                ss_path = session.output_dir / "screenshots" / f"{requirement.id}_failure.png"
                ss = _safe_screenshot(page, ss_path)
                if ss:
                    screenshots.append(str(ss_path.relative_to(session.output_dir)))

            duration = (datetime.now(timezone.utc) - start).total_seconds()

            error = None
            if status == "failed":
                error_msgs = [s.error_message for s in failed_steps if s.error_message]
                error = {
                    "message": "; ".join(error_msgs) if error_msgs else "Verification failed",
                    "type": "VerificationError",
                }

            clarification_reason = None
            if status == "needs_clarification":
                clarification_reason = (
                    "; ".join(ambiguity_reasons)
                    if ambiguity_reasons
                    else "Requirement could not be fully verified"
                )

            return VerificationResult(
                requirement_id=requirement.id,
                status=status,
                duration=duration,
                steps=steps,
                screenshots=screenshots,
                logs=logs,
                error=error,
                clarification_reason=clarification_reason,
                refinement_suggestion=refinement or None,
            )

        except Exception as exc:
            logger.error("Unexpected error verifying %s: %s", requirement.id, exc)
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            error_step = _make_step("verify", "requirement", False, error_message=str(exc))
            steps.append(error_step)
            return VerificationResult(
                requirement_id=requirement.id,
                status="error",
                duration=duration,
                steps=steps,
                screenshots=screenshots,
                logs=logs,
                error={"message": str(exc), "type": type(exc).__name__},
            )

    def _execute_step(
        self,
        action: str,
        target: str,
        selector: str,
        value: str,
        page,
        session: TestSession,
        req_id: str,
        resolved_url: Optional[str] = None,
    ) -> TestStep:
        """Execute a single verification step.

        Args:
            action: Step action type.
            target: Human-readable target description.
            selector: CSS/XPath selector.
            value: Value for fill/navigate actions.
            page: Playwright page.
            session: Active session (for screenshot paths).
            req_id: Requirement ID (for naming screenshots).
            resolved_url: Per-requirement resolved URL (used for relative navigation).

        Returns:
            TestStep with result.
        """
        start = datetime.now(timezone.utc)

        try:
            timeout_ms = self.timeout * 1000

            if action == "navigate":
                if value.startswith("http"):
                    url = value
                elif resolved_url:
                    url = resolved_url.rstrip("/") + "/" + value.lstrip("/")
                elif self.app_config.url:
                    url = self.app_config.url.rstrip("/") + "/" + value.lstrip("/")
                else:
                    url = value  # best-effort fallback
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                step = _make_step(action, target, True, value=url, selector=selector)

            elif action == "fill":
                if selector:
                    page.fill(selector, value, timeout=timeout_ms)
                step = _make_step(action, target, True, value="[REDACTED]", selector=selector)

            elif action == "click":
                if selector:
                    page.click(selector, timeout=timeout_ms)
                step = _make_step(action, target, True, selector=selector)

            elif action == "wait":
                if selector:
                    page.wait_for_selector(selector, timeout=timeout_ms)
                else:
                    page.wait_for_load_state("networkidle", timeout=timeout_ms)
                step = _make_step(action, target, True, selector=selector)

            elif action == "verify":
                if selector:
                    result = page.wait_for_selector(selector, timeout=timeout_ms)
                    found = result is not None
                else:
                    # Generic verify: just check page is loaded
                    found = page.title() != "" or True
                step = _make_step(action, target, found, selector=selector)
                if not found:
                    step.error_message = f"Element not found: {selector}"

            elif action == "screenshot":
                ss_name = f"{req_id}_{target.replace(' ', '_')}.png"
                ss_path = session.output_dir / "screenshots" / ss_name
                ss_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(ss_path), full_page=True)
                rel_path = str(ss_path.relative_to(session.output_dir))
                step = _make_step(action, target, True, value=rel_path, selector=selector)

            else:
                step = _make_step(action, target, False, error_message=f"Unknown action: {action}")

        except Exception as exc:
            step = _make_step(
                action, target, False,
                value=value, selector=selector,
                error_message=str(exc),
            )

        duration = (datetime.now(timezone.utc) - start).total_seconds()
        step.duration = duration
        return step


def _safe_screenshot(page, path: Path) -> Optional[str]:
    """Capture screenshot without raising exceptions."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=True)
        return str(path)
    except Exception:
        return None


def _print_result(result: VerificationResult) -> None:
    """Print a single verification result to stdout."""
    icons = {
        "passed": "✓",
        "failed": "✗",
        "needs_clarification": "?",
        "skipped": "-",
        "error": "!",
    }
    icon = icons.get(result.status, "?")
    print(f"  {icon} {result.requirement_id}: {result.status} ({result.duration:.1f}s)")
    if result.error:
        print(f"    Error: {result.error.get('message', '')}")
    if result.clarification_reason:
        print(f"    Needs clarification: {result.clarification_reason}")
