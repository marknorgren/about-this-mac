# Implementation Plan: about-this-mac Information CLI

**Branch**: `001-mac-info-cli` | **Date**: 2026-06-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-mac-info-cli/spec.md`

## Summary

This is a **conformance plan** for an already-shipped feature, not a greenfield
build. `about-this-mac` v0.2.2 already implements the full CLI surface, six
output formats, macOS source gathering, and the public-format privacy boundary
described in the spec. The work this plan governs is therefore: (1) verify the
shipped implementation against each spec contract, and (2) close the
regression-test gaps surfaced during clarification and analysis — a negative
privacy assertion for the `public` format, a non-macOS early-exit test, a
limited-permission / no-battery graceful-degradation test, and a
mutually-exclusive-flag usage-error test. No production behavior changes; the
deliverable is documented conformance plus guard tests so the baseline contract
cannot silently regress.

## Technical Context

**Language/Version**: Python 3.10+ (`requires-python = ">=3.10"` in `pyproject.toml`)

**Primary Dependencies**: PyYAML (runtime); pytest, pytest-cov, black, pylint,
mypy, types-PyYAML (dev). No new dependencies required.

**Storage**: None. Output goes to stdout or a `--output` file. The `reports/`
directory is gitignored and used only for local dogfood verification (never
committed — public repo, no real machine data).

**Testing**: pytest with coverage (`--cov=src/about_this_mac`), 50 existing test
functions across `tests/`. CI-parity gate: `uv sync --extra dev`, `just
fmt-check`, `just type-check`, `just lint`, pytest. CLI dogfood for changed
surfaces per CLAUDE.md.

**Target Platform**: macOS 11+ (Darwin). Non-macOS raises `SystemError`
(`hardware_info.py:83`), surfaced by `handle_error` as a non-zero exit.

**Project Type**: Single Python CLI package (`src/about_this_mac/`).

**Performance Goals**: No hard latency gate (spec SC-008). Runtime is dominated
by `system_profiler`/`sysctl` calls; the only performance invariant is "must not
hang" and "do not issue duplicate expensive system calls" (Constitution
Principle IV — gathering is separated from formatting).

**Constraints**: Graceful degradation under limited permissions (documented
unknown/empty values + hint); valid JSON/YAML output; `public` format must
exclude serial number, unique device identifiers, and network identifiers
(spec OC-004); color only on TTY text output respecting `NO_COLOR`/`TERM=dumb`/
`--no-color`/file output.

**Scale/Scope**: Single-user, single-invocation local diagnostic CLI.

**Unknowns**: None. All three clarification items (privacy breadth, exit-code
contract, performance gate) were resolved in the spec's Clarifications session
(2026-06-02). No `NEEDS CLARIFICATION` markers remain.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial evaluation (pre-Phase 0):**

- **CLI Contract** — **PASS**. No flags, formats, stdout/stderr split, or exit
  behavior change. Spec OC-001 records the existing surface verbatim from
  `cli.py`. No breaking change, so no migration path required.
- **macOS Source Truth and Privacy** — **PASS with one test gap**. All facts map
  to documented sources (spec OC-003, README "Data Sources"). The `public`
  formatter is allowlist-based (`formatting.py:606`) and emits only
  Device/Model/Release Date/Processor/Hard Drive/Memory — it never reads serial
  or network fields, so it satisfies the widened OC-004 boundary by construction.
  **Gap**: no negative test asserts serial/network absence in `public` output
  (`test_report.py:66` sets a serial but asserts only presence of other fields).
  Remediated in Phase 1 (guard test).
- **Test-First Quality** — **PASS**. The four new guard tests are written before
  any code is touched. Because the implementation already conforms, each is
  expected to pass on first run; to honor red-green every guard test is first
  asserted against a deliberately-failing condition (leaky stub, non-Unknown
  value) to prove it can fail, then pointed at the real behavior. The non-macOS
  test monkeypatches `platform.system` to a non-Darwin value and asserts a
  non-zero exit; the degradation test monkeypatches command execution to empty
  output and asserts `UNKNOWN_VALUE` markers with no uncaught exception; the
  flag test asserts argparse rejects mutually-exclusive flags.
- **Deep Modules** — **PASS**. No change to module boundaries. Gathering
  (`hardware/`, `battery/`), raw execution (`commands/raw.py`), formatting
  (`utils/formatting.py`), output handling (`output.py`), and dispatch (`cli.py`)
  stay separated. New tests live under `tests/` and introduce no pass-through
  wrappers and do not make formatters run system commands.
- **Human and Agent Operability** — **PASS**. Acceptance criteria, one-command
  verification, allowed side effects, evidence, and escalation are specified in
  quickstart.md and the spec's per-story Independent Tests.

**Post-Phase 1 re-evaluation:** PASS (unchanged). Design artifacts add only
documentation and four test additions; no new abstractions, dependencies, or
boundary violations introduced. Complexity Tracking table is empty — no
violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-mac-info-cli/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli-contract.md  # Phase 1 output (CLI command schema)
├── checklists/
│   └── requirements.md  # From /speckit.specify
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

Existing files this feature **verifies** (read-only — no behavior change):

```text
src/about_this_mac/
├── cli.py                       # arg parsing, dispatch, exit behavior (OC-001, FR-014)
├── output.py                    # CliError, Output, handle_error (FR-013, FR-014)
├── commands/
│   ├── raw.py                   # --*-info raw passthrough (FR-008, US4)
│   └── report.py                # format dispatch incl. public/simple (US1-3)
├── hardware/hardware_info.py    # HardwareInfo/MemoryInfo/StorageInfo; Darwin guard (FR-001/3/12)
├── battery/battery_info.py      # BatteryInfo (FR-002)
└── utils/
    ├── formatting.py            # six formatters; public allowlist (OC-002/04, FR-011/15)
    ├── command.py               # subprocess helper
    └── system.py                # sysctl/system helpers
```

Files this feature **adds to** (test-only):

```text
tests/
├── commands/test_report.py      # ADD: negative privacy assertion for public format (T008)
├── test_cli.py                  # ADD: non-macOS early-exit (T012) + mutually-exclusive flags (T016)
├── test_hardware_info.py        # ADD: limited-permission graceful-degradation (T015)
└── test_battery_info.py         # ADD: no-battery degradation path (T015)
```

**Structure Decision**: Reuse all existing modules; touch only `tests/`. No new
source modules, packages, or helpers. This matches Constitution Principle IV
(reuse existing helpers before adding new ones) and the "smallest change that
solves the root cause" rule — the only real change is adding the four missing
guard tests; everything else is verification of shipped behavior.

## Complexity Tracking

> No Constitution Check violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |
