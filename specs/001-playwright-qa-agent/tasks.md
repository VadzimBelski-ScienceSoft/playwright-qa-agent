---

description: "Task list for Playwright QA Agent implementation"
---

# Tasks: Playwright QA Agent

**Input**: Design documents from `/specs/001-playwright-qa-agent/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure (src/models, src/services, src/cli, src/lib, tests/)

**Acceptance Criteria**:
- All directories exist: `src/models/`, `src/services/`, `src/cli/`, `src/lib/`, `tests/contract/`, `tests/integration/`, `tests/unit/`
- Each directory has `__init__.py` file for Python package structure
- Directory structure matches plan.md specification

**Verification**:
- Run `ls -la src/` and verify all subdirectories present
- Import test: `python -c "import src.models; import src.services; import src.cli; import src.lib"`

---

- [ ] T002 Initialize pyproject.toml with UV dependencies

**Acceptance Criteria**:
- `pyproject.toml` file created at repository root
- Contains project metadata (name: "playwright-qa-agent", version, Python requirement: ">=3.11")
- Dependencies declared: `claude-agent-sdk >=0.1.39`, `playwright >=1.58.0`, `mistune >=3.0`, `junit-xml >=1.9`
- Dev dependencies: `pytest`, `ruff` (for linting)
- Entry point configured for CLI: `playwright-qa-agent = "src.cli.main:main"`

**Verification**:
- Run `uv sync` successfully installs all dependencies
- Run `uv pip list` shows all 4 core dependencies
- File validates: `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"`

---

- [ ] T003 [P] Configure linting with ruff

**Acceptance Criteria**:
- `ruff.toml` or `pyproject.toml` section for ruff configuration
- Line length set to 100 characters (matches Python standards)
- Target Python version 3.11+
- Basic rules enabled (unused imports, undefined names, etc.)

**Verification**:
- Run `ruff check .` executes without configuration errors
- Run `ruff format .` executes without configuration errors

---

- [ ] T004 [P] Install Playwright browser binaries

**Acceptance Criteria**:
- Playwright browsers installed (Chromium, Firefox, WebKit)
- System dependencies installed if on Linux
- Installation completes without errors

**Verification**:
- Run `playwright install` completes successfully
- Run `playwright --version` shows installed version
- Browsers located in expected cache directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create Requirement model in src/models/requirement.py

**Acceptance Criteria**:
- Python dataclass with all fields from data-model.md section 2
- Fields: `id` (str), `number` (int), `title` (str), `description` (str), `given` (str), `when` (str), `then` (str), `priority` (str), `category` (str)
- Type hints on all fields
- `to_dict()` method for JSON serialization
- `from_dict()` classmethod for deserialization
- `validate()` method checking: id pattern (REQ-\d{3}), number > 0, title non-empty

**Verification**:
- Import: `from src.models.requirement import Requirement`
- Instantiate: `req = Requirement(id="REQ-001", number=1, title="Test", description="Test desc")`
- Serialize: `req.to_dict()` returns dict
- Validate: `req.validate()` returns empty list for valid data, list of errors for invalid

---

- [ ] T006 [P] Create RequirementsDocument model in src/models/requirements_document.py

**Acceptance Criteria**:
- Python dataclass with fields from data-model.md section 1
- Fields: `file_path` (pathlib.Path), `format` (str), `raw_content` (str), `requirements` (List[Requirement]), `metadata` (dict)
- Type hints including `from pathlib import Path`
- `to_dict()` and `from_dict()` methods
- `validate()` method checking: file_path exists, format in ["txt", "md"], raw_content non-empty

**Verification**:
- Import: `from src.models.requirements_document import RequirementsDocument`
- Uses Requirement model: `from src.models.requirement import Requirement`
- Path handling: `doc.file_path` is `pathlib.Path` instance

---

- [ ] T007 [P] Create TestStep model in src/models/test_step.py

**Acceptance Criteria**:
- Dataclass with fields from data-model.md section 5
- Fields: `action` (str), `target` (str), `value` (str), `selector` (str), `success` (bool), `timestamp` (datetime), `duration` (float), `error_message` (str)
- Action types validated: navigate, fill, click, wait, verify, screenshot
- `to_dict()` method with datetime serialization

