"""Report service for generating test reports in multiple formats."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import List

from src.lib.logger import get_logger
from src.models.test_report import TestReport

logger = get_logger(__name__)


class ReportService:
    """Generates test reports in JSON, JUnit XML, and HTML formats."""

    def generate_json_report(self, test_report: TestReport, output_path: Path) -> Path:
        """Generate a JSON report from a TestReport.

        Args:
            test_report: The TestReport to serialize.
            output_path: Path for the output JSON file.

        Returns:
            Path to the written JSON file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = test_report.to_dict()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("JSON report written: %s", output_path)
        return output_path

    def generate_junit_xml(self, test_report: TestReport, output_path: Path) -> Path:
        """Generate a JUnit XML report from a TestReport.

        Args:
            test_report: The TestReport to serialize.
            output_path: Path for the output XML file.

        Returns:
            Path to the written XML file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from junit_xml import TestCase, TestSuite  # type: ignore

            cases = []

            for result in test_report.results:
                case = TestCase(
                    name=result.requirement_id,
                    classname="requirements",
                    elapsed_sec=result.duration,
                    stdout="\n".join(result.logs or []),
                )

                # Add screenshots as attachments in stdout
                if result.screenshots:
                    attachments = "\n".join(
                        f"[[ATTACHMENT|{ss}]]" for ss in result.screenshots
                    )
                    case.stdout = attachments + "\n" + (case.stdout or "")

                if result.status == "failed":
                    error = result.error or {}
                    case.add_failure_info(
                        message=error.get("message", "Verification failed"),
                        output=error.get("traceback", ""),
                        failure_type=error.get("type", "VerificationError"),
                    )
                elif result.status == "error":
                    error = result.error or {}
                    case.add_error_info(
                        message=error.get("message", "Execution error"),
                        output=error.get("traceback", ""),
                        error_type=error.get("type", "ExecutionError"),
                    )
                elif result.status in ("needs_clarification", "skipped"):
                    case.add_skipped_info(
                        message=(
                            result.clarification_reason
                            or "Needs clarification"
                        )
                    )

                cases.append(case)

            env = test_report.environment
            suite = TestSuite(
                name="Requirements Verification",
                test_cases=cases,
                hostname=socket.gethostname(),
                timestamp=test_report.created.isoformat(),
                properties={
                    "session_id": test_report.session_id,
                    "python_version": env.get("python_version", ""),
                    "playwright_version": env.get("playwright_version", ""),
                    "platform": env.get("platform", ""),
                },
            )

            xml_str = TestSuite.to_xml_string([suite], prettyprint=True)
            output_path.write_text(xml_str, encoding="utf-8")

        except ImportError:
            logger.warning("junit-xml not available, generating basic XML")
            xml_str = self._generate_basic_junit_xml(test_report)
            output_path.write_text(xml_str, encoding="utf-8")

        logger.info("JUnit XML report written: %s", output_path)
        return output_path

    def _generate_basic_junit_xml(self, test_report: TestReport) -> str:
        """Generate basic JUnit XML without external library."""
        summary = test_report.summary
        created = test_report.created.isoformat()
        hostname = socket.gethostname()

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<testsuites name="Playwright QA Agent Test Suite"'
                f' tests="{summary.total}"'
                f' failures="{summary.failed}"'
                f' errors="{summary.errors}"'
                f' skipped="{summary.needs_clarification + summary.skipped}"'
                f' time="{test_report.duration:.3f}">'
            ),
            (
                f'  <testsuite name="Requirements Verification"'
                f' tests="{summary.total}"'
                f' failures="{summary.failed}"'
                f' errors="{summary.errors}"'
                f' skipped="{summary.needs_clarification + summary.skipped}"'
                f' time="{test_report.duration:.3f}"'
                f' timestamp="{created}"'
                f' hostname="{_escape_xml(hostname)}">'
            ),
        ]

        for result in test_report.results:
            req_id = result.requirement_id
            case_name = _escape_xml(req_id)
            lines.append(
                f'    <testcase classname="requirements"'
                f' name="{case_name}"'
                f' time="{result.duration:.3f}">'
            )

            logs_content = "\n".join(result.logs or [])
            if result.screenshots:
                attachments = "\n".join(
                    f"[[ATTACHMENT|{ss}]]" for ss in result.screenshots
                )
                logs_content = attachments + "\n" + logs_content

            if result.status == "failed":
                error = result.error or {}
                msg = _escape_xml(error.get("message", "Verification failed"))
                etype = _escape_xml(error.get("type", "VerificationError"))
                lines.append(f'      <failure message="{msg}" type="{etype}"/>')
            elif result.status == "error":
                error = result.error or {}
                msg = _escape_xml(error.get("message", "Execution error"))
                etype = _escape_xml(error.get("type", "ExecutionError"))
                lines.append(f'      <error message="{msg}" type="{etype}"/>')
            elif result.status in ("needs_clarification", "skipped"):
                reason = _escape_xml(
                    result.clarification_reason or "Needs clarification"
                )
                lines.append(f'      <skipped message="{reason}"/>')

            if logs_content:
                lines.append(f"      <system-out><![CDATA[{logs_content}]]></system-out>")

            lines.append("    </testcase>")

        lines.append("  </testsuite>")
        lines.append("</testsuites>")
        return "\n".join(lines)

    def generate_html_report(self, test_report: TestReport, output_path: Path) -> Path:
        """Generate an HTML report from a TestReport.

        Args:
            test_report: The TestReport to render.
            output_path: Path for the output HTML file.

        Returns:
            Path to the written HTML file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = self._render_html(test_report)
        output_path.write_text(html, encoding="utf-8")
        logger.info("HTML report written: %s", output_path)
        return output_path

    def _render_html(self, report: TestReport) -> str:
        """Render the test report as an HTML string."""
        summary = report.summary
        pass_pct = f"{summary.pass_rate * 100:.1f}"

        status_colors = {
            "passed": "#28a745",
            "failed": "#dc3545",
            "needs_clarification": "#ffc107",
            "skipped": "#6c757d",
            "error": "#fd7e14",
        }

        rows = []
        for result in report.results:
            color = status_colors.get(result.status, "#6c757d")
            req_id = _escape_html(result.requirement_id)
            status = _escape_html(result.status)
            duration = f"{result.duration:.2f}s"

            notes = ""
            if result.error:
                notes = _escape_html(result.error.get("message", ""))
            elif result.clarification_reason:
                notes = _escape_html(result.clarification_reason)

            refinement = ""
            if result.refinement_suggestion:
                refinement = (
                    f'<br><small><em>Suggestion: '
                    f'{_escape_html(result.refinement_suggestion)}</em></small>'
                )

            rows.append(
                f"<tr>"
                f'<td>{req_id}</td>'
                f'<td><span style="color:{color};font-weight:bold">{status}</span></td>'
                f"<td>{duration}</td>"
                f"<td>{notes}{refinement}</td>"
                f"</tr>"
            )

        rows_html = "\n".join(rows)
        created = report.created.strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Playwright QA Agent Report</title>
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
    h1 {{ color: #333; }}
    .summary {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
    .stat {{ background: white; padding: 15px 25px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
    .stat .label {{ color: #666; font-size: 0.85em; }}
    .stat .value {{ font-size: 2em; font-weight: bold; }}
    .passed {{ color: #28a745; }}
    .failed {{ color: #dc3545; }}
    .needs_clarification {{ color: #ffc107; }}
    .error {{ color: #fd7e14; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    th {{ background: #495057; color: white; padding: 12px 15px; text-align: left; }}
    td {{ padding: 10px 15px; border-bottom: 1px solid #dee2e6; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f8f9fa; }}
    .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
  </style>
</head>
<body>
  <h1>Playwright QA Agent Report</h1>
  <div class="meta">
    Session: {_escape_html(report.session_id)} &bull;
    Created: {_escape_html(created)} &bull;
    Duration: {report.duration:.1f}s
  </div>
  <div class="summary">
    <div class="stat"><div class="value">{summary.total}</div><div class="label">Total</div></div>
    <div class="stat"><div class="value passed">{summary.passed}</div><div class="label">Passed</div></div>
    <div class="stat"><div class="value failed">{summary.failed}</div><div class="label">Failed</div></div>
    <div class="stat"><div class="value needs_clarification">{summary.needs_clarification}</div><div class="label">Clarify</div></div>
    <div class="stat"><div class="value error">{summary.errors}</div><div class="label">Errors</div></div>
    <div class="stat"><div class="value">{pass_pct}%</div><div class="label">Pass Rate</div></div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Requirement</th>
        <th>Status</th>
        <th>Duration</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</body>
</html>
"""

    def generate_all(
        self,
        test_report: TestReport,
        output_dir: Path,
        formats: List[str] | None = None,
    ) -> dict:
        """Generate reports in all requested formats.

        Args:
            test_report: The TestReport to generate from.
            output_dir: Directory to write reports in.
            formats: List of formats: json, junit, html. Default: all.

        Returns:
            Dict mapping format name to output Path.
        """
        if formats is None or "all" in formats:
            formats = ["json", "junit", "html"]

        output_dir = Path(output_dir)
        generated = {}

        if "json" in formats:
            path = self.generate_json_report(test_report, output_dir / "report.json")
            generated["json"] = str(path)

        if "junit" in formats:
            path = self.generate_junit_xml(test_report, output_dir / "junit.xml")
            generated["junit_xml"] = str(path)

        if "html" in formats:
            path = self.generate_html_report(test_report, output_dir / "report.html")
            generated["html"] = str(path)

        return generated


def _escape_xml(s: str) -> str:
    """Escape special characters for XML attributes."""
    return (
        s.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&apos;")
    )


def _escape_html(s: str) -> str:
    """Escape special characters for HTML content."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
