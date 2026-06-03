# Tasks: about-this-mac Information CLI

**Input**: Design documents from `/specs/001-mac-info-cli/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: This feature reverse-documents shipped v0.2.2. No production behavior
changes. The only new code is four regression-test additions that close gaps
found during planning and analysis: public-format privacy negative assertion
(T008), non-macOS early-exit (T012), limited-permission / no-battery graceful
degradation (T015), and conflicting-flag usage errors (T016). All other tasks
verify existing behavior against the spec contracts. Test tasks are written
before any change and must demonstrably be able to fail (red-green) per
Constitution Principle III.

**Organization**: Grouped by user story. Each story is independently verifiable
via its quickstart command.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story the task serves (US1–US5)
- All paths are repo-relative; this is a single Python project (`src/`, `tests/`)

## Path Conventions

- Source (read-only this feature): `src/about_this_mac/`
- Tests (only files added to): `tests/commands/test_report.py`, `tests/test_cli.py`
- Verification: `uv`, `just`, and `about-this-mac` per `CLAUDE.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Reproducible environment and a known-green baseline.

- [X] T001 Sync dev environment: `uv sync --extra dev`
- [X] T002 Record CI-parity baseline (green) before changes: `just fmt-check && just type-check && just lint && uv run pytest --cov=src/about_this_mac --cov-report=term-missing:skip-covered tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm shared fixtures exist; no new infrastructure is required.

- [X] T003 Confirm existing sample-data fixtures in `tests/conftest.py` cover hardware + battery dictionaries used by formatter tests; reuse them (do NOT add new fixtures unless a gap is proven)

**Checkpoint**: Baseline green and fixtures confirmed — story verification can begin in parallel.

---

## Phase 3: User Story 1 - Complete Mac summary (Priority: P1) 🎯 MVP

**Goal**: Default text report covering hardware + battery + system facts.

**Independent Test**: `about-this-mac` prints a human-readable report and exits 0.

- [X] T004 [US1] Verify default report and section filters: run `about-this-mac`, `about-this-mac --section hardware`, `about-this-mac --section battery`; confirm correct scoping and exit 0 (dogfood to `reports/`, do not commit)
- [X] T005 [P] [US1] Confirm existing coverage for the default/text path in `tests/utils/test_formatting.py` and `tests/commands/test_report.py` still passes (no change expected)

**Checkpoint**: US1 verified — MVP behavior confirmed.

---

## Phase 4: User Story 2 - Machine-readable output (Priority: P1)

**Goal**: Valid JSON/YAML/Markdown output and file writing for automation.

**Independent Test**: `--format json` parses as JSON; `--format yaml` parses as YAML.

- [X] T006 [P] [US2] Verify structured output parses: `about-this-mac --format json | python -m json.tool` and `about-this-mac --format yaml | python -c 'import sys,yaml; yaml.safe_load(sys.stdin)'`
- [X] T007 [P] [US2] Verify file output: `about-this-mac --json -o /tmp/atm.json` writes the report; `-o -` writes to stdout

**Checkpoint**: US2 verified — automation contract holds.

---

## Phase 5: User Story 3 - Privacy-safe public listing (Priority: P2)

**Goal**: `public` format excludes serial, unique device IDs, and network IDs (OC-004).

**Independent Test**: `about-this-mac --format public` contains no serial/device-ID/MAC/hostname string.

### Test for User Story 3 (write before any change) ⚠️

- [X] T008 [US3] Add the missing negative privacy regression test in `tests/commands/test_report.py`: feed a fixture whose hardware dict includes `serial_number`, `device_identifier`, and synthetic MAC/hostname values into `format_output_as_public`, then assert NONE of those strings appear in the output. Prove it can fail first (assert against a deliberately-leaky local stub formatter), then point the assertion at the real `format_output_as_public` and confirm it passes. This guards the allowlist against future leaks.

### Verification for User Story 3

- [X] T009 [US3] Dogfood `about-this-mac --format public` and `about-this-mac --format simple`; confirm `public` omits the serial while `simple` includes it (run the quickstart privacy spot-check; expect `OK`)

**Checkpoint**: US3 verified — privacy boundary is now test-guarded.

---

## Phase 6: User Story 4 - Raw source data (Priority: P2)

**Goal**: Each `--*-info` flag prints its raw macOS source output and short-circuits the report.

**Independent Test**: `about-this-mac --hardware-info` prints raw `SPHardwareDataType`.

- [X] T010 [P] [US4] Verify each raw flag prints source output and skips the formatted report: `--hardware-info`, `--power-info`, `--graphics-info`, `--storage-info`, `--memory-info`, `--audio-info`, `--network-info`, and `--release-date`; confirm existing coverage in `tests/commands/test_raw.py` passes

**Checkpoint**: US4 verified — raw passthrough intact.

---

## Phase 7: User Story 5 - Discoverability (Priority: P3)

**Goal**: `--help` lists flags + examples; `--version` prints version.

**Independent Test**: `about-this-mac --help` and `about-this-mac --version` both exit 0.

- [X] T011 [P] [US5] Verify `about-this-mac --help` lists all flags + examples and `about-this-mac --version` prints the version; confirm coverage in `tests/test_cli.py` passes

**Checkpoint**: US5 verified.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Close the second test gap and confirm cross-cutting guarantees.

### Test (write before any change) ⚠️

- [X] T012 Add non-macOS early-exit test in `tests/test_cli.py`: monkeypatch `about_this_mac.hardware.hardware_info.platform.system` to return `"Linux"`, invoke the CLI entry point, and assert it exits non-zero with the clear "only works on macOS" message and emits no partial report. (Characterization test for the existing `hardware_info.py:83` guard — the gap is the missing test, not the behavior; verify it fails if the guard is removed.)

### Test (write before any change) ⚠️

- [X] T015 Add graceful-degradation test (FR-013, SC-006) in `tests/test_hardware_info.py` (and `tests/test_battery_info.py` for the no-battery path): monkeypatch the gatherer's command execution to return empty/failed output, then assert the gatherer still produces a report whose unresolved fields render as the `UNKNOWN_VALUE` marker and that no uncaught exception escapes. Prove it can fail (e.g., temporarily assert a non-Unknown value) before pinning the real assertion. Closes analysis finding G1.

### Cross-cutting verification

- [X] T013 Verify verbosity + color contract (FR-009, FR-015): confirm `-q` suppresses warnings and `-v` enables DEBUG logging; `NO_COLOR=1 about-this-mac` and `about-this-mac --color -o /tmp/atm.txt` emit no ANSI codes while `--color` on a TTY does
- [X] T014 Verify error/exit contract (FR-014): an induced error exits non-zero (not asserting a specific code) and writes the message to stderr
- [X] T016 Verify mutually-exclusive flags (spec edge case) in `tests/test_cli.py`: assert `--json --plain`, `--color --no-color`, and `-v -q` each exit non-zero with an argparse usage error. Closes analysis finding G2.
- [X] T017 Run the full CI-parity gate green and confirm coverage did not decrease vs the T002 baseline: `just fmt-check && just type-check && just lint && uv run pytest --cov=src/about_this_mac --cov-report=term-missing:skip-covered tests/`

**Checkpoint**: All four test gaps closed; all contracts verified; gate green.

---

## Dependencies & Execution Order

- **Setup (T001–T002)** → blocks everything.
- **Foundational (T003)** → blocks story phases.
- **User stories (Phase 3–7)** are independent of each other and can run in any
  order or in parallel once Foundational is done. Each is independently testable.
- **Polish (Phase 8)**: T012, T015, and T016 are independent (test-only); T017
  (full gate) MUST run last, after T008, T012, T015, and T016 add their tests.
- **Story priority for incremental delivery**: US1 (MVP) → US2 → US3 → US4 → US5.

### Parallel opportunities

- After T003: T004/T005, T006/T007, T010, T011 can proceed in parallel (distinct
  commands/files).
- The new-test tasks touch different files and can be written in parallel:
  `T008` (`tests/commands/test_report.py`), `T012` + `T016` (`tests/test_cli.py`
  — same file, so sequential to each other), and `T015`
  (`tests/test_hardware_info.py` / `tests/test_battery_info.py`).

## Implementation Strategy

- **MVP scope**: Phase 1–3 (Setup + Foundational + US1) proves the core tool works.
- **Real new work**: T008, T012, T015, and T016 are the only tasks that add code
  (test-only). Everything else is verification of shipped v0.2.2 behavior.
- **No production source changes** are planned; if any verification task reveals a
  contract violation, stop and open a separate fix spec (do not patch silently).