**Verification**:
- Import and instantiate with various action types
- Validate action enum: only accepts valid action types

---

- [ ] T008 [P] Create VerificationResult model in src/models/verification_result.py

**Acceptance Criteria**:
- Dataclass with fields from data-model.md section 4
- Fields: `requirement_id` (str), `status` (str), `duration` (float), `steps` (List[TestStep]), `screenshots` (List[str]), `logs` (List[str]), `error` (dict), `clarification_reason` (str), `refinement_suggestion` (str), `evidence` (dict)
- Status types: passed, failed, needs_clarification, skipped, error
- `validate()` enforces: if status=failed then error must be present, if status=needs_clarification then clarification_reason must be present

**Verification**:
- Import and create with TestStep list
- Status validation works correctly

---

- [ ] T009 [P] Create TestSummary model in src/models/test_summary.py

**Acceptance Criteria**:
- Dataclass with fields from data-model.md section 7
- Fields: `total` (int), `passed` (int), `failed` (int), `needs_clarification` (int), `skipped` (int), `errors` (int), `pass_rate` (float)
- `calculate_pass_rate()` method: returns passed / total if total > 0, else 0.0
- `validate()` checks: all counts >= 0, pass_rate between 0.0 and 1.0, sum of counts equals total

**Verification**:
- Create summary and verify pass_rate calculation
- Validate constraints work

---

- [ ] T010 [P] Create TestSession model in src/models/test_session.py

**Acceptance Criteria**:
- Dataclass with fields from data-model.md section 3
- Fields: `session_id` (str UUID), `start_time` (datetime), `end_time` (datetime), `duration` (float), `requirements_doc` (RequirementsDocument), `app_url` (str), `username` (str), `browser_type` (str), `headless` (bool), `results` (List[VerificationResult]), `status` (str), `output_dir` (Path), `environment` (dict)
- Status values: running, completed, failed
- State transition methods: `start()`, `complete()`, `fail()`
- UUID generation for session_id

**Verification**:
- Import and create session
- State transitions work correctly
- Duration calculated from start_time and end_time

---

- [ ] T011 [P] Create TestReport model in src/models/test_report.py

**Acceptance Criteria**:
- Dataclass with fields from data-model.md section 6
- Fields: `session_id` (str), `created` (datetime), `duration` (float), `summary` (TestSummary), `requirements_tested` (int), `results` (List[VerificationResult]), `environment` (dict), `files` (dict)
- `to_dict()` method for JSON export
- `generate_summary()` method to create TestSummary from results list

**Verification**:
- Create report from session data
- Summary generation works correctly
- JSON serialization includes all nested models

---

- [ ] T012 [P] Create WebApplication model in src/models/web_application.py

**Acceptance Criteria**:
- Dataclass with fields from data-model.md section 8
- Fields: `url` (str), `username` (str), `password` (str), `login_url` (str), `login_selectors` (dict), `session_storage` (str)
- `validate()` checks: url is valid HTTP/HTTPS, username and password non-empty
- Password NEVER included in `to_dict()` output (security requirement)

**Verification**:
- Create with credentials
- Verify password not in serialized output: `assert "password" not in app.to_dict()`
- URL validation works

---

- [ ] T013 [P] Create file utilities in src/lib/file_utils.py

**Acceptance Criteria**:
- Function `create_timestamped_dir(base_dir: Path) -> Path`: creates YYYY-MM-DD_HH-MM-SS directory
- Function `create_latest_symlink(target_dir: Path, link_name: str = "latest")`: creates/updates symlink
- Function `ensure_dir_exists(path: Path)`: creates directory if not exists
- Function `get_relative_path(path: Path, base: Path) -> str`: returns relative path as string
- All functions use pathlib.Path
- Cross-platform compatible (works on Windows, Linux, macOS)

**Verification**:
- Import: `from src.lib.file_utils import *`
- Create test directory and verify timestamp format
- Symlink creation works on current OS

---

- [ ] T014 [P] Create logger utility in src/lib/logger.py

