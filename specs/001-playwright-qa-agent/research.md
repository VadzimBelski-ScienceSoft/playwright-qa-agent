# Research: Playwright QA Agent

**Phase**: 0 - Technical Research
**Date**: 2026-02-20
**Status**: Complete

## Overview

This document consolidates research findings for building an AI-powered QA agent that automates web application testing using Claude SDK and Playwright.

## Technology Stack Decisions

### 1. AI Agent Framework

**Decision**: Use Claude Agent SDK (`claude-agent-sdk`)

**Package**: `claude-agent-sdk` v0.1.39+
**Installation**: `uv add claude-agent-sdk`
**Python Requirement**: 3.10+ (compatible with our 3.11+ requirement)

**Rationale**:
- Official Anthropic SDK for building AI agents
- Built-in tool system for file operations, bash commands, web interaction
- Supports stateful conversations for iterative requirement refinement
- Permission modes for controlled automation (important for CI/CD)
- Specialized subagent pattern for complex workflows
- UV package manager compatible

**Key Capabilities**:
- `query()` function for stateless operations
- `ClaudeSDKClient` class for stateful conversations (needed for requirement refinement)
- Built-in tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
- Custom tool integration via `@tool` decorator
- Hooks for pre/post tool execution (useful for logging)

### 2. Browser Automation

**Decision**: Use Playwright for Python (`playwright`)

**Package**: `playwright` v1.58.0+
**Installation**: `uv add playwright && playwright install`
**Python Requirement**: 3.8+

**Rationale**:
- Official Microsoft browser automation library
- Headless mode by default (CI/CD ready)
- Cross-platform (Linux, macOS, Windows including ARM64)
- Auto-waiting for elements (reduces flaky tests)
- Built-in screenshot and tracing capabilities
- Supports SPAs with networkidle wait states
- Handles authentication state persistence

**Key Features for This Project**:
- Login form automation via semantic locators
- Screenshot capture for test evidence
- Network idle detection for AJAX/SPA content
- iframe handling with `frameLocator()`
- Cross-platform compatibility verified

### 3. Requirements Parsing

**Decision**: Use Mistune for Markdown parsing

**Package**: `mistune` v3.0+
**Installation**: `uv add mistune`
**Dependencies**: Zero

**Rationale**:
- Zero external dependencies (pure Python)
- Fastest pure Python markdown parser
- Lightweight and simple (aligns with constitution)
- CommonMark compliant
- For plain text requirements, use built-in `re` module (no additional dependency)

**Alternative Considered**: Python-Markdown (rejected - less performant, more dependencies)

### 4. Report Generation

**Decision**: Multi-format reporting approach

**Packages**:
- JUnit XML: `junit-xml` (minimal dependencies, only `six`)
- JSON: Python built-in `json` module (zero dependencies)
- Custom HTML: Generate programmatically (no framework)

**Installation**: `uv add junit-xml`

**Rationale**:
- `junit-xml` is framework-agnostic (not tied to pytest/unittest)
- Direct API for creating test cases and suites
- Minimal footprint (single dependency on `six`)
- JSON using stdlib avoids dependencies
- pytest-json-report considered but rejected (adds pytest dependency when we want standalone CLI)

**Report Formats**:
1. **JUnit XML**: For CI/CD integration (Jenkins, GitHub Actions, GitLab CI)
2. **JSON**: For programmatic access and detailed data
3. **HTML**: For human-readable reports (generated from JSON)

### 5. Logging

**Decision**: Python standard library `logging`

**Package**: Built-in (no additional dependency)

**Rationale**:
- Zero dependencies
- Flexible configuration
- Cross-platform
- Sufficient for requirement logging and debugging

## Architecture Patterns

### Agent Orchestration Pattern

```
User provides:
├── Requirements Document (.txt or .md)
├── Web Application URL
└── Login Credentials

↓

Claude Agent (Orchestrator):
├── Parse requirements using Mistune/regex
├── For each requirement:
│   ├── Use Playwright to interact with app
│   ├── Verify UI elements and behaviors
│   ├── Capture screenshots as evidence
│   ├── Log all actions
│   └── Classify result (passed/failed/needs_clarification)
├── Identify ambiguous requirements
└── Generate reports (JUnit XML + JSON)

↓

Output:
├── Test Report (JUnit XML for CI/CD)
├── Detailed Report (JSON)
├── Screenshots (PNG files)
└── Execution Logs
```

### Specialized Subagent Pattern (Optional Enhancement)

Based on Playwright's official agent architecture:

- **Planner Agent**: Analyzes requirements and creates test strategy
- **Generator Agent**: Executes tests via Playwright
- **Healer Agent**: Analyzes failures and suggests refinements

This pattern can be implemented if needed for iterative refinement (User Story 2 - P2).

## Implementation Approach

### Requirements Parsing Strategy

**Format Support**:
1. **Plain Text (.txt)**: Use regex patterns to identify requirements
2. **Markdown (.md)**: Use Mistune + regex for structured parsing

**Parsing Patterns**:
- Numbered lists: `1. Requirement text`
- Section headers: `## REQ-001: Requirement title`
- Given/When/Then: Regex patterns for acceptance criteria

**Code Approach**:
```python
# Simple regex for 90% of cases
pattern = r'^(\d+)\.\s+(?:\*\*([^*]+)\*\*:\s+)?(.+)$'

# Gherkin pattern matching
gherkin = r'(?:Given|When|Then)[\s:]+([^\n]+)'
```

No heavy NLP libraries needed - requirement parsing is pattern-based.

### Browser Automation Strategy

