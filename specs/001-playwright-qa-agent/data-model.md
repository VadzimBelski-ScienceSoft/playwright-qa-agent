# Data Model: Playwright QA Agent

**Phase**: 1 - Design
**Date**: 2026-02-20
**Status**: Complete

## Overview

This document defines the data models for the Playwright QA Agent. All models are designed for simplicity, cross-platform compatibility, and easy serialization to JSON/XML formats.

## Core Entities

### 1. Requirements Document

**Purpose**: Represents the input requirements document containing expected application behavior.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_path` | `pathlib.Path` | Yes | Path to requirements file (.txt or .md) |
| `format` | `str` | Yes | File format ("txt" or "md") |
| `raw_content` | `str` | Yes | Raw file content |
| `requirements` | `List[Requirement]` | Yes | Parsed list of requirements |
| `metadata` | `dict` | No | Optional metadata (author, version, etc.) |

**Example**:
```python
RequirementsDocument(
    file_path=Path("requirements.md"),
    format="md",
    raw_content="1. User can login...",
    requirements=[...],
    metadata={"version": "1.0"}
)
```

---

### 2. Requirement

**Purpose**: Individual requirement extracted from the requirements document.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier (e.g., "REQ-001") |
| `number` | `int` | Yes | Sequential number (1, 2, 3...) |
| `title` | `str` | Yes | Short requirement title |
| `description` | `str` | Yes | Full requirement description |
| `given` | `str` | No | Precondition (Given clause) |
| `when` | `str` | No | Action trigger (When clause) |
| `then` | `str` | No | Expected outcome (Then clause) |
| `priority` | `str` | No | Priority level (P1, P2, P3) |
| `category` | `str` | No | Category (authentication, dashboard, etc.) |

**Validation Rules**:
- `id` must match pattern: `REQ-\d{3}` (e.g., REQ-001)
- `number` must be positive integer
- `title` must be non-empty
- At least one of (`description`, `given`+`when`+`then`) must be present

**Example**:
```python
Requirement(
    id="REQ-001",
    number=1,
    title="User Login",
    description="User can login with valid credentials",
    given="User is on login page",
    when="User enters valid username and password",
    then="User is redirected to dashboard",
    priority="P1",
    category="authentication"
)
```

---

### 3. Test Session

**Purpose**: Represents a single execution of the QA agent against a web application.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | `str` | Yes | Unique session identifier (UUID) |
| `start_time` | `datetime` | Yes | Session start timestamp |
| `end_time` | `datetime` | No | Session end timestamp (None if running) |
| `duration` | `float` | No | Duration in seconds (calculated) |
| `requirements_doc` | `RequirementsDocument` | Yes | Input requirements |
| `app_url` | `str` | Yes | Target web application URL |
| `username` | `str` | Yes | Authentication username |
| `browser_type` | `str` | Yes | Browser used ("chromium", "firefox", "webkit") |
| `headless` | `bool` | Yes | Whether browser ran in headless mode |
| `results` | `List[VerificationResult]` | Yes | Results for each requirement |
| `status` | `str` | Yes | Overall status ("running", "completed", "failed") |
| `output_dir` | `pathlib.Path` | Yes | Directory for reports and artifacts |
| `environment` | `dict` | Yes | Environment info (Python version, OS, etc.) |

**State Transitions**:
- Initial: `status="running"`, `end_time=None`
- Complete: `status="completed"`, `end_time=<timestamp>`
- Error: `status="failed"`, `end_time=<timestamp>`

**Example**:
```python
TestSession(
    session_id="550e8400-e29b-41d4-a716-446655440000",
    start_time=datetime(2026, 2, 20, 14, 30, 45),
    end_time=datetime(2026, 2, 20, 14, 35, 12),
    duration=267.0,
    requirements_doc=req_doc,
    app_url="https://app.example.com",
    username="testuser",
    browser_type="chromium",
    headless=True,
    results=[...],
    status="completed",
    output_dir=Path("test-results/2026-02-20_14-30-45"),
    environment={
        "python_version": "3.11.0",
        "platform": "Linux",
        "playwright_version": "1.58.0"
    }
)
```

---

### 4. Verification Result

**Purpose**: Result of verifying a single requirement against the web application.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requirement_id` | `str` | Yes | Reference to tested requirement |
| `status` | `str` | Yes | Result status (see Status Values below) |
| `duration` | `float` | Yes | Time taken to test (seconds) |
| `steps` | `List[TestStep]` | Yes | Executed test steps |
| `screenshots` | `List[str]` | No | Screenshot file paths (relative) |
| `logs` | `List[str]` | No | Execution log messages |
| `error` | `dict` | No | Error details if failed |
| `clarification_reason` | `str` | No | Why clarification needed (if applicable) |
| `refinement_suggestion` | `str` | No | Suggested requirement refinement |
| `evidence` | `dict` | No | Additional evidence (DOM snapshots, network logs) |