**Acceptance Criteria**:
- Function `setup_logger(name: str, log_file: Path = None, level: str = "INFO") -> logging.Logger`
- Returns configured Python logger with console and file handlers
- Log format includes timestamp: `[HH:MM:SS] MESSAGE`
- Supports levels: DEBUG, INFO, WARNING, ERROR
- File handler optional (for test execution logs)

**Verification**:
- Import: `from src.lib.logger import setup_logger`
- Create logger: `logger = setup_logger("test")`
- Log messages appear with correct timestamp format

---

- [ ] T015 Create CLI argument parser in src/cli/main.py (basic structure)

**Acceptance Criteria**:
- Python file with `main()` entry point function
- Uses `argparse` for CLI argument parsing
- Defines all arguments from contracts/cli-interface.md:
  - Positional: requirements_file
  - Required: --url, --username, --password
  - Optional: --browser, --headless/--headed, --output, --format, --log-level, --timeout
- Environment variable support using `os.getenv` with `QA_AGENT_` prefix
- Returns parsed arguments namespace
- No implementation yet, just structure and parsing

**Acceptance Criteria (Structure Only)**:
- Argument parser configured with all CLI options
- Help text for each argument
- Default values set per contracts
- Environment variable fallback logic

**Verification**:
- Run `python src/cli/main.py --help` shows all options
- Parse test args: arguments correctly extracted

---

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Requirements Verification (Priority: P1) 🎯 MVP

**Goal**: Enable QA engineers to verify documented requirements against actual web applications

**Independent Test**: Provide a requirements document and test web app, verify agent logs in, navigates, and produces verification report

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement plain text parser in src/services/parser_service.py (parse_plain_text function)

**Acceptance Criteria**:
- Function `parse_plain_text(content: str) -> List[Requirement]`
- Parses numbered list format: "1. Title: Description" or "1. Description"
- Extracts Given/When/Then using regex patterns from research.md
- Pattern: `^(\d+)\.\s+(?:\*\*([^*]+)\*\*:\s+)?(.+)$` for main requirement
- Patterns for GWT: `[-*]\s*Given:\s*(.+)`, `[-*]\s*When:\s*(.+)`, `[-*]\s*Then:\s*(.+)`
- Generates requirement IDs: REQ-001, REQ-002, etc.
- Returns List[Requirement] with all fields populated

**Verification**:
- Parse sample plain text requirements file
- Verify all requirements extracted with correct IDs
- Given/When/Then correctly captured when present

---

- [ ] T017 [P] [US1] Implement Markdown parser in src/services/parser_service.py (parse_markdown function)

**Acceptance Criteria**:
- Function `parse_markdown(content: str) -> List[Requirement]`
- Uses mistune library to parse markdown
- Supports section headers: `## REQ-001: Title` or `## Title`
- Extracts description from first paragraph after header
- Extracts Given/When/Then from bold markers: `**Given**:`, `**When**:`, `**Then**:`
- Handles numbered lists in markdown
- Returns List[Requirement]

**Verification**:
- Parse sample markdown requirements file
- Verify structured markdown correctly parsed
- Both numbered and section-based formats work

---

- [ ] T018 [US1] Implement ParserService in src/services/parser_service.py (main class)

**Acceptance Criteria**:
- Class `ParserService` with method `parse_requirements(file_path: Path) -> RequirementsDocument`
- Auto-detects format from file extension (.txt or .md)
- Calls appropriate parser (parse_plain_text or parse_markdown)
- Reads file content using pathlib
- Returns RequirementsDocument with parsed requirements
- Raises clear error if format unsupported or file not found

**Verification**:
- Parse .txt file: `parser.parse_requirements(Path("test.txt"))`
- Parse .md file: `parser.parse_requirements(Path("test.md"))`
- Error handling: invalid file raises appropriate exception

---

- [ ] T019 [P] [US1] Implement browser initialization in src/services/browser_service.py (BrowserService.__init__ and launch)

**Acceptance Criteria**:
- Class `BrowserService` with `__init__(browser_type: str = "chromium", headless: bool = True)`
- Method `launch() -> Browser`: launches Playwright browser
- Supports browser types: chromium, firefox, webkit
- Launches in headless or headed mode per parameter
- Stores browser instance as class attribute
- Method `close()`: closes browser

**Verification**:
- Import playwright: `from playwright.sync_api import sync_playwright`
- Launch browser: `service = BrowserService(); service.launch()`
- Browser instance created
- Close works without errors