**Login Handling**:
- Use Playwright's `storage_state()` to save authentication
- Reuse auth state across tests (performance optimization)

**Screenshot Strategy**:
- Capture before/after critical actions
- Save with requirement ID naming: `req_001_login_success.png`
- Optimize file size (resize to max 1920px width, PNG compression)

**SPA Handling**:
- Use `page.wait_for_load_state('networkidle')` for AJAX content
- Use `page.wait_for_selector()` for specific elements

**Headless Mode**:
- Default to headless for CI/CD
- Allow headed mode via CLI flag for debugging

### Report Generation Strategy

**Directory Structure**:
```
test-results/
├── YYYY-MM-DD_HH-MM-SS/    # Timestamped run
│   ├── junit.xml           # CI/CD integration
│   ├── report.json         # Detailed results
│   ├── report.html         # Human-readable
│   ├── screenshots/        # Evidence
│   └── logs/               # Execution logs
└── latest -> [symlink]     # Points to most recent
```

**JUnit XML Format**:
- Use `<testcase>` for each requirement
- Add `<properties>` for requirement metadata
- Include screenshot paths in `<system-out>`
- Support attachment markers: `[[ATTACHMENT|path]]`

**JSON Format**:
```json
{
  "summary": {"total": 50, "passed": 45, "failed": 3, ...},
  "requirements": [
    {
      "id": "REQ-001",
      "status": "passed",
      "screenshots": ["screenshots/req_001.png"],
      "logs": ["Step 1", "Step 2"],
      "duration": 2.34
    }
  ]
}
```

## Integration Patterns

### Claude SDK + Playwright Integration

**Option 1: Playwright MCP Server** (More complex, not recommended for v1)
- Requires Node.js runtime (violates constitution - non-Python dependency)
- Uses 4x more tokens than direct approach
- Adds complexity

**Option 2: Direct Playwright Python API** (RECOMMENDED)
- Use Playwright Python package directly
- Claude agent orchestrates Playwright calls
- Simpler, fewer dependencies, aligns with constitution
- Better performance (fewer tokens)

**Decision**: Use direct Playwright Python API (Option 2)

### CI/CD Integration

**GitHub Actions Example**:
```yaml
- run: |
    uv run playwright-qa-agent \
      --requirements requirements.md \
      --url https://staging.app.com \
      --username ${{ secrets.TEST_USER }} \
      --password ${{ secrets.TEST_PASS }} \
      --headless \
      --output test-results/

- uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: test-results/
```

**Exit Codes**:
- `0`: All requirements verified
- `1`: One or more requirements failed
- `2`: Execution error (invalid config, network failure)

## Performance Considerations

**Target**: Generate reports within 5 minutes for 50 requirements (SC-004)

**Optimizations**:
1. **Authentication State Reuse**: Login once, reuse for all tests
2. **Parallel Processing**: Test independent requirements concurrently (future enhancement)
3. **Screenshot Optimization**: Resize + compress images
4. **Network Idle**: Use `networkidle` only for SPAs (faster for static pages)
5. **Token Efficiency**: Direct Playwright API (vs MCP) saves ~4x tokens

**Estimated Timing**:
- Authentication: 5-10 seconds (one-time)
- Per requirement test: 3-6 seconds average
- Screenshot capture: <1 second each
- Report generation: 2-3 seconds
- **Total for 50 requirements**: ~3-5 minutes ✓

## Constraints & Limitations

### Edge Cases Identified

1. **Multi-Factor Authentication (MFA)**: Not supported in v1 (requires manual intervention)
2. **CAPTCHAs**: Cannot be automated (will fail with clear error message)
3. **Bot Detection**: May trigger on some sites (use delays, random mouse movements as mitigation)
4. **Performance Testing**: Out of scope (functional testing only)
5. **Complex iframes**: Supported via `frameLocator()` but may need manual selectors

### Security Considerations

- Credentials passed via CLI args or env vars (not stored)
- Reports should NOT contain passwords in logs
- Screenshots may contain sensitive data (user responsibility)

## Alternatives Considered & Rejected

| Alternative | Rejected Because |
|------------|------------------|
| Selenium | Playwright is faster, more modern, better async support |
| Puppeteer (Node.js) | Requires Node.js runtime (violates Python-only stack) |
| Playwright MCP Server | Requires Node.js, uses 4x more tokens, adds complexity |
| Heavy NLP libraries (spaCy) | Overkill for pattern-based requirement parsing |
| pytest-playwright | Adds pytest framework dependency (want standalone CLI) |
| BeautifulSoup for parsing | Mistune is faster and markdown-aware |
| Custom XML library | junit-xml is simpler and battle-tested |

## Dependencies Summary

**Final Package List**:
```toml
[dependencies]
claude-agent-sdk = "^0.1.39"
playwright = "^1.58.0"
mistune = "^3.0.0"
junit-xml = "^1.9"
# All other needs met by Python stdlib
```

**Total External Dependencies**: 4 packages (minimal, aligns with constitution)

**Installation Size**: ~200MB (mostly Playwright browser binaries)

## Next Steps

Phase 1 will define:
1. **Data Models**: RequirementsDocument, TestSession, TestReport, VerificationResult
2. **Contracts**: CLI interface, report schemas
3. **Quickstart Guide**: Installation, basic usage, CI/CD integration

## References

- [Claude Agent SDK Documentation](https://platform.claude.com/docs/en/agent-sdk/python)
- [Playwright Python Documentation](https://playwright.dev/python/docs/intro)
- [Mistune Documentation](https://mistune.lepture.com/)
- [JUnit XML Format Specification](https://github.com/testmoapp/junitxml)