**Status Values**:
- `"passed"`: Requirement verified successfully
- `"failed"`: Requirement could not be verified
- `"needs_clarification"`: Requirement is ambiguous or incomplete
- `"skipped"`: Requirement not testable (dependency failed)
- `"error"`: Test execution error (not requirement failure)

**Validation Rules**:
- If `status="failed"`, `error` must be present
- If `status="needs_clarification"`, `clarification_reason` must be present
- `screenshots` paths must be relative to session output directory
- `steps` must contain at least one step

**Example**:
```python
VerificationResult(
    requirement_id="REQ-001",
    status="passed",
    duration=2.34,
    steps=[
        TestStep(action="navigate", target="login page", success=True),
        TestStep(action="fill", target="username", success=True),
        TestStep(action="click", target="login button", success=True)
    ],
    screenshots=["screenshots/req_001_login_success.png"],
    logs=[
        "[14:30:46] Navigating to login page",
        "[14:30:47] Entering credentials",
        "[14:30:48] Login successful"
    ],
    error=None,
    clarification_reason=None,
    refinement_suggestion="Consider adding MFA requirement",
    evidence={"login_redirect_url": "https://app.example.com/dashboard"}
)
```

---

### 5. Test Step

**Purpose**: Individual action taken during requirement verification.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | `str` | Yes | Action type (navigate, fill, click, wait, verify) |
| `target` | `str` | Yes | Target element or page |
| `value` | `str` | No | Value for fill/input actions |
| `selector` | `str` | No | CSS/XPath selector used |
| `success` | `bool` | Yes | Whether step succeeded |
| `timestamp` | `datetime` | Yes | When step executed |
| `duration` | `float` | No | Step duration in seconds |
| `error_message` | `str` | No | Error if step failed |

**Action Types**:
- `"navigate"`: Go to URL
- `"fill"`: Enter text in input field
- `"click"`: Click element
- `"wait"`: Wait for element/condition
- `"verify"`: Assert element/condition
- `"screenshot"`: Capture screenshot

**Example**:
```python
TestStep(
    action="click",
    target="login button",
    selector="#login-btn",
    success=True,
    timestamp=datetime(2026, 2, 20, 14, 30, 48),
    duration=0.123
)
```

---

### 6. Test Report

**Purpose**: Consolidated output containing all verification results and metadata.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | `str` | Yes | Reference to test session |
| `created` | `datetime` | Yes | Report creation timestamp |
| `duration` | `float` | Yes | Total test duration |
| `summary` | `TestSummary` | Yes | Aggregated statistics |
| `requirements_tested` | `int` | Yes | Number of requirements tested |
| `results` | `List[VerificationResult]` | Yes | Individual results |
| `environment` | `dict` | Yes | Environment information |
| `files` | `dict` | Yes | Generated file paths (XML, JSON, HTML) |

**Example**:
```python
TestReport(
    session_id="550e8400-e29b-41d4-a716-446655440000",
    created=datetime(2026, 2, 20, 14, 35, 12),
    duration=267.0,
    summary=TestSummary(
        total=50,
        passed=45,
        failed=3,
        needs_clarification=2,
        skipped=0,
        errors=0,
        pass_rate=0.90
    ),
    requirements_tested=50,
    results=[...],
    environment={...},
    files={
        "junit_xml": "junit.xml",
        "json": "report.json",
        "html": "report.html"
    }
)
```

---

### 7. Test Summary

