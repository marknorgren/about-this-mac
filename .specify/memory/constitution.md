<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Placeholder Principle 1 -> I. CLI Contracts Are Product Contracts
- Placeholder Principle 2 -> II. macOS Source Truth and Privacy Boundaries
- Placeholder Principle 3 -> III. Test-First, Reproducible Quality Gates
- Placeholder Principle 4 -> IV. Deep Modules Over Pass-Through Surfaces
- Placeholder Principle 5 -> V. Human and Agent Operability
Added sections:
- Technical Constraints
- Development Workflow and Quality Gates
Removed sections:
- None
Templates requiring updates:
- ✅ updated .specify/templates/plan-template.md
- ✅ updated .specify/templates/spec-template.md
- ✅ updated .specify/templates/tasks-template.md
- ✅ reviewed .specify/templates/commands/*.md (directory absent; no update required)
- ✅ reviewed README.md, AGENTS.md, and docs/refactoring-walkthrough.md (no update required)
Follow-up TODOs:
- None
-->
# about-this-mac Constitution

## Core Principles

### I. CLI Contracts Are Product Contracts

The `about-this-mac` command is the product boundary. Every feature MUST preserve
documented flags, output formats (`text`, `json`, `yaml`, `markdown`, `public`,
`simple`), stdout/stderr separation, exit behavior, and `--help` discoverability
unless a feature spec explicitly records a breaking change and migration path.
New flags, sections, and output fields MUST be documented and covered by focused
tests.

Rationale: humans use the CLI directly, and agents depend on predictable
commands and structured output for automation.

### II. macOS Source Truth and Privacy Boundaries

System facts MUST come from explicit macOS sources already used by the project
(`system_profiler`, `sysctl`, `pmset`, `networksetup`, `netstat`, or Python's
platform APIs) or from a newly documented source with parsing tests. Raw commands
MUST continue to expose source data for diagnosis. Public listing output MUST
remain free of serial numbers and unique device identifiers; any feature that
adds, removes, or relocates sensitive identifiers MUST document the affected
formats and include tests for the boundary.

Rationale: this tool reports local device facts, so accuracy, provenance, and
privacy boundaries are part of correctness.

### III. Test-First, Reproducible Quality Gates

New code MUST start with a failing test when practical. If tests are skipped for
a non-code or explicitly exploratory change, the plan or task list MUST record
the rationale. Changes MUST pass the repo's CI-parity gates before push or PR:
`uv sync --extra dev`, `just fmt-check`, `just type-check`, `just lint`, and the
pytest coverage command from AGENTS.md. Changes touching CLI behavior, system
data gathering, or formatting MUST also dogfood the affected CLI outputs.

Rationale: macOS command output varies by machine and permissions; focused tests
and dogfooding catch regressions before users or agents depend on them.

### IV. Deep Modules Over Pass-Through Surfaces

Gathering, raw command execution, formatting, output handling, and CLI dispatch
MUST stay separated. Formatters MUST NOT trigger system commands. Gatherers MUST
NOT expose pass-through wrappers solely to leak internal command helpers. New
abstractions MUST reduce real duplication or isolate a source of change already
present in the codebase.

Rationale: the repo has already paid down complexity from hidden subprocess
calls and pass-through methods; future work must not reintroduce those failure
modes.

### V. Human and Agent Operability

Every feature plan MUST state testable acceptance criteria, one-command
verification, allowed side effects, evidence requirements, and stop or escalation
conditions. Commands useful to automation MUST expose stable machine-readable
output, raw diagnostic output, or both. Errors MUST include enough context for a
human or agent to retry, downgrade gracefully, or escalate.

Rationale: the project is both a human CLI and an agent-operable diagnostic
surface.

## Technical Constraints

- Runtime target: macOS 11 or later with Python 3.10 or later. Non-macOS
  execution MUST fail early with a clear error.
- Package and dependency changes MUST use `pyproject.toml` and `uv`; lockfiles
  and generated dependency metadata MUST NOT be edited by hand.
- Existing helpers in `about_this_mac.utils` MUST be reused before adding new
  command, parsing, or formatting utilities.
- JSON and YAML outputs MUST parse successfully. Text color MUST remain limited
  to TTY text output and continue to respect `NO_COLOR`, `TERM=dumb`, output
  files, and `--no-color`.
- Privileged macOS commands MUST degrade gracefully under limited permissions,
  using documented unknown or empty values plus actionable hints instead of
  uncaught tracebacks.
- Secrets and credentials MUST NOT be stored in repo files; use 1Password-backed
  configuration when secrets are required.

## Development Workflow and Quality Gates

- Specifications MUST keep user stories independently testable and list the
  exact CLI commands or observable outputs that prove each story works.
- Plans MUST complete the Constitution Check before Phase 0 research and repeat
  it after Phase 1 design.
- Task lists MUST put failing tests before implementation for code changes and
  include exact file paths in every task.
- Feature work MUST use the repository command surface (`uv`, `just`, and
  `about-this-mac`) rather than undocumented local scripts.
- Before push or PR, contributors MUST verify the private push guardrails when
  branch or remote behavior is relevant: `git config --get remote.pushDefault`,
  `git config --get core.hooksPath`, and `.githooks/pre-push`.

## Governance

This constitution supersedes conflicting project practices for specs, plans,
tasks, code review, and agent work. Amendments MUST include a Sync Impact Report,
the semantic version change, updated dependent templates, and verification
evidence.

Versioning policy:
- MAJOR: incompatible governance changes, removed principles, or redefined
  public obligations.
- MINOR: new principles, new mandatory sections, or materially expanded
  compliance gates.
- PATCH: clarifications, typo fixes, and non-semantic wording updates.

Compliance review:
- Plans MUST record pass/fail status for each principle in the Constitution
  Check.
- Reviews MUST block changes that violate a MUST requirement without an approved
  amendment or documented exception.
- Final implementation summaries MUST list the verification commands that ran
  and any skipped checks with the reason.

**Version**: 1.0.0 | **Ratified**: 2026-06-03 | **Last Amended**: 2026-06-03