---

- [ ] T020 [P] [US1] Implement authentication in src/services/browser_service.py (authenticate method)

**Acceptance Criteria**:
- Method `authenticate(page: Page, app_config: WebApplication) -> bool`
- Navigates to login URL (app_config.login_url or app_config.url + "/login")
- Fills username field using selector from app_config.login_selectors or default "#username"
- Fills password field using selector or default "#password"
- Clicks submit button using selector or default "button[type='submit']"
- Waits for navigation after login
- Returns True if successful, False if failed
- Never logs password (security requirement)

**Verification**:
- Mock Playwright page and test authentication flow
- Verify selectors used correctly
- Password not in any logs

---

- [ ] T021 [US1] Implement authentication state management in src/services/browser_service.py (save_auth_state, load_auth_state methods)

**Acceptance Criteria**:
- Method `save_auth_state(context: BrowserContext, file_path: Path)`
- Uses Playwright's `context.storage_state(path=str(file_path))`
- Saves cookies and localStorage to JSON file
- Method `load_auth_state(file_path: Path) -> dict`
- Loads and returns storage state from JSON file
- Returns None if file doesn't exist

**Verification**:
- Save state after authentication
- Load state and verify JSON structure
- Reuse state in new context

---

- [ ] T022 [P] [US1] Implement navigation in src/services/browser_service.py (navigate_to method)

**Acceptance Criteria**:
- Method `navigate_to(page: Page, url: str, wait_for: str = "load") -> bool`
- Navigates to URL using `page.goto(url)`
- Supports wait_for options: "load", "networkidle", "domcontentloaded"
- Returns True if navigation successful
- Handles navigation errors gracefully
- Logs navigation action with timestamp

**Verification**:
- Navigate to test URL
- Test all wait_for options
- Error handling for invalid URL

---

- [ ] T023 [P] [US1] Implement element verification in src/services/browser_service.py (verify_element method)

**Acceptance Criteria**:
- Method `verify_element(page: Page, selector: str, timeout: int = 30000) -> dict`
- Waits for element using `page.wait_for_selector(selector, timeout=timeout)`
- Returns dict with: `{"success": bool, "element": Element or None, "error": str or None}`
- Captures screenshot on failure
- Uses semantic locators when possible (getByRole, getByLabel)

**Verification**:
- Verify existing element returns success
- Verify non-existent element returns failure with error
- Screenshot captured on failure

---

- [ ] T024 [US1] Implement screenshot capture in src/services/browser_service.py (capture_screenshot method)

**Acceptance Criteria**:
- Method `capture_screenshot(page: Page, filepath: Path, full_page: bool = True) -> Path`
- Uses `page.screenshot(path=str(filepath), full_page=full_page)`
- Creates screenshot directory if not exists
- Returns Path to saved screenshot
- Supports both full page and viewport screenshots

**Verification**:
- Capture screenshot of test page
- Verify file created at specified path
- File is valid PNG image

---

- [ ] T025 [US1] Implement AgentService orchestration in src/services/agent_service.py

**Acceptance Criteria**:
- Class `AgentService` with Claude SDK integration
- `__init__(requirements_doc: RequirementsDocument, app_config: WebApplication)`
- Method `verify_requirements(browser_service: BrowserService) -> List[VerificationResult]`
- For each requirement:
  - Uses Claude SDK to interpret requirement natural language
  - Plans verification steps (navigate, fill, click, verify)
  - Executes steps via browser_service
  - Creates TestStep objects for each action
  - Captures screenshots at key points
  - Returns VerificationResult with status (passed/failed)
- Handles errors gracefully, marks as failed with error details

**Verification**:
- Create agent with sample requirements
- Verify requirements against test app
- All results have proper status and steps

---

- [ ] T026 [US1] Implement JSON report generation in src/services/report_service.py (generate_json_report method)

**Acceptance Criteria**:
- Class `ReportService` with method `generate_json_report(test_report: TestReport, output_path: Path)`
- Serializes TestReport to JSON using `to_dict()` methods
- Follows JSON schema from contracts/json-report-schema.json
- Includes all fields: session_id, created, duration, summary, results, environment, files
- Writes to output_path with proper formatting (indent=2)
- All paths in report are relative (not absolute)

