# Playwright QA Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered QA agent that verifies web application requirements using Playwright and Claude AI. Provide a requirements document and a web app URL, and the agent will log in, navigate, and produce a detailed verification report.

## Features

- **Automated requirement verification** against live web applications
- **AI-powered test interpretation** via the Claude SDK
- **Multiple output formats**: JSON, JUnit XML (CI/CD ready), HTML
- **Ambiguity detection** with actionable refinement suggestions
- **Configurable browsers**: Chromium, Firefox, WebKit
- **CI/CD integration** with proper exit codes and machine-readable output
- **Environment variable support** for secret management

## Installation

### Prerequisites

- Python 3.11 or higher
- [UV package manager](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip

### Step 1: Install the package

```bash
# Using UV (recommended)
uv add playwright-qa-agent

# Or using pip
pip install playwright-qa-agent
```

### Step 2: Install browser binaries

```bash
# Install all browsers
playwright install

# On Linux, include system dependencies
playwright install --with-deps
```

### Step 3: Verify installation

```bash
playwright-qa-agent --version
```

## Quick Start

1. **Create a requirements file** (`requirements.md`):

```markdown
1. **Login**: User can log in with valid credentials
   - Given: User is on the login page
   - When: User enters valid username and password and clicks Login
   - Then: User is redirected to the dashboard

2. **Dashboard**: Dashboard displays user name after login
   - Given: User is logged in
   - When: User views the dashboard
   - Then: The page shows the user's name
```

2. **Run verification**:

```bash
playwright-qa-agent requirements.md \
  --url https://your-app.example.com \
  --username testuser \
  --password testpass
```

3. **View results** in `test-results/` directory (JSON, JUnit XML, HTML reports).

## CLI Usage

```
playwright-qa-agent [OPTIONS] requirements_file

Positional Arguments:
  requirements_file       Path to requirements document (.txt or .md)

Authentication:
  --url URL               Web application URL to test
  --username USERNAME     Login username
  --password PASSWORD     Login password
  --auth-state FILE       Path to save/load Playwright auth state

Browser:
  --browser {chromium,firefox,webkit}
                          Browser type (default: chromium)
  --headless / --headed   Run in headless or headed mode (default: headless)

Output:
  --output DIR            Output directory (default: test-results/YYYY-MM-DD_HH-MM-SS)
  --format FORMAT         Report formats: json, junit, html, or all (default: all)

Logging:
  --log-level LEVEL       Verbosity: debug, info, warning, error (default: info)
  --log-file FILE         Path to log file

Advanced:
  --timeout SECONDS       Per-requirement timeout in seconds (default: 30)
  --retries COUNT         Retries for failed tests (default: 0)
  --screenshot-on WHEN    When to capture: always, failure, never (default: always)
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All requirements passed |
| 1 | One or more requirements failed |
| 2 | Execution error (network, config, etc.) |
| 3 | Authentication failed |
| 4 | Invalid requirements file format |

## Environment Variables

All CLI options can be set via environment variables with the `QA_AGENT_` prefix:

```bash
export QA_AGENT_URL=https://app.example.com
export QA_AGENT_USERNAME=testuser
export QA_AGENT_PASSWORD=secretpass   # use env vars to avoid shell history
export QA_AGENT_BROWSER=chromium
export QA_AGENT_LOG_LEVEL=info

playwright-qa-agent requirements.md
```

## Requirements File Format

### Plain Text (`.txt`)

```
1. User can log in with valid credentials
   - Given: User is on the login page
   - When: User submits valid credentials
   - Then: User is redirected to the dashboard

2. User can view their profile
```

### Markdown (`.md`)

```markdown
## REQ-001: User Authentication

User can log in with valid credentials.

**Given**: User is on the login page
**When**: User enters valid username and password
**Then**: User is redirected to the dashboard
```

## CI/CD Integration

See [docs/ci-cd-integration.md](docs/ci-cd-integration.md) for complete examples with GitHub Actions, GitLab CI, Jenkins, and Azure DevOps.

**Quick GitHub Actions example**:

```yaml
- name: Run QA verification
  env:
    QA_AGENT_PASSWORD: ${{ secrets.QA_PASSWORD }}
  run: |
    playwright-qa-agent requirements.md \
      --url ${{ vars.APP_URL }} \
      --username ${{ vars.QA_USERNAME }} \
      --format all \
      --output test-results

- name: Publish test results
  uses: actions/upload-artifact@v4
  with:
    name: qa-reports
    path: test-results/
```

## Documentation

- [Quickstart Guide](specs/001-playwright-qa-agent/quickstart.md)
- [CI/CD Integration](docs/ci-cd-integration.md)
- [Specification](specs/001-playwright-qa-agent/spec.md)

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run linting
ruff check .

# Run tests
pytest tests/unit/

# Run integration tests (requires a running web app)
pytest tests/integration/
```

## License

MIT
