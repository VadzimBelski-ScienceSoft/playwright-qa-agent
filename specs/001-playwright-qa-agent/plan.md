# Implementation Plan: Playwright QA Agent

**Branch**: `001-playwright-qa-agent` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-playwright-qa-agent/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build an AI-powered QA agent that automates web application testing by reading requirements documents, using Playwright to interact with web applications, and generating detailed verification reports. The agent will verify requirements against actual application behavior, suggest refinements for ambiguous requirements, and integrate with CI/CD pipelines. Core technical approach: Python 3.11+ with UV package management, Claude SDK for AI reasoning, Playwright for browser automation, zero-config CLI tool with detailed reporting in JUnit XML and JSON formats.

## Technical Context

**Language/Version**: Python 3.11+ (per constitution requirement)
**Primary Dependencies**:
- `claude-agent-sdk` v0.1.39+ (AI agent framework)
- `playwright` v1.58.0+ (browser automation)
- `mistune` v3.0+ (Markdown parsing, zero dependencies)
- `junit-xml` v1.9+ (JUnit XML generation, minimal dependencies)
**Storage**: Local filesystem (requirements documents in .txt/.md, test reports in JSON/XML, screenshots in PNG, logs in text)
**Testing**: pytest (per constitution standard)
**Target Platform**: Cross-platform (Linux, macOS, Windows - per constitution requirement)
**Project Type**: Single CLI tool (no web frontend or mobile components)
**Performance Goals**: Generate complete test reports within 5 minutes for applications with up to 50 requirements (SC-004)
**Constraints**: Zero false positives for verified requirements (SC-007), 95%+ accuracy in requirement classification (SC-003), headless browser support for CI/CD (FR-011)
**Scale/Scope**: Support 20+ requirements per test run (SC-001), process up to 50 requirements (SC-004), handle complex web applications with dynamic content

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with constitution v1.0.0 principles:

- [x] **Simplicity First**: Is this the minimum code solution? Can it be simpler?
  - ✅ Only 4 external dependencies (claude-agent-sdk, playwright, mistune, junit-xml)
  - ✅ Using direct Playwright API (not MCP) - simpler, fewer tokens, no Node.js dependency
  - ✅ Pattern-based requirement parsing (regex) - no heavy NLP libraries
  - ✅ JSON using stdlib - no framework
  - ✅ Flat module structure (models, services, cli, lib)

- [x] **Cross-Platform**: Does this work on Linux, macOS, and Windows?
  - ✅ Python 3.11+ runs on all platforms
  - ✅ Playwright officially supports Linux, macOS, Windows (including ARM64)
  - ✅ All file paths use pathlib for cross-platform compatibility
  - ✅ No shell commands or platform-specific code
  - ✅ Headless browser works on all platforms

- [x] **UV + Python Stack**: Uses only UV and Python 3.11+, no additional tooling?
  - ✅ Python 3.11+ as implementation language
  - ✅ UV as exclusive package manager (no pip, poetry, conda)
  - ✅ No build tools (webpack, babel, etc.)
  - ✅ No non-Python runtime requirements (Node.js rejected for MCP approach)
  - ✅ pytest for testing (minimal config)

- [x] **Maintainability**: Can a new contributor understand this in 60 seconds?
  - ✅ Flat module organization (src/models, src/services, src/cli, src/lib)
  - ✅ Single responsibility per service (agent, browser, parser, report)
  - ✅ Clear data models with explicit fields
  - ✅ Self-documenting names (RequirementsDocument, VerificationResult, TestSession)
  - ✅ Standard patterns (dataclasses, type hints, pathlib)

- [x] **Usability**: Does this maintain zero-config defaults and intuitive CLI?
  - ✅ Single command installation: `uv add playwright-qa-agent`
  - ✅ Zero-config: Headless by default, sensible timeouts, automatic report generation
  - ✅ Environment variable support (QA_AGENT_USERNAME, etc.)
  - ✅ Clear error messages with actionable guidance
  - ✅ Intuitive CLI: `playwright-qa-agent --url <URL> --username <USER> --password <PASS> requirements.md`

**Complexity Justification** (required if any gate fails):

*No violations - all gates passed. No justification needed.*

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/                  # Data models (RequirementsDoc, TestSession, TestReport, etc.)
├── services/                # Core services (agent orchestration, Playwright interaction)
│   ├── agent_service.py     # Claude SDK agent orchestration
│   ├── browser_service.py   # Playwright browser automation
│   ├── parser_service.py    # Requirements document parsing
│   └── report_service.py    # Report generation (JUnit XML, JSON)
├── cli/                     # Command-line interface
│   └── main.py              # CLI entry point with zero-config defaults
└── lib/                     # Utility libraries
    ├── file_utils.py        # Cross-platform file handling (pathlib)
    └── logger.py            # Action logging for debugging

tests/
├── contract/                # Contract tests for agent behavior
├── integration/             # End-to-end tests with real browser
└── unit/                    # Unit tests for individual components

pyproject.toml               # UV dependency management
README.md                    # Installation and usage guide
```

**Structure Decision**: Single project structure selected. This is a CLI tool with no web frontend or mobile components. The flat module organization (models, services, cli, lib) ensures easy navigation and maintainability per constitution principles. All paths use pathlib for cross-platform compatibility.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: No complexity violations detected. All constitution principles are satisfied.

**Architecture Decisions**:
- **Direct Playwright API over MCP**: Simpler, faster, fewer dependencies, no Node.js requirement
- **Pattern-based parsing over NLP**: Regex sufficient for 90% of requirements, avoids heavy libraries
- **Stdlib JSON over framework**: Zero dependencies, adequate for our needs
- **Flat module structure**: Easy navigation, clear separation of concerns