**Verification**:
- Generate report from test session
- Validate against JSON schema
- All nested models serialized correctly

---

- [ ] T027 [US1] Implement test session management in src/services/agent_service.py (create_session, complete_session methods)

**Acceptance Criteria**:
- Method `create_session(requirements_doc: RequirementsDocument, app_config: WebApplication, output_dir: Path) -> TestSession`
- Generates UUID for session_id
- Sets start_time to current datetime
- Creates output directory structure (screenshots/, logs/)
- Creates symlink to "latest"
- Method `complete_session(session: TestSession, results: List[VerificationResult])`
- Sets end_time, calculates duration
- Sets status to "completed" or "failed"
- Populates environment dict (Python version, platform, etc.)

**Verification**:
- Create session and verify UUID generated
- Directory structure created correctly
- Complete session and verify timestamps

---

- [ ] T028 [US1] Integrate all components in src/cli/main.py (User Story 1 flow)

**Acceptance Criteria**:
- Complete `main()` function implementation for US1 flow:
  1. Parse CLI arguments
  2. Load requirements using ParserService
  3. Create WebApplication config from args
  4. Create AgentService
  5. Launch BrowserService
  6. Authenticate to web app
  7. Verify requirements
  8. Generate reports (JSON)
  9. Print summary to stdout
  10. Return exit code (0 = success, 1 = failures, 2 = errors)
- Error handling for each step with clear messages
- Progress output during execution
- Logger integration for debugging

**Verification**:
- Run full CLI command with test requirements and app
- Verify report generated
- Exit code correct based on results

---

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The MVP can verify requirements and generate JSON reports.

---

## Phase 4: User Story 2 - Iterative Requirements Refinement (Priority: P2)

**Goal**: Identify ambiguous or incomplete requirements and suggest refinements based on actual application behavior

**Independent Test**: Provide vague requirements, verify agent produces specific clarification suggestions

### Implementation for User Story 2

- [ ] T029 [P] [US2] Implement ambiguity detection in src/services/agent_service.py (detect_ambiguity method)

**Acceptance Criteria**:
- Method `detect_ambiguity(requirement: Requirement, page: Page) -> dict`
- Uses Claude SDK to analyze requirement text for vague language
- Patterns detected: "manage", "handle", "process", "update" without specifics
- Missing details: unclear subjects, no acceptance criteria
- Returns dict: `{"is_ambiguous": bool, "reasons": List[str], "discovered_elements": List[str]}`
- Inspects page to find actual elements related to requirement
- Example: "manage settings" → finds multiple settings options

**Verification**:
- Test with vague requirement: "User can manage settings"
- Verify ambiguity detected
- Discovered elements listed (e.g., "user settings", "admin settings")

---

- [ ] T030 [US2] Implement refinement suggestions in src/services/agent_service.py (suggest_refinement method)

**Acceptance Criteria**:
- Method `suggest_refinement(requirement: Requirement, ambiguity_info: dict) -> str`
- Uses Claude SDK to generate specific refinement suggestion
- Suggests precise language based on discovered elements
- Format: "Consider specifying which settings: found 'User Settings' and 'Admin Settings' links"
- Includes examples from actual application
- Returns clear, actionable suggestion text

**Verification**:
- Input ambiguous requirement and ambiguity info
- Verify suggestion is specific and actionable
- Includes discovered element names

---

- [ ] T031 [US2] Add clarification status to verification flow in src/services/agent_service.py

**Acceptance Criteria**:
- Update `verify_requirements()` to detect ambiguity before/during verification
- If ambiguity detected, set VerificationResult.status = "needs_clarification"
- Populate `clarification_reason` with detected ambiguity reasons
- Populate `refinement_suggestion` with suggested refinement
- Still attempt verification but mark result for clarification
- Agent can verify multiple interpretations and note discrepancies

**Verification**:
- Run with ambiguous requirement
- Verify result has status "needs_clarification"
- Clarification reason and suggestion populated

---

- [ ] T032 [P] [US2] Add refinement suggestions to JSON report in src/services/report_service.py