**Purpose**: Aggregated statistics for a test session.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total` | `int` | Yes | Total requirements tested |
| `passed` | `int` | Yes | Requirements verified successfully |
| `failed` | `int` | Yes | Requirements that failed verification |
| `needs_clarification` | `int` | Yes | Ambiguous requirements |
| `skipped` | `int` | Yes | Requirements skipped |
| `errors` | `int` | Yes | Test execution errors |
| `pass_rate` | `float` | Yes | Percentage passed (0.0-1.0) |

**Calculated Fields**:
- `pass_rate = passed / total` (if total > 0)
- `total = passed + failed + needs_clarification + skipped + errors`

**Validation**:
- All counts must be >= 0
- `pass_rate` must be between 0.0 and 1.0
- Sum of status counts must equal `total`

**Example**:
```python
TestSummary(
    total=50,
    passed=45,
    failed=3,
    needs_clarification=2,
    skipped=0,
    errors=0,
    pass_rate=0.90  # 45/50
)
```

---

### 8. Web Application (Configuration)

**Purpose**: Configuration for the web application under test.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | `str` | Yes | Base URL of application |
| `username` | `str` | Yes | Login username |
| `password` | `str` | Yes | Login password (stored securely) |
| `login_url` | `str` | No | Custom login page URL (defaults to /login) |
| `login_selectors` | `dict` | No | Custom selectors for login form |
| `session_storage` | `str` | No | Path to saved authentication state |

**Security Note**: Passwords should never be logged or included in reports.

**Example**:
```python
WebApplication(
    url="https://app.example.com",
    username="testuser",
    password="***",  # Never log actual password
    login_url="https://app.example.com/auth/login",
    login_selectors={
        "username": "#username",
        "password": "#password",
        "submit": "button[type='submit']"
    },
    session_storage="auth_state.json"
)
```

---

## Relationships

```
RequirementsDocument (1) ──has──> (N) Requirement
TestSession (1) ──references──> (1) RequirementsDocument
TestSession (1) ──contains──> (N) VerificationResult
VerificationResult (1) ──references──> (1) Requirement
VerificationResult (1) ──contains──> (N) TestStep
TestReport (1) ──summarizes──> (1) TestSession
TestReport (1) ──contains──> (N) VerificationResult
```

## Serialization

All models must support serialization to:
1. **JSON**: For programmatic access and report generation
2. **JUnit XML**: For CI/CD integration (subset of fields)

**JSON Serialization Pattern**:
```python
@dataclass
class Requirement:
    # ... fields ...

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "given": self.given,
            "when": self.when,
            "then": self.then,
            "priority": self.priority,
            "category": self.category
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Requirement":
        """Create from dictionary"""
        return cls(**data)
```

**Path Handling**:
- Use `pathlib.Path` for all file paths internally
- Convert to `str` for JSON serialization
- All paths in reports must be relative (for portability)

## Validation

Each model should implement a `validate()` method:

```python
def validate(self) -> List[str]:
    """
    Validate model constraints.

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    if not self.id.startswith("REQ-"):
        errors.append("ID must start with 'REQ-'")

    if self.number < 1:
        errors.append("Number must be positive")

    return errors
```

## File Storage Patterns

### Output Directory Structure

```
test-results/
└── YYYY-MM-DD_HH-MM-SS/          # TestSession.output_dir
    ├── junit.xml                  # JUnit XML report
    ├── report.json                # TestReport (JSON)
    ├── report.html                # TestReport (HTML)
    ├── session.json               # TestSession metadata
    ├── screenshots/               # VerificationResult.screenshots
    │   ├── req_001_step_1.png
    │   ├── req_001_step_2.png
    │   └── req_002_failure.png
    ├── logs/                      # VerificationResult.logs
    │   ├── test_execution.log
    │   └── req_001.log
    └── auth_state.json            # Playwright auth state
```

### File Naming Conventions

- **Screenshots**: `{requirement_id}_{description}.png`
- **Logs**: `{requirement_id}.log` or `test_execution.log` (global)
- **Reports**: Fixed names (`junit.xml`, `report.json`, `report.html`)
- **Session**: `session.json` (metadata)

## Success Criteria Mapping

These models support all success criteria from the specification:

- **SC-001** (20+ requirements): `RequirementsDocument.requirements` list
- **SC-002** (successful login): `TestSession.status`, `WebApplication` config
- **SC-003** (95% accuracy): `TestSummary.pass_rate`
- **SC-004** (5 min for 50 reqs): `TestSession.duration`
- **SC-005** (CI/CD output): `TestReport.files` (junit.xml)
- **SC-006** (refinement suggestions): `VerificationResult.refinement_suggestion`
- **SC-007** (zero false positives): `VerificationResult.status` classification
- **SC-008** (debugging detail): `VerificationResult.screenshots`, `logs`, `steps`

## Next Steps

Phase 1 will continue with:
- CLI interface contracts (command structure, arguments, options)
- Report format schemas (JSON schema, JUnit XML structure)
- Quick start guide with example usage
