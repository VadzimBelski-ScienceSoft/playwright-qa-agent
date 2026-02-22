# Quickstart Guide: Playwright QA Agent

**Version**: 1.0.0
**Date**: 2026-02-20

## Overview

The Playwright QA Agent is an AI-powered tool that automates web application testing by reading requirements documents and verifying them against actual application behavior. This guide will get you up and running in under 5 minutes.

## Prerequisites

- **Python**: 3.11 or higher
- **UV Package Manager**: [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
- **Anthropic API key**: [Anthropic Console](https://console.anthropic.com/) (required for AI-powered verification)
- **Operating System**: Linux, macOS, or Windows
- **Network Access**: To target web applications

## Installation

### Step 1: Install the Package

```bash
# Using UV (recommended)
uv add playwright-qa-agent

# Alternatively, using pip
pip install playwright-qa-agent
```

### Step 2: Install Browser Binaries

```bash
# Install Playwright browsers
playwright install

# Or with system dependencies (Linux)
playwright install --with-deps
```

**Installation Size**: ~200MB (includes Chromium, Firefox, WebKit browsers)

### Step 3: Verify Installation

```bash
playwright-qa-agent --version
```

Expected output:
```
Playwright QA Agent v1.0.0
```

## API Key Setup

The Playwright QA Agent uses Claude AI for intelligent test interpretation. You need an Anthropic API key to use it.

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Set the environment variable:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

> **Important**: Store your API key securely. Never commit it to version control.

## Quick Start (5 Minutes)

### 1. Create a Requirements Document

Create a file named `requirements.md`:

```markdown
# Login Requirements

1. **User Login**: User can login with valid credentials
   - Given: User is on the login page
   - When: User enters valid username and password
   - Then: User is redirected to the dashboard

2. **Dashboard Load**: Dashboard displays user statistics
   - Given: User is logged in
   - When: User navigates to dashboard
   - Then: Statistics widgets are visible

3. **User Profile**: User can view their profile
   - Given: User is logged in
   - When: User clicks on profile link
   - Then: Profile page shows user information
```

### 2. Run the Agent

```bash
playwright-qa-agent \
  --url https://your-app.com \
  --username testuser \
  --password testpass123 \
  requirements.md
```

### 3. View Results

The agent will:
1. Parse your requirements
2. Log into the application
3. Test each requirement
4. Generate reports

Output:
```
Playwright QA Agent v1.0.0
========================================

Loading requirements from: requirements.md
Found 3 requirements

Testing against: https://your-app.com
Browser: chromium (headless)

Authenticating...
  Login successful

Running tests:
  ✓ REQ-001: passed (2.3s)
  ✓ REQ-002: passed (1.8s)
  ✓ REQ-003: passed (1.5s)

Summary:
========================================
Total:      3
Passed:     3 (100%)
Failed:     0
Clarify:    0
Errors:     0
Duration:   5.6s

Reports generated:
  json: test-results/2026-02-20_14-30-45/report.json
  junit_xml: test-results/2026-02-20_14-30-45/junit.xml
  html: test-results/2026-02-20_14-30-45/report.html

Exit code: 0
```

## Usage Patterns

### Basic Usage

```bash
# Minimum required arguments
playwright-qa-agent \
  --url https://app.example.com \
  --username user \
  --password pass \
  requirements.md
```

### Using Environment Variables

```bash
# Set credentials via environment
export QA_AGENT_URL=https://app.example.com
export QA_AGENT_USERNAME=testuser
export QA_AGENT_PASSWORD=secretpass

# Run without credentials in command
playwright-qa-agent requirements.md
```

### Headed Mode (See Browser)

```bash
# Watch the browser in action
playwright-qa-agent \
  --url https://app.example.com \
  --username user \
  --password pass \
  --headed \
  requirements.md
```

### Debug Mode

```bash
# Verbose logging for debugging
playwright-qa-agent \
  --url https://app.example.com \
  --username user \
  --password pass \
  --log-level debug \
  --headed \
  --screenshot-on always \
  requirements.md
```

### CI/CD Mode

```bash
# Optimized for continuous integration
playwright-qa-agent \
  --url https://staging.app.com \
  --username $CI_USERNAME \
  --password $CI_PASSWORD \
  --headless \
  --format junit,json \
  --output ./test-results \
  requirements.txt
```

### Reusing Authentication

```bash
# First run: save authentication state
playwright-qa-agent \
  --url https://app.com \
  --username user \
  --password pass \
  --auth-state ./auth.json \
  requirements.md

# Subsequent runs: reuse auth (faster, no password needed)
playwright-qa-agent \
  --url https://app.com \
  --auth-state ./auth.json \
  requirements.md
```

## Requirements Document Format

### Plain Text (.txt)

```
1. User can login with valid credentials
   Given: User is on login page
   When: User enters valid username and password
   Then: User is redirected to dashboard

2. Dashboard displays user statistics
   Given: User is logged in
   When: User navigates to dashboard
   Then: Statistics are visible
```

### Markdown (.md)

```markdown
## REQ-001: User Login

User can login with valid credentials.

**Given**: User is on login page
**When**: User enters valid username and password
**Then**: User is redirected to dashboard

## REQ-002: Dashboard Load

Dashboard displays user statistics.

**Given**: User is logged in
**When**: User navigates to dashboard
**Then**: Statistics widgets are visible
```

### Best Practices

1. **Numbering**: Use sequential numbers (1, 2, 3...)
2. **Titles**: Keep titles concise and descriptive
3. **Given/When/Then**: Include acceptance criteria for better verification
4. **Priority**: Optionally add priority tags (P1, P2, P3)
5. **Clarity**: Be specific about UI elements and actions

## Understanding Reports

### Directory Structure

```
test-results/
└── 2026-02-20_14-30-45/
    ├── junit.xml           # For CI/CD integration
    ├── report.json         # Detailed results (programmatic access)
    ├── report.html         # Human-readable report
    ├── screenshots/        # Test evidence
    │   ├── req_001_before_login.png
    │   ├── req_001_after_login.png
    │   └── req_002_dashboard.png
    └── logs/
        └── test_execution.log
```

### JUnit XML (CI/CD)

Used by continuous integration systems to display test results.

**Supported Platforms**:
- GitHub Actions
- GitLab CI
- Jenkins
- Azure DevOps
- CircleCI
- Travis CI

### JSON Report (Programmatic)

Detailed results in JSON format for custom processing.

**Example**:
```json
{
  "summary": {
    "total": 3,
    "passed": 3,
    "failed": 0,
    "pass_rate": 1.0
  },
  "results": [
    {
      "requirement_id": "REQ-001",
      "status": "passed",
      "duration": 2.3,
      "screenshots": ["screenshots/req_001.png"]
    }
  ]
}
```

### HTML Report (Human-Readable)

Visual report with:
- Test summary and statistics
- Pass/fail status for each requirement
- Embedded screenshots
- Detailed logs
- Execution timeline

## CI/CD Integration

For comprehensive CI/CD examples with complete configurations, see the [CI/CD Integration Guide](../../docs/ci-cd-integration.md).

### GitHub Actions

`.github/workflows/qa-tests.yml`:

```yaml
name: QA Tests

on:
  push:
    branches: [main, staging]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: |
          uv sync
          uv run playwright install --with-deps chromium

      - name: Run QA Agent
        env:
          QA_AGENT_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: |
          uv run playwright-qa-agent requirements.md \
            --url ${{ vars.APP_URL }} \
            --username ${{ vars.QA_USERNAME }} \
            --format all \
            --output test-results

      - name: Publish Test Results
        uses: mikepenz/action-junit-report@v4
        if: always()
        with:
          report_paths: test-results/**/junit.xml

      - name: Upload Test Artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results/
```

### GitLab CI

`.gitlab-ci.yml`:

```yaml
qa-tests:
  image: python:3.11
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.cargo/bin:$PATH"
    - uv add playwright-qa-agent
    - playwright install --with-deps
  script:
    - |
        uv run playwright-qa-agent requirements.md \
          --url "$QA_APP_URL" \
          --username "$QA_USERNAME" \
          --format all \
          --output test-results
  artifacts:
    when: always
    reports:
      junit: test-results/**/junit.xml
    paths:
      - test-results/
  only:
    - main
    - staging
```

### Jenkins

`Jenkinsfile`:

```groovy
pipeline {
    agent any

    environment {
        QA_AGENT_URL = 'https://staging.example.com'
        QA_USERNAME = credentials('qa-username')
        QA_PASSWORD = credentials('qa-password')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'curl -LsSf https://astral.sh/uv/install.sh | sh'
                sh 'uv add playwright-qa-agent'
                sh 'playwright install --with-deps'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    playwright-qa-agent \
                        --url $QA_AGENT_URL \
                        --username $QA_USERNAME \
                        --password $QA_PASSWORD \
                        --headless \
                        --output test-results \
                        requirements.md
                '''
            }
        }
    }

    post {
        always {
            junit 'test-results/**/junit.xml'
            archiveArtifacts artifacts: 'test-results/**/*', allowEmptyArchive: true
        }
    }
}
```

## Troubleshooting

### Common Issues

#### "Requirements file not found"

```bash
# Ensure file exists and has correct extension
ls requirements.md
# Use absolute path if needed
playwright-qa-agent --url ... /full/path/to/requirements.md
```

#### "Authentication failed"

```bash
# Verify credentials
playwright-qa-agent \
  --url https://app.com \
  --username testuser \
  --password testpass \
  --headed \
  --log-level debug \
  requirements.md
# Watch browser login attempt in headed mode
```

#### "Element not found"

The application might use dynamic selectors or slow loading:

```bash
# Increase timeout
playwright-qa-agent \
  --url https://app.com \
  --username user \
  --password pass \
  --timeout 60 \
  requirements.md
```

#### "Browser installation failed"

```bash
# On Linux, install system dependencies
playwright install --with-deps

# Or manually install dependencies
sudo apt-get install libnss3 libatk1.0-0 libx11-xcb1
```

#### "Permission denied"

```bash
# Ensure output directory is writable
chmod +w test-results/

# Or specify different output directory
playwright-qa-agent --output ~/my-reports requirements.md
```

### Debug Mode

When tests fail unexpectedly, use debug mode:

```bash
playwright-qa-agent \
  --url https://app.com \
  --username user \
  --password pass \
  --headed \
  --log-level debug \
  --screenshot-on always \
  --log-file debug.log \
  requirements.md
```

This will:
- Show the browser window (headed mode)
- Print detailed logs (debug level)
- Capture screenshots at every step
- Save all logs to `debug.log`

## Next Steps

### Advanced Features

- **Iterative Refinement**: Agent suggests improvements for ambiguous requirements (P2 feature)
- **CI/CD Integration**: Automate testing on every deployment (P3 feature)
- **Custom Selectors**: Configure custom selectors for login forms
- **Parallel Testing**: Run multiple requirements concurrently (future enhancement)

### Examples

See the `examples/` directory for:
- Sample requirements documents
- CI/CD configurations
- Custom selector configurations
- Report templates

### Support

- **Documentation**: https://docs.playwright-qa-agent.com
- **Issues**: https://github.com/yourorg/playwright-qa-agent/issues
- **Discussions**: https://github.com/yourorg/playwright-qa-agent/discussions

## Configuration File (Future)

For complex setups, create a `qa-agent.yaml`:

```yaml
app:
  url: https://app.example.com
  username: testuser
  password: ${QA_PASSWORD}  # From environment

browser:
  type: chromium
  headless: true
  timeout: 30

output:
  directory: ./test-results
  formats:
    - junit
    - json
    - html

logging:
  level: info
  file: qa-agent.log

screenshots:
  on: failure
  max_size: 1920
```

Then run:

```bash
playwright-qa-agent --config qa-agent.yaml requirements.md
```

*Note: Configuration file support is a future enhancement, not in v1.*

## Acceptance Criteria Verification

This quickstart guide enables users to:

✅ **SC-001**: Test 20+ requirements in a single run
✅ **SC-002**: Successfully login and navigate web applications
✅ **SC-004**: Generate reports within 5 minutes for 50 requirements
✅ **SC-005**: Integrate with CI/CD pipelines (GitHub Actions, GitLab, Jenkins)
✅ **SC-008**: Access detailed debugging information (screenshots, logs)

## Constitution Compliance

✅ **Simplicity**: Zero-config installation (`uv add playwright-qa-agent`)
✅ **Cross-Platform**: Works on Linux, macOS, Windows
✅ **UV + Python**: Uses UV package manager and Python 3.11+
✅ **Maintainability**: Clear documentation with examples
✅ **Usability**: Single command to run, sensible defaults