**Acceptance Criteria**:
- Update `generate_json_report()` to include refinement suggestions
- Each result with `status="needs_clarification"` includes:
  - `clarification_reason` field
  - `refinement_suggestion` field
  - `discovered_elements` from ambiguity detection
- Summary includes count of requirements needing clarification

**Verification**:
- Generate report with clarification results
- Verify refinement suggestions in JSON
- Summary count correct

---

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. The agent can verify requirements and suggest refinements.

---

## Phase 5: User Story 3 - CI/CD Integration (Priority: P3)

**Goal**: Enable automatic requirement verification in CI/CD pipelines with machine-readable output

**Independent Test**: Trigger agent from CI/CD script, verify JUnit XML output and exit codes work correctly

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement JUnit XML generation in src/services/report_service.py (generate_junit_xml method)

**Acceptance Criteria**:
- Method `generate_junit_xml(test_report: TestReport, output_path: Path)`
- Uses `junit-xml` library to create XML structure
- Follows format from contracts/junit-xml-structure.md
- Creates `<testsuites>` with single `<testsuite>`
- Each requirement → `<testcase>` element
- Pass → testcase with no child elements
- Fail → testcase with `<failure>` element
- Needs clarification → testcase with `<skipped>` element
- Properties include: requirement_id, priority, screenshot paths
- System-out includes: attachment markers `[[ATTACHMENT|path]]`, timestamped logs

**Verification**:
- Generate JUnit XML from test report
- Validate XML structure with xmllint or similar
- Parse with CI/CD tools (verify format compatibility)

---

- [ ] T034 [P] [US3] Implement HTML report generation in src/services/report_service.py (generate_html_report method)

**Acceptance Criteria**:
- Method `generate_html_report(test_report: TestReport, output_path: Path)`
- Generates self-contained HTML file with embedded CSS
- Includes:
  - Summary section with pass/fail statistics
  - Table of requirements with status badges
  - Expandable details for each requirement (steps, logs, screenshots)
  - Embedded screenshots as base64 data URLs
- Responsive design (works on mobile)
- No external dependencies (CSS/JS inline)

**Verification**:
- Generate HTML report
- Open in browser and verify rendering
- All screenshots display correctly
- Expandable sections work

---

- [ ] T035 [US3] Implement exit code logic in src/cli/main.py

**Acceptance Criteria**:
- Update `main()` to return proper exit codes per contracts/cli-interface.md
- Exit code 0: All requirements passed
- Exit code 1: One or more requirements failed
- Exit code 2: Execution error (invalid config, network failure, auth failure)
- Exit code 3: Authentication failed specifically
- Exit code 4: Invalid requirements file format
- Based on TestSummary counts and exception types

**Verification**:
- Run with all passing requirements: `echo $?` returns 0
- Run with failures: exit code 1
- Run with invalid file: exit code 4
- Run with auth failure: exit code 3

---

- [ ] T036 [P] [US3] Add multi-format report generation to CLI in src/cli/main.py

**Acceptance Criteria**:
- Support `--format` argument: junit, json, html, all
- Generate only requested formats
- Default to "all" (generate all three)
- Report file paths to stdout after generation
- Create all reports in same output directory

**Verification**:
- Run with `--format junit`: only junit.xml created
- Run with `--format json,html`: both created
- Run with `--format all`: all three created
- Paths printed to stdout correctly

---

- [ ] T037 [P] [US3] Create CI/CD integration documentation in docs/ci-cd-integration.md

**Acceptance Criteria**:
- Document includes working examples for:
  - GitHub Actions (with YAML config)
  - GitLab CI (with .gitlab-ci.yml)
  - Jenkins (with Jenkinsfile)
  - Azure DevOps (with pipeline YAML)
- Each example shows:
  - How to install UV and dependencies
  - How to run the agent with credentials from secrets
  - How to publish test results
  - How to upload artifacts
- Examples are copy-paste ready (minimal modification needed)

**Verification**:
- Documentation file exists and renders correctly in markdown
- Examples include all necessary steps
- Secrets/environment variables properly used

---

**Checkpoint**: All user stories should now be independently functional. CI/CD integration works with machine-readable output.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final release preparation

- [ ] T038 [P] Create README.md at repository root

