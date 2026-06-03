# Phase 0 Research: about-this-mac Information CLI

**Feature**: 001-mac-info-cli | **Date**: 2026-06-03

This feature reverse-documents a shipped tool, so "research" is the act of
reading the existing implementation to confirm how each contract is realized and
resolving the three clarification items. There were no open `NEEDS
CLARIFICATION` markers entering Phase 0.

## Decision 1 — Public-format privacy boundary

- **Decision**: `public` output excludes (1) serial number, (2) unique device
  identifiers, and (3) network identifiers (MAC addresses, hostname), including
  fields not surfaced today.
- **Rationale**: `format_output_as_public` (`utils/formatting.py:606`) is
  **allowlist-based** — it constructs output only from Device, Model, Release
  Date, Processor, Hard Drive, and Memory fields and never reads `serial_number`
  or any network field. An allowlist is inherently forward-safe: a future
  hardware field cannot leak into `public` unless a developer explicitly adds it
  to this function. This matches the broadest clarification answer at no
  implementation cost.
- **Alternatives considered**: A denylist (strip known-sensitive keys) was
  rejected — it would fail open for any new sensitive field, contradicting the
  "fields not surfaced today" clause.
- **Verification gap found**: `test_report.py:66` feeds a `serial_number` into
  the public formatter but asserts only the presence of safe fields, never the
  absence of the serial. A negative regression test is required (Phase 1).

## Decision 2 — Error exit-code contract

- **Decision**: Errors guarantee a non-zero exit status; no specific code is
  part of the contract.
- **Rationale**: `CliError` defaults `exit_code=1` (`output.py:12`) and
  `handle_error` (`output.py:66`) routes both `CliError` and generic exceptions
  through `Output.error` → `sys.exit`. The non-Darwin guard raises `SystemError`,
  which `handle_error` also turns into a non-zero exit. Pinning to "non-zero"
  rather than "exactly 1" leaves room to introduce a code taxonomy later without
  breaking automation, while still giving scripts a reliable success/failure
  signal via `exit 0` vs non-zero.
- **Alternatives considered**: "Exactly 1" (too rigid; blocks future taxonomy);
  distinct per-class codes (not implemented today; would be invented scope).

## Decision 3 — Performance / latency target

- **Decision**: No hard latency gate. Invariant is "must terminate / must not
  hang" and "avoid duplicate expensive system calls".
- **Rationale**: End-to-end runtime is dominated by `system_profiler` and
  `sysctl`, which vary by machine, permissions, and cold/warm caches. A fixed
  second-count would be flaky and outside the tool's control. The architecture
  already separates gathering from formatting (Constitution Principle IV), so the
  controllable performance concern is not re-running expensive commands, which
  the gatherers handle.
- **Alternatives considered**: "Under 5s/10s full report" — rejected as flaky and
  not enforceable given external command latency.

## Decision 4 — Non-macOS behavior

- **Decision**: Fail early and clearly on non-Darwin platforms with a non-zero
  exit.
- **Rationale**: `MacInfoGatherer.__init__` checks
  `platform.system() == "Darwin"` (`hardware_info.py:83`) and raises
  `SystemError("This script only works on macOS")` before any gathering. This is
  surfaced as a single clear error via `handle_error`.
- **Verification gap found**: no test asserts the non-Darwin early-exit path. A
  test that monkeypatches `platform.system` and asserts a non-zero exit is
  required (Phase 1).

## Outcome

All clarifications resolved; two regression-test gaps identified for Phase 1.
No production code change is warranted — the implementation conforms.
