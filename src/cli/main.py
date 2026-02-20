"""CLI entry point for the Playwright QA Agent."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

# Exit codes per contracts/cli-interface.md
EXIT_SUCCESS = 0
EXIT_FAILURES = 1
EXIT_ERROR = 2
EXIT_AUTH_FAILED = 3
EXIT_INVALID_REQUIREMENTS = 4


def _env(key: str, default: str = "") -> str:
    """Read an environment variable with the QA_AGENT_ prefix."""
    return os.environ.get(f"QA_AGENT_{key}", default)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="playwright-qa-agent",
        description=(
            "AI-powered QA agent that verifies web application requirements "
            "using Playwright."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  playwright-qa-agent --url https://app.example.com --username user --password pass requirements.md
  playwright-qa-agent --url https://staging.app.com --headed --log-level debug requirements.txt
  playwright-qa-agent --url https://app.com --format junit,json --output ./reports requirements.md

Environment variables (QA_AGENT_ prefix):
  QA_AGENT_URL, QA_AGENT_USERNAME, QA_AGENT_PASSWORD,
  QA_AGENT_BROWSER, QA_AGENT_HEADLESS, QA_AGENT_OUTPUT, QA_AGENT_LOG_LEVEL

Exit codes:
  0  All requirements verified successfully
  1  One or more requirements failed
  2  Execution error (invalid config, network failure, etc.)
  3  Authentication failed
  4  Invalid requirements file format
""",
    )

    # Positional argument
    parser.add_argument(
        "requirements_file",
        help="Path to requirements document (.txt or .md)",
    )

    # Authentication
    auth = parser.add_argument_group("Authentication")
    auth.add_argument(
        "--url",
        default=_env("URL"),
        help="Web application URL to test (env: QA_AGENT_URL)",
    )
    auth.add_argument(
        "--username",
        default=_env("USERNAME"),
        help="Login username (env: QA_AGENT_USERNAME)",
    )
    auth.add_argument(
        "--password",
        default=_env("PASSWORD"),
        help="Login password (env: QA_AGENT_PASSWORD)",
    )
    auth.add_argument(
        "--auth-state",
        default=_env("AUTH_STATE", ""),
        metavar="FILE",
        help="Path to save/load Playwright authentication state (default: .auth_state.json)",
    )

    # Browser configuration
    browser = parser.add_argument_group("Browser")
    browser.add_argument(
        "--browser",
        default=_env("BROWSER", "chromium"),
        choices=["chromium", "firefox", "webkit"],
        help="Browser type (default: chromium, env: QA_AGENT_BROWSER)",
    )

    headless_group = parser.add_mutually_exclusive_group()
    headless_group.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run in headless mode (default)",
    )
    headless_group.add_argument(
        "--headed",
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Run in headed (visible) mode",
    )

    # Output configuration
    output = parser.add_argument_group("Output")
    output.add_argument(
        "--output",
        default=_env("OUTPUT", ""),
        metavar="DIR",
        help="Output directory for reports (default: test-results/YYYY-MM-DD_HH-MM-SS)",
    )
    output.add_argument(
        "--format",
        default=_env("FORMAT", "all"),
        help="Report format(s): junit, json, html, or all (comma-separated, default: all)",
    )

    # Logging
    logging_group = parser.add_argument_group("Logging")
    logging_group.add_argument(
        "--log-level",
        default=_env("LOG_LEVEL", "info"),
        choices=["debug", "info", "warning", "error"],
        metavar="LEVEL",
        help="Logging verbosity: debug, info, warning, error (default: info)",
    )
    logging_group.add_argument(
        "--log-file",
        default=_env("LOG_FILE", ""),
        metavar="FILE",
        help="Path to log file (default: <output>/logs/test_execution.log)",
    )

    # Advanced options
    advanced = parser.add_argument_group("Advanced")
    advanced.add_argument(
        "--timeout",
        type=int,
        default=int(_env("TIMEOUT", "30")),
        metavar="SECONDS",
        help="Per-requirement timeout in seconds (default: 30)",
    )
    advanced.add_argument(
        "--retries",
        type=int,
        default=int(_env("RETRIES", "0")),
        metavar="COUNT",
        help="Number of retries for failed tests (default: 0)",
    )
    advanced.add_argument(
        "--screenshot-on",
        default=_env("SCREENSHOT_ON", "always"),
        choices=["always", "failure", "never"],
        metavar="WHEN",
        help="When to capture screenshots: always, failure, never (default: always)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    return parser


def validate_args(args: argparse.Namespace) -> Optional[str]:
    """Validate parsed arguments.

    Returns:
        Error message string if invalid, None if valid.
    """
    # Validate requirements file
    req_file = Path(args.requirements_file)
    if not req_file.exists():
        return (
            f"Requirements file '{req_file}' not found. "
            "Please provide a valid .txt or .md file."
        )

    if req_file.suffix.lower() not in (".txt", ".md"):
        return (
            f"Unsupported requirements file format: '{req_file.suffix}'. "
            "Please provide a .txt or .md file."
        )

    # Validate URL
    if not args.url:
        return (
            "--url is required (or set QA_AGENT_URL environment variable). "
            "Example: --url https://app.example.com"
        )

    if not (args.url.startswith("http://") or args.url.startswith("https://")):
        return (
            f"--url must start with http:// or https://, got: '{args.url}'"
        )

    # Validate credentials (required unless auth-state provided)
    auth_state = getattr(args, "auth_state", "") or ""
    if not auth_state:
        if not args.username:
            return (
                "--username is required (or set QA_AGENT_USERNAME). "
                "Example: --username testuser"
            )
        if not args.password:
            return (
                "--password is required (or set QA_AGENT_PASSWORD). "
                "Note: use environment variable QA_AGENT_PASSWORD to avoid shell history."
            )

    return None


def _parse_formats(format_str: str) -> List[str]:
    """Parse the --format argument into a list."""
    parts = [p.strip().lower() for p in format_str.split(",")]
    if "all" in parts:
        return ["json", "junit", "html"]
    return parts


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0-4).
    """
    parser = build_parser()
    args = parser.parse_args()

    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"ERROR: {error}", file=sys.stderr)
        return EXIT_ERROR

    # Set up logging early
    from src.lib.logger import setup_logger
    log_file = Path(args.log_file) if args.log_file else None
    logger = setup_logger(level=args.log_level, log_file=log_file)

    print("Playwright QA Agent v1.0.0")
    print("=" * 40)

    # Parse requirements
    from src.services.parser_service import ParserService
    try:
        parser_svc = ParserService()
        requirements_doc = parser_svc.parse_requirements(Path(args.requirements_file))
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INVALID_REQUIREMENTS
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INVALID_REQUIREMENTS

    print(f"Loading requirements from: {args.requirements_file}")
    print(f"Found {len(requirements_doc.requirements)} requirements")
    print()

    # Set up output directory
    output_base = Path(args.output) if args.output else Path("test-results")
    from src.lib.file_utils import ensure_dir
    ensure_dir(output_base)

    # Set up web application config
    from src.models.web_application import WebApplication
    app_config = WebApplication(
        url=args.url,
        username=args.username or "",
        password=args.password or "",
        session_storage=args.auth_state or None,
    )

    print(f"Testing against: {args.url}")
    print(f"Browser: {args.browser} ({'headless' if args.headless else 'headed'})")
    print()

    # Create services
    from src.services.agent_service import AgentService
    from src.services.browser_service import BrowserService
    from src.services.report_service import ReportService

    agent_svc = AgentService(
        requirements_doc=requirements_doc,
        app_config=app_config,
        timeout=args.timeout,
        screenshot_on=args.screenshot_on,
    )

    # Create test session
    session = agent_svc.create_session(
        output_base=output_base,
        browser_type=args.browser,
        headless=args.headless,
    )

    # Set up log file in session output dir if not specified
    if not log_file:
        log_file = session.output_dir / "logs" / "test_execution.log"
        setup_logger(level=args.log_level, log_file=log_file)

    browser_svc = BrowserService(browser_type=args.browser, headless=args.headless)

    try:
        browser_svc.launch()

        # Authenticate
        print("Authenticating...")
        context = browser_svc.new_context()

        # Try to load saved auth state
        auth_state_path = Path(args.auth_state) if args.auth_state else None
        if auth_state_path and auth_state_path.exists():
            state = browser_svc.load_auth_state(auth_state_path)
            if state:
                context.close()
                context = browser_svc.new_context(storage_state=state)
                print("  Loaded saved authentication state")
        else:
            page = context.new_page()
            authenticated = browser_svc.authenticate(page, app_config)
            if not authenticated:
                print(
                    "ERROR: Authentication failed. Check --username and --password.",
                    file=sys.stderr,
                )
                session.fail()
                browser_svc.close()
                return EXIT_AUTH_FAILED

            # Save auth state if requested
            if auth_state_path:
                browser_svc.save_auth_state(context, auth_state_path)

            page.close()

        context.close()

        print("  Login successful")
        print()
        print("Running tests:")

        # Verify requirements
        results = agent_svc.verify_requirements(browser_svc, session)
        agent_svc.complete_session(session, results)

    except Exception as exc:
        logger.error("Unexpected error during test execution: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        session.fail()
        browser_svc.close()
        return EXIT_ERROR
    finally:
        browser_svc.close()

    # Generate reports
    from src.models.test_report import TestReport
    report_svc = ReportService()
    formats = _parse_formats(args.format)

    test_report = TestReport.from_results(
        session_id=session.session_id,
        duration=session.duration or 0.0,
        results=results,
        environment=session.environment,
    )

    generated_files = report_svc.generate_all(test_report, session.output_dir, formats)
    test_report.files = generated_files

    # Print summary
    summary = test_report.summary
    print()
    print("Summary:")
    print("=" * 40)
    print(f"Total:      {summary.total}")
    print(f"Passed:     {summary.passed} ({summary.pass_rate * 100:.0f}%)")
    print(f"Failed:     {summary.failed}")
    print(f"Clarify:    {summary.needs_clarification}")
    print(f"Errors:     {summary.errors}")
    print(f"Duration:   {test_report.duration:.1f}s")
    print()

    if generated_files:
        print("Reports generated:")
        for fmt, path in generated_files.items():
            print(f"  {fmt}: {path}")
    print()

    # Determine exit code
    if summary.errors > 0:
        exit_code = EXIT_ERROR
    elif summary.failed > 0:
        exit_code = EXIT_FAILURES
    else:
        exit_code = EXIT_SUCCESS

    print(f"Exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