**Acceptance Criteria**:
- Sections include:
  - Project description and features
  - Installation instructions (UV + Playwright setup)
  - Quick start example
  - CLI usage with all options
  - Exit codes explanation
  - Link to full documentation
- Badges for: Python version, license, build status (placeholders OK)
- Examples use actual command syntax
- Links to quickstart.md and other docs

**Verification**:
- README renders correctly on GitHub
- Installation steps work when followed
- Quick start example runs successfully

---

- [ ] T039 [P] Add comprehensive logging throughout codebase

**Acceptance Criteria**:
- All services use logger from src/lib/logger.py
- Log levels used appropriately:
  - DEBUG: Detailed step information
  - INFO: Progress updates (requirement X of Y)
  - WARNING: Non-fatal issues (element not found, retrying)
  - ERROR: Fatal errors before exceptions
- Logs include timestamps (handled by logger utility)
- Passwords NEVER logged (security requirement)
- Log file created in output directory when --log-file specified

**Verification**:
- Run with `--log-level debug`: see detailed logs
- Run with `--log-level error`: only errors shown
- No passwords appear in log files

---

- [ ] T040 [P] Add error handling and user-friendly error messages

**Acceptance Criteria**:
- All exceptions caught and converted to clear error messages
- Error messages follow pattern from contracts/cli-interface.md:
  - Bad: "Invalid input" → Good: "Requirements file 'reqs.md' not found. Please provide a valid .txt or .md file."
  - Bad: "Auth failed" → Good: "Authentication failed: Invalid credentials for user 'testuser'. Please check --username and --password."
- Network errors include retry suggestions
- File errors include path and permission hints
- All errors printed to stderr, not stdout

**Verification**:
- Test various error conditions
- Verify messages are actionable
- stderr vs stdout correct

---

- [ ] T041 Add type hints and docstrings to all modules

**Acceptance Criteria**:
- Every function has type hints for parameters and return value
- Every class and method has docstring (Google style or NumPy style)
- Docstrings include:
  - Brief description
  - Args: parameter descriptions
  - Returns: return value description
  - Raises: exceptions that may be raised (for public methods)
- Complex logic has inline comments

**Verification**:
- Run `ruff check .` with docstring rules enabled
- No missing type hints warnings
- Documentation can be generated with Sphinx (future)

---

- [ ] T042 [P] Add unit tests for utility functions in tests/unit/

**Acceptance Criteria**:
- Test file_utils.py: create_timestamped_dir, create_latest_symlink, relative paths
- Test logger.py: logger creation, log levels, file output
- Test model validation: Requirement.validate(), TestSummary.validate(), etc.
- Use pytest framework
- All tests pass
- Coverage for critical utility functions >80%

**Verification**:
- Run `pytest tests/unit/` succeeds
- All utility functions tested
- Tests are fast (<1 second total)

---

- [ ] T043 [P] Add integration test for full workflow in tests/integration/

**Acceptance Criteria**:
- Test file: `tests/integration/test_full_workflow.py`
- Sets up test web application (simple HTML pages with login)
- Creates test requirements document
- Runs full CLI workflow:
  - Parse requirements
  - Authenticate
  - Verify requirements
  - Generate reports
- Validates all three report formats created
- Cleans up test artifacts after run
- Test takes <30 seconds to run

**Verification**:
- Run `pytest tests/integration/test_full_workflow.py`
- Test passes end-to-end
- All assertions verify expected behavior

---

- [ ] T044 Update quickstart.md with final CLI examples

**Acceptance Criteria**:
- All examples use final CLI syntax
- Examples tested and working
- Common patterns documented:
  - Basic usage
  - Debug mode
  - CI/CD mode
  - Environment variables
- Troubleshooting section includes common errors and solutions
- Links to full documentation

**Verification**:
- All examples can be copy-pasted and run successfully
- Troubleshooting solutions actually work

---

- [ ] T045 Run quickstart.md validation

**Acceptance Criteria**:
- Manually execute all examples from quickstart.md
- Verify each example produces expected output
- Fix any discrepancies between docs and actual behavior
- Ensure exit codes correct
- Ensure report formats match documentation

