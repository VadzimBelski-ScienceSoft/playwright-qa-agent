# CLI Interface Contract

**Version**: 1.0.0
**Date**: 2026-02-20

## Overview

This document defines the command-line interface for the Playwright QA Agent. The CLI follows POSIX conventions and prioritizes zero-configuration defaults.

## Command Structure

```bash
playwright-qa-agent [OPTIONS] <REQUIREMENTS_FILE>
```

## Required Arguments

### `<REQUIREMENTS_FILE>`

Path to requirements document (.txt or .md file).

**Type**: File path
**Format**: `.txt` or `.md`
**Example**: `requirements.md` or `specs/feature-001.txt`

## Options

### Authentication

#### `--url <URL>`

**Description**: Web application URL to test
**Required**: Yes
**Type**: URL (http:// or https://)
**Example**: `--url https://staging.app.example.com`

#### `--username <USERNAME>`

**Description**: Login username
**Required**: Yes
**Type**: String
**Example**: `--username testuser`
**Environment Variable**: `QA_AGENT_USERNAME`

#### `--password <PASSWORD>`

**Description**: Login password
**Required**: Yes
**Type**: String
**Example**: `--password secret123`
**Environment Variable**: `QA_AGENT_PASSWORD`
**Security**: Never log this value

#### `--auth-state <FILE>`

**Description**: Path to save/load Playwright authentication state
**Required**: No
**Type**: File path
**Default**: `.auth_state.json`
**Example**: `--auth-state ./auth/session.json`

### Browser Configuration

#### `--browser <TYPE>`

**Description**: Browser type to use
**Required**: No
**Type**: Enum (`chromium`, `firefox`, `webkit`)
**Default**: `chromium`
**Example**: `--browser firefox`

#### `--headless`

**Description**: Run browser in headless mode
**Required**: No
**Type**: Boolean flag
**Default**: `true` (headless by default)
**Example**: `--headless` (explicit) or `--no-headless` (headed mode)

#### `--headed`

**Description**: Run browser in headed mode (alias for `--no-headless`)
**Required**: No
**Type**: Boolean flag
**Default**: `false`
**Example**: `--headed`

### Output Configuration

#### `--output <DIR>`

**Description**: Output directory for reports and screenshots
**Required**: No
**Type**: Directory path
**Default**: `test-results/YYYY-MM-DD_HH-MM-SS`
**Example**: `--output ./reports/run-001`

#### `--format <FORMAT>`

**Description**: Report format(s) to generate
**Required**: No
**Type**: Comma-separated list (`junit`, `json`, `html`, `all`)
**Default**: `all`
**Example**: `--format junit,json`

### Logging

#### `--log-level <LEVEL>`

**Description**: Logging verbosity
**Required**: No
**Type**: Enum (`debug`, `info`, `warning`, `error`)
**Default**: `info`
**Example**: `--log-level debug`

#### `--log-file <FILE>`

**Description**: Path to log file
**Required**: No
**Type**: File path
**Default**: `<output>/logs/test_execution.log`
**Example**: `--log-file ./qa-agent.log`

### Advanced Options

#### `--timeout <SECONDS>`

**Description**: Global timeout for each requirement test
**Required**: No
**Type**: Integer (seconds)
**Default**: `30`
**Example**: `--timeout 60`

#### `--retries <COUNT>`

**Description**: Number of retries for flaky tests
**Required**: No
**Type**: Integer
**Default**: `0` (no retries)
**Example**: `--retries 2`

#### `--screenshot-on <WHEN>`

**Description**: When to capture screenshots
**Required**: No
**Type**: Enum (`always`, `failure`, `never`)
**Default**: `always`
**Example**: `--screenshot-on failure`

#### `--version`

**Description**: Show version and exit
**Required**: No
**Type**: Boolean flag

#### `--help`

**Description**: Show help message and exit
**Required**: No
**Type**: Boolean flag

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All requirements verified successfully |
| `1` | One or more requirements failed |
| `2` | Execution error (invalid config, network failure, etc.) |
| `3` | Authentication failed |
| `4` | Invalid requirements file format |

## Examples

### Basic Usage

```bash
playwright-qa-agent \
  --url https://staging.app.com \
  --username testuser \
  --password secret123 \
  requirements.md
```

### CI/CD Usage

```bash
# Using environment variables for credentials
export QA_AGENT_USERNAME=testuser
export QA_AGENT_PASSWORD=secret123

playwright-qa-agent \
  --url https://staging.app.com \
  --headless \
  --format junit,json \
  --output ./test-results \
  requirements.txt
```

### Debugging Usage

```bash
playwright-qa-agent \
  --url http://localhost:3000 \
  --username admin \
  --password admin123 \
  --headed \
  --log-level debug \
  --screenshot-on always \
  requirements.md
```

### Reusing Authentication

```bash
# First run: saves auth state
playwright-qa-agent \
  --url https://app.com \
  --username user \
  --password pass \
  --auth-state ./auth.json \
  requirements.md

# Subsequent runs: reuses auth (faster)
playwright-qa-agent \
  --url https://app.com \
  --auth-state ./auth.json \
  requirements.md
```

## Environment Variables

All options can be set via environment variables with `QA_AGENT_` prefix:

| Environment Variable | CLI Option |
|---------------------|------------|
| `QA_AGENT_URL` | `--url` |
| `QA_AGENT_USERNAME` | `--username` |
| `QA_AGENT_PASSWORD` | `--password` |
| `QA_AGENT_BROWSER` | `--browser` |
| `QA_AGENT_HEADLESS` | `--headless` |
| `QA_AGENT_OUTPUT` | `--output` |
| `QA_AGENT_LOG_LEVEL` | `--log-level` |

CLI arguments take precedence over environment variables.

## Output

### Standard Output

Progress indicators and summary:

```
Playwright QA Agent v1.0.0
===========================

Loading requirements from: requirements.md
Found 50 requirements

Testing against: https://staging.app.com
Browser: Chromium (headless)

Authenticating...
✓ Login successful

Running tests:
✓ REQ-001: User can login with valid credentials (2.3s)
✓ REQ-002: Dashboard displays user statistics (1.8s)
✗ REQ-003: User can export reports (4.5s)
  Error: Export button not found
? REQ-004: Settings page shows preferences (1.2s)
  Needs clarification: Found multiple "Settings" links

[... progress for all requirements ...]

Summary:
========
Total:      50
Passed:     45 (90%)
Failed:     3  (6%)
Clarify:    2  (4%)
Duration:   267.5s

Reports generated:
  JUnit XML: test-results/2026-02-20_14-30-45/junit.xml
  JSON:      test-results/2026-02-20_14-30-45/report.json
  HTML:      test-results/2026-02-20_14-30-45/report.html

Exit code: 1 (failures detected)
```

### Standard Error

Errors and warnings only:

```
ERROR: Failed to connect to https://invalid-url.com
WARNING: Screenshot for REQ-025 exceeds 5MB, consider optimizing
```

## Validation Rules

### Required Options

When `--auth-state` is NOT provided:
- `--url` is required
- `--username` is required
- `--password` is required

When `--auth-state` is provided:
- `--url` is required
- `--username` and `--password` are optional (auth state used instead)

### File Validation

- `<REQUIREMENTS_FILE>` must exist and be readable
- `<REQUIREMENTS_FILE>` must have `.txt` or `.md` extension
- `--output` directory will be created if it doesn't exist
- `--auth-state` file will be created on first run

### URL Validation

- `--url` must be valid HTTP or HTTPS URL
- `--url` must be reachable (network check performed)

## Error Messages

### Clear, Actionable Errors

❌ **Bad**: "Invalid input"
✅ **Good**: "Requirements file 'reqs.md' not found. Please provide a valid .txt or .md file."

❌ **Bad**: "Auth failed"
✅ **Good**: "Authentication failed: Invalid credentials for user 'testuser'. Please check --username and --password."

❌ **Bad**: "Timeout"
✅ **Good**: "REQ-042 timed out after 30 seconds while waiting for element '.dashboard-widget'. Try increasing --timeout or check if element exists."

## Future Enhancements (Not in v1)

- `--parallel <N>`: Run N requirements in parallel
- `--filter <PATTERN>`: Test only requirements matching pattern
- `--skip <REQ_ID>`: Skip specific requirements
- `--config <FILE>`: Load options from YAML/JSON config file
- `--dry-run`: Parse requirements without testing
- `--watch`: Re-run tests on requirements file changes

## Compliance with Constitution

- **Simplicity**: Zero-config defaults, minimal required options
- **Cross-Platform**: All paths use pathlib, works on Linux/macOS/Windows
- **Usability**: Clear error messages, sensible defaults, environment variable support
- **UV Integration**: Installed via `uv add playwright-qa-agent`, runs via `uv run`
