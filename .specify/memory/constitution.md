<!--
  SYNC IMPACT REPORT
  ==================
  Version change: [TEMPLATE] → 1.0.0 (initial ratification)

  Added principles:
  - I. Simplicity First (minimum code, no overcomplications)
  - II. Cross-Platform Compatibility (run on any OS)
  - III. UV + Python Stack (technology standardization)
  - IV. Maintainability (easy to maintain and understand)
  - V. Usability (very easy to use)

  Added sections:
  - Technology Standards (UV + Python requirements)
  - Development Workflow (simplicity enforcement)

  Templates requiring updates:
  ✅ .specify/templates/plan-template.md - Constitution Check section compatible
  ✅ .specify/templates/spec-template.md - User story focus compatible
  ✅ .specify/templates/tasks-template.md - Task organization compatible

  Follow-up TODOs: None
-->

# Playwright QA Agent Constitution

## Core Principles

### I. Simplicity First

**MUST minimize code complexity and volume at all costs.**

- Every feature MUST be implemented with the absolute minimum code required
- Complex abstractions, design patterns, or frameworks are FORBIDDEN unless explicitly justified
- Code MUST be self-evident; if it requires extensive comments, it's too complex
- YAGNI (You Aren't Gonna Need It) is strictly enforced - no speculative features
- Duplication is preferable to the wrong abstraction

**Rationale**: Minimal code means fewer bugs, faster comprehension, easier maintenance, and lower cognitive load for all contributors.

### II. Cross-Platform Compatibility

**MUST run on any major operating system without modification.**

- All code MUST work identically on Linux, macOS, and Windows
- Platform-specific code is FORBIDDEN unless no alternative exists
- File paths MUST use cross-platform conventions (pathlib, not string manipulation)
- Shell commands MUST be avoided; use Python standard library alternatives
- Testing MUST verify behavior across platforms before release

**Rationale**: Users should never encounter "works on my machine" problems. True portability means zero friction for adoption.

### III. UV + Python Stack

**MUST use UV as the package manager and Python as the implementation language.**

- Python version: 3.11+ (for modern syntax and performance)
- Package management: UV exclusively (no pip, poetry, conda, or other tools)
- Dependency declarations MUST be minimal - only include what's directly used
- Virtual environment management via UV
- No additional build tools or compilers required

**Rationale**: UV provides fast, reliable, cross-platform dependency resolution. Standardizing on one stack eliminates tooling complexity and environment inconsistencies.

### IV. Maintainability

**MUST prioritize code that is easy to understand, modify, and debug.**

- Functions MUST do one thing and do it well (single responsibility)
- Module organization MUST be flat and obvious (no deep nesting)
- Naming MUST be self-documenting (clear > clever)
- Side effects MUST be explicit and minimal
- Error messages MUST tell users exactly what went wrong and how to fix it

**Rationale**: Code is read far more often than written. Maintainability directly correlates with long-term project health and contributor velocity.

### V. Usability

**MUST be very easy for end users to install, configure, and use.**

- Installation MUST be a single command: `uv pip install playwright-qa-agent`
- Configuration MUST have sensible defaults (zero-config for common cases)
- CLI commands MUST be intuitive and follow standard conventions
- Error messages MUST be actionable (not just stack traces)
- Documentation MUST show working examples, not just API references

**Rationale**: A tool that's hard to use won't be used. User friction is a feature killer.

## Technology Standards

### Required Stack

- **Language**: Python 3.11+
- **Package Manager**: UV
- **Testing**: pytest (minimal configuration)
- **Linting**: ruff (fast, zero-config)
- **Type Checking**: pyright or mypy (optional but recommended)

### Forbidden

- Additional build tools (webpack, babel, etc.)
- Complex frameworks (unless the feature is fundamentally impossible without them)
- Platform-specific dependencies
- Non-Python runtime requirements (Node.js, Ruby, etc.)

## Development Workflow

### Complexity Gates

**BEFORE adding any dependency or abstraction**:

1. Can this be done with Python standard library? If yes, MUST use stdlib.
2. Can this be done with 10 lines of simple code? If yes, write those 10 lines.
3. Does this solve an actual problem we have today? If no, FORBIDDEN.

### Code Review Checklist

Every pull request MUST answer:

- Why is this code necessary?
- Why is this the simplest possible solution?
- Does this work on Linux, macOS, and Windows?
- Can a new contributor understand this in 60 seconds?

### Refactoring Policy

- Refactoring to reduce lines of code: ALWAYS approved
- Refactoring to add abstractions: Requires justification
- Refactoring to "follow best practices": Rejected unless measurable benefit

## Governance

### Amendment Process

1. Proposed changes MUST be documented in a pull request
2. Justification MUST explain why the constitution itself is insufficient
3. Approval requires demonstrating that alternatives within current principles were exhausted
4. Amendments increment version according to semver:
   - MAJOR: Removing or fundamentally changing a principle
   - MINOR: Adding new principles or sections
   - PATCH: Clarifications or typo fixes

### Compliance

- All pull requests MUST verify compliance with these principles
- Complexity violations MUST be justified in writing (see plan-template.md)
- The constitution supersedes all other guidelines, conventions, or "best practices"

### Version Control

Changes to this document MUST update:
- `CONSTITUTION_VERSION`: Increment per semver rules above
- `LAST_AMENDED_DATE`: Set to date of change (ISO 8601 format)
- Sync Impact Report: Document what changed and template impacts

**Version**: 1.0.0 | **Ratified**: 2026-02-20 | **Last Amended**: 2026-02-20