**Verification**:
- Checklist: each example from quickstart.md tested
- All examples work as documented
- No surprises or undocumented behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P2): Can start after Foundational - No dependencies on US1 (independent)
  - User Story 3 (P3): Can start after Foundational - Integrates output from US1

- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - Can be implemented first (MVP)
- **User Story 2 (P2)**: Independent of US1 - Adds refinement logic to verification flow
- **User Story 3 (P3)**: Uses reports from US1 - Adds additional output formats

### Within Each User Story

- **US1**:
  - Parsers (T016, T017, T018) can run in parallel
  - Browser service methods (T019-T024) can run in parallel
  - Agent service (T025) depends on browser service methods
  - Session management (T027) can run in parallel with agent service
  - Report generation (T026) depends on models being complete
  - CLI integration (T028) depends on all above

- **US2**:
  - All tasks depend on US1 agent service existing
  - Ambiguity detection (T029) and refinement (T030) can run in parallel
  - Integration (T031) depends on both above
  - Report updates (T032) depends on integration

- **US3**:
  - JUnit XML (T033), HTML (T034), documentation (T037) can run in parallel
  - Exit code logic (T035) and format selection (T036) depend on report generators
  - All tasks use reports from US1

### Parallel Opportunities

- **Phase 1**: All tasks can run in parallel (T001-T004)
- **Phase 2**: All model creation tasks (T005-T012) and utilities (T013-T014) can run in parallel
- **Phase 3 (US1)**: Parsers in parallel, browser methods in parallel
- **Phase 4 (US2)**: Detection and suggestion in parallel
- **Phase 5 (US3)**: Report generators and docs in parallel
- **Phase 6**: All polish tasks can run in parallel (documentation, logging, tests)

---

## Parallel Example: User Story 1

```bash
# Launch parser tasks together:
Task: T016 - Plain text parser
Task: T017 - Markdown parser
Task: T018 - ParserService main class (depends on T016, T017)

# Launch browser service methods together:
Task: T019 - Browser initialization
Task: T020 - Authentication
Task: T021 - Auth state management
Task: T022 - Navigation
Task: T023 - Element verification
Task: T024 - Screenshot capture

# Agent service (T025) and session management (T027) can run in parallel
# CLI integration (T028) waits for all above
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T015) - CRITICAL blocking phase
3. Complete Phase 3: User Story 1 (T016-T028)
4. **STOP and VALIDATE**: Test User Story 1 independently with real requirements and app
5. Generate reports, verify all features work
6. Deploy/demo if ready (MVP complete!)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test refinement independently → Deploy/Demo
4. Add User Story 3 → Test CI/CD integration → Deploy/Demo
5. Add Polish → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (critical path)
2. Once Foundational is done:
   - Developer A: User Story 1 (T016-T028)
   - Developer B: User Story 2 (T029-T032) - wait for US1 agent_service structure
   - Developer C: User Story 3 (T033-T037) - wait for US1 report structures
3. Stories complete and integrate independently

---

## Notes

- **[P] tasks**: Different files, no dependencies - safe to parallelize
- **[Story] label**: Maps task to specific user story for traceability (US1, US2, US3)
- **Acceptance Criteria**: Every task has clear, testable conditions for completion (per user request)
- **Verification Steps**: Each task includes how to verify the work (per user request)
- Each user story should be independently completable and testable
- Tests are NOT included (no explicit TDD request in specification)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Foundational phase is CRITICAL - all user stories blocked until complete
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Summary

**Total Tasks**: 45

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 11 tasks
- Phase 3 (User Story 1 - P1): 13 tasks
- Phase 4 (User Story 2 - P2): 4 tasks
- Phase 5 (User Story 3 - P3): 5 tasks
- Phase 6 (Polish): 8 tasks

**By User Story**:
- Setup/Foundational: 15 tasks (infrastructure)
- US1 (MVP): 13 tasks (core requirements verification)
- US2 (Refinement): 4 tasks (ambiguity detection and suggestions)
- US3 (CI/CD): 5 tasks (report formats and integration)
- Polish: 8 tasks (documentation, tests, final touches)

**Parallel Opportunities**: 28 tasks marked with [P] can run in parallel within their phase

**Suggested MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only) = 28 tasks

This delivers core requirements verification capability with JSON reports and CLI interface.
