# CI/CD Integration Guide

This guide shows how to integrate the Playwright QA Agent into popular CI/CD pipelines.

## Table of Contents

- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Jenkins](#jenkins)
- [Azure DevOps](#azure-devops)
- [Environment Variables Reference](#environment-variables-reference)
- [Exit Codes Reference](#exit-codes-reference)

---

## GitHub Actions

### Basic Workflow

Create `.github/workflows/qa.yml`:

```yaml
name: Requirements Verification

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  qa-verification:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: |
          uv sync
          uv run playwright install --with-deps chromium

      - name: Run QA verification
        env:
          QA_AGENT_PASSWORD: ${{ secrets.QA_PASSWORD }}
        run: |
          uv run playwright-qa-agent requirements.md \
            --url ${{ vars.APP_URL }} \
            --username ${{ vars.QA_USERNAME }} \
            --format all \
            --output test-results \
            --log-level info

      - name: Publish JUnit test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: qa-reports
          path: test-results/
          retention-days: 30

      - name: Upload test results to GitHub
        uses: mikepenz/action-junit-report@v4
        if: always()
        with:
          report_paths: "test-results/**/junit.xml"
```

### With Authentication State Caching

```yaml
      - name: Restore auth state cache
        uses: actions/cache@v4
        with:
          path: .auth_state.json
          key: auth-state-${{ hashFiles('requirements.md') }}

      - name: Run QA verification (with cached auth)
        env:
          QA_AGENT_PASSWORD: ${{ secrets.QA_PASSWORD }}
        run: |
          uv run playwright-qa-agent requirements.md \
            --url ${{ vars.APP_URL }} \
            --username ${{ vars.QA_USERNAME }} \
            --auth-state .auth_state.json \
            --format all
```

### Matrix Strategy (Multiple Browsers)

```yaml
jobs:
  qa-verification:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser: [chromium, firefox, webkit]
      fail-fast: false

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv sync
          uv run playwright install --with-deps ${{ matrix.browser }}

      - name: Run QA verification (${{ matrix.browser }})
        env:
          QA_AGENT_PASSWORD: ${{ secrets.QA_PASSWORD }}
        run: |
          uv run playwright-qa-agent requirements.md \
            --url ${{ vars.APP_URL }} \
            --username ${{ vars.QA_USERNAME }} \
            --browser ${{ matrix.browser }} \
            --output test-results/${{ matrix.browser }}

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: qa-reports-${{ matrix.browser }}
          path: test-results/${{ matrix.browser }}/
```

---

## GitLab CI

Create `.gitlab-ci.yml`:

```yaml
image: mcr.microsoft.com/playwright/python:v1.50.0-noble

stages:
  - qa-verification

variables:
  QA_AGENT_BROWSER: chromium
  QA_AGENT_LOG_LEVEL: info

qa-verify:
  stage: qa-verification
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.local/bin:$PATH"
    - uv sync
    - playwright install --with-deps chromium
  script:
    - |
      uv run playwright-qa-agent requirements.md \
        --url "$APP_URL" \
        --username "$QA_USERNAME" \
        --format all \
        --output test-results
  after_script:
    - echo "QA verification complete. Exit code: $CI_JOB_STATUS"
  artifacts:
    when: always
    paths:
      - test-results/
    reports:
      junit: test-results/junit.xml
    expire_in: 7 days
  only:
    - main
    - merge_requests
```

### GitLab with Secrets

Store `QA_AGENT_PASSWORD` in **Settings → CI/CD → Variables** as a masked variable.

```yaml
qa-verify:
  script:
    - |
      QA_AGENT_PASSWORD="$QA_AGENT_PASSWORD" \
      uv run playwright-qa-agent requirements.md \
        --url "$APP_URL" \
        --username "$QA_USERNAME"
```

---

## Jenkins

### Declarative Pipeline (`Jenkinsfile`)

```groovy
pipeline {
    agent {
        docker {
            image 'mcr.microsoft.com/playwright/python:v1.50.0-noble'
        }
    }

    environment {
        QA_AGENT_URL        = "${env.APP_URL}"
        QA_AGENT_USERNAME   = "${env.QA_USERNAME}"
        QA_AGENT_PASSWORD   = credentials('qa-password')
        QA_AGENT_LOG_LEVEL  = 'info'
    }

    stages {
        stage('Install Dependencies') {
            steps {
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    export PATH="$HOME/.local/bin:$PATH"
                    uv sync
                    playwright install --with-deps chromium
                '''
            }
        }

        stage('Run QA Verification') {
            steps {
                sh '''
                    export PATH="$HOME/.local/bin:$PATH"
                    uv run playwright-qa-agent requirements.md \
                        --format all \
                        --output test-results
                '''
            }
        }
    }

    post {
        always {
            junit 'test-results/junit.xml'
            archiveArtifacts artifacts: 'test-results/**', fingerprint: true
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'test-results',
                reportFiles: 'report.html',
                reportName: 'QA Agent Report'
            ])
        }
    }
}
```

---

## Azure DevOps

Create `azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: ubuntu-latest

variables:
  APP_URL: $(appUrl)
  QA_USERNAME: $(qaUsername)

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: "3.11"
    displayName: "Use Python 3.11"

  - script: |
      curl -LsSf https://astral.sh/uv/install.sh | sh
      echo "##vso[task.prependpath]$HOME/.local/bin"
    displayName: "Install UV"

  - script: |
      uv sync
      uv run playwright install --with-deps chromium
    displayName: "Install dependencies"

  - script: |
      uv run playwright-qa-agent requirements.md \
        --url "$(APP_URL)" \
        --username "$(QA_USERNAME)" \
        --format all \
        --output $(Build.ArtifactStagingDirectory)/test-results
    env:
      QA_AGENT_PASSWORD: $(qaPassword)
    displayName: "Run QA verification"

  - task: PublishTestResults@2
    condition: always()
    inputs:
      testResultsFormat: JUnit
      testResultsFiles: "$(Build.ArtifactStagingDirectory)/test-results/junit.xml"
      testRunTitle: "Playwright QA Agent"

  - task: PublishPipelineArtifact@1
    condition: always()
    inputs:
      targetPath: "$(Build.ArtifactStagingDirectory)/test-results"
      artifact: "qa-reports"
      publishLocation: pipeline

  - task: PublishHtmlReport@1
    condition: always()
    inputs:
      reportDir: "$(Build.ArtifactStagingDirectory)/test-results"
      tabName: "QA Report"
```

### Azure DevOps Variable Groups

Store secrets in a Variable Group (`Library → Variable Groups`):

```yaml
variables:
  - group: qa-agent-secrets  # Contains: qaPassword, appUrl, qaUsername
```

---

## Environment Variables Reference

| Variable | CLI Option | Description |
|----------|------------|-------------|
| `QA_AGENT_URL` | `--url` | Target web application URL |
| `QA_AGENT_USERNAME` | `--username` | Login username |
| `QA_AGENT_PASSWORD` | `--password` | Login password (always use env var) |
| `QA_AGENT_BROWSER` | `--browser` | Browser: chromium, firefox, webkit |
| `QA_AGENT_HEADLESS` | `--headless` | Run headless (true/false) |
| `QA_AGENT_OUTPUT` | `--output` | Output directory path |
| `QA_AGENT_FORMAT` | `--format` | Report formats: json, junit, html, all |
| `QA_AGENT_LOG_LEVEL` | `--log-level` | Log verbosity: debug, info, warning, error |
| `QA_AGENT_TIMEOUT` | `--timeout` | Per-requirement timeout in seconds |

---

## Exit Codes Reference

| Code | Meaning | CI Action |
|------|---------|-----------|
| 0 | All requirements passed | Pipeline succeeds |
| 1 | One or more requirements failed | Pipeline fails |
| 2 | Execution error | Pipeline fails |
| 3 | Authentication failed | Pipeline fails (check credentials) |
| 4 | Invalid requirements file | Pipeline fails (check file format) |

### Handling Exit Codes in Scripts

```bash
uv run playwright-qa-agent requirements.md --url "$URL" --username "$USER"
EXIT_CODE=$?

case $EXIT_CODE in
  0) echo "All requirements verified successfully" ;;
  1) echo "Some requirements failed - check report" ;;
  2) echo "Execution error - check logs" ;;
  3) echo "Authentication failed - check credentials" ;;
  4) echo "Invalid requirements file - check format" ;;
esac

exit $EXIT_CODE
```

---

## Tips

### Security Best Practices

- **Never put passwords in pipeline YAML files** - use secret variables/credentials
- Use `QA_AGENT_PASSWORD` environment variable instead of `--password` flag
- Consider using `--auth-state` to cache login tokens and reduce credential exposure

### Performance Optimization

- Use `--browser chromium` (fastest) for CI pipelines
- Use `--headless` (default) in CI - headed mode requires display server
- Use `--screenshot-on failure` to reduce artifact size in CI

### Debugging Failed Pipelines

```bash
# Run with debug logging for detailed output
uv run playwright-qa-agent requirements.md \
  --url "$APP_URL" --username "$USER" \
  --log-level debug \
  --log-file debug.log
```
