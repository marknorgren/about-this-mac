# Feature Specification: about-this-mac Information CLI

**Feature Branch**: `001-mac-info-cli`

**Created**: 2026-06-02

**Status**: Draft (reverse-engineered from existing implementation at v0.2.2)

**Input**: User description: "generate the spec for what is built here"

## Overview

`about-this-mac` is a command-line tool that gathers and reports detailed
information about a Mac — hardware, battery, storage, memory, graphics, audio,
network, and macOS version — for documentation, diagnostics, and resale
listings. It reads facts from documented macOS sources (`system_profiler`,
`sysctl`, `pmset`, `networksetup`, `netstat`, and Python platform APIs) and
renders them in human- and machine-readable formats. This specification
describes the behavior already shipped, so it serves as the baseline contract
for future changes.

## Clarifications

### Session 2026-06-02

- Q: Beyond the serial number, how broad is the `public`-format privacy
  exclusion? → A: Exclude the serial number, all unique device identifiers
  (hardware/provisioning UUID, device identifier), AND network identifiers
  (Wi-Fi/Bluetooth MAC addresses, hostname) — even fields not surfaced today.
- Q: What is the error exit-code contract for automation? → A: Guarantee
  non-zero on error; no specific code is promised, leaving room for a future
  taxonomy without a breaking change.
- Q: Should Success Criteria include a measurable runtime/latency target? → A:
  No hard target; runtime is dominated by macOS source commands outside the
  tool's control.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a complete Mac summary on the terminal (Priority: P1)

A Mac owner or technician runs the tool with no arguments and immediately sees a
readable summary of the machine's hardware, battery, and system facts in the
terminal.

**Why this priority**: This is the default invocation and the core value of the
tool — answering "what Mac is this and what condition is it in?" without the user
navigating System Settings or remembering `system_profiler` incantations. Every
other capability builds on the gathered data this story produces.

**Independent Test**: Run `about-this-mac` on a supported Mac and confirm it
prints a human-readable report covering hardware, battery, and macOS version to
stdout and exits 0.

**Acceptance Scenarios**:

1. **Given** a supported Mac, **When** the user runs `about-this-mac`, **Then**
   the tool prints a text report including model, processor, memory, storage,
   battery health, and macOS version, and exits 0.
2. **Given** a supported Mac, **When** the user runs `about-this-mac --section
   hardware`, **Then** only the hardware section is printed.
3. **Given** a supported Mac, **When** the user runs `about-this-mac --section
   battery`, **Then** only the battery section is printed.
4. **Given** stdout is a TTY, **When** the user runs `about-this-mac --color`,
   **Then** the text report uses color; **When** the user runs `--no-color` or
   `NO_COLOR` is set or `TERM=dumb` or output is redirected to a file, **Then**
   no color codes are emitted.

---

### User Story 2 - Produce machine-readable output for automation (Priority: P1)

An agent or script runs the tool requesting structured output and consumes the
result programmatically.

**Why this priority**: The tool is an agent-operable diagnostic surface. Stable,
parseable output is what lets automation collect fleet inventory or feed asset
systems without scraping human text.

**Independent Test**: Run `about-this-mac --format json` and confirm the output
parses as valid JSON; run `--format yaml` and confirm it parses as valid YAML.

**Acceptance Scenarios**:

1. **Given** a supported Mac, **When** the user runs `about-this-mac --format
   json` (or the `--json` shorthand), **Then** valid JSON is written to stdout.
2. **Given** a supported Mac, **When** the user runs `about-this-mac --format
   yaml`, **Then** valid YAML is written to stdout.
3. **Given** a supported Mac, **When** the user runs `about-this-mac --format
   markdown`, **Then** a Markdown document is produced.
4. **Given** any format, **When** the user adds `--output report.json` (or
   `-o report.json`), **Then** the report is written to that file; **When** the
   user passes `-o -`, **Then** the report is written to stdout.

---

### User Story 3 - Generate a privacy-safe listing for resale (Priority: P2)

A seller produces a buyer-facing summary that highlights the desirable specs
without leaking the device serial number or unique identifiers.

**Why this priority**: Resale is a named use case. The privacy boundary between
internal and public output is a correctness requirement, not a nicety, because
serial numbers enable warranty fraud and tracking.

**Independent Test**: Run `about-this-mac --format public` and confirm the output
contains marketing-friendly specs (model, size, storage, memory) and contains no
serial number, unique device identifier, or network identifier (MAC address,
hostname) string.

**Acceptance Scenarios**:

1. **Given** a supported Mac, **When** the user runs `about-this-mac --format
   public`, **Then** a sales-friendly summary is produced that omits the serial
   number, all unique device identifiers (hardware/provisioning UUID, device
   identifier), and network identifiers (Wi-Fi/Bluetooth MAC addresses,
   hostname).
2. **Given** a supported Mac, **When** the user runs `about-this-mac --format
   simple`, **Then** a concise summary is produced that DOES include the serial
   number (internal/owner use).

---

### User Story 4 - Inspect raw source data for diagnosis (Priority: P2)

A technician or agent needs the unprocessed output of a specific macOS source to
diagnose a discrepancy or verify a parsed value.

**Why this priority**: When parsed values look wrong, the raw passthrough is the
escape hatch that makes the tool trustworthy and debuggable.

**Independent Test**: Run `about-this-mac --hardware-info` and confirm it prints
the raw `system_profiler SPHardwareDataType` output.

**Acceptance Scenarios**:

1. **Given** a supported Mac, **When** the user runs any of `--hardware-info`,
   `--power-info`, `--graphics-info`, `--storage-info`, `--memory-info`,
   `--audio-info`, or `--network-info`, **Then** the corresponding raw source
   output is printed and the tool exits without generating the formatted report.
2. **Given** a supported Mac, **When** the user runs `about-this-mac
   --release-date`, **Then** the resolved model release date is printed, or a
   clear error is shown if it cannot be determined.

---

### User Story 5 - Discover capabilities and version (Priority: P3)

A new user or agent inspects what the tool can do and which version is installed.

**Why this priority**: Discoverability supports both human onboarding and agent
capability detection, but it is supporting infrastructure rather than the primary
data-gathering value.

**Independent Test**: Run `about-this-mac --help` and confirm usage, all flags,
and examples are listed; run `about-this-mac --version` and confirm the version
string is printed.

**Acceptance Scenarios**:

1. **Given** any environment, **When** the user runs `--help`, **Then** usage,
   the documented flags, and example invocations are printed and the tool exits
   0.
2. **Given** any environment, **When** the user runs `--version`, **Then** the
   installed version is printed and the tool exits 0.

---

### Edge Cases

- **Non-macOS host**: The tool MUST fail early with a clear message rather than
  emitting a partial or misleading report.
- **Limited permissions**: When a privileged macOS command returns nothing or
  partial data, affected fields MUST degrade to documented unknown/empty values
  with an actionable hint, not an uncaught traceback.
- **No battery present** (e.g. desktop Mac): Battery fields MUST resolve to a
  documented unknown/empty state without erroring the whole report.
- **Unknown or missing values**: Individual fields that cannot be resolved MUST
  render as a consistent "Unknown" marker rather than empty noise or a crash.
- **Conflicting format flags**: `--format`, `--json`, and `--plain` are mutually
  exclusive; supplying conflicting verbosity (`--verbose`/`--quiet`) or color
  (`--color`/`--no-color`) flags together MUST be rejected by the parser.
- **Output to file**: When `--output` targets a file, color MUST be disabled
  regardless of `--color`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST gather hardware facts (model name, device
  identifier, model number, serial number, processor, CPU/performance/efficiency
  core counts, GPU cores, graphics, Bluetooth chipset/firmware/transport, macOS
  version and build, uptime, release date, model size, and model year).
- **FR-002**: The tool MUST gather battery facts (current charge, health
  percentage, full-charge capacity, design capacity, manufacture date, cycle
  count, temperature in Celsius and Fahrenheit, charging power, and low-power-mode
  state).
- **FR-003**: The tool MUST gather memory, storage, graphics, audio, and network
  facts from documented macOS sources.
- **FR-004**: The tool MUST default to a human-readable text report covering all
  sections when run with no arguments.
- **FR-005**: Users MUST be able to select an output format from `text`, `json`,
  `yaml`, `markdown`, `public`, and `simple`, with `--json` and `--plain` as
  shorthands for `json` and `text`.
- **FR-006**: Users MUST be able to restrict the report to a section via
  `--section {hardware, battery, all}` (default `all`).
- **FR-007**: Users MUST be able to write the report to a file via `-o/--output`,
  with `-` meaning stdout.
- **FR-008**: Users MUST be able to view raw source output via `--hardware-info`,
  `--power-info`, `--graphics-info`, `--storage-info`, `--memory-info`,
  `--audio-info`, `--network-info`, and `--release-date`; these short-circuit the
  formatted report.
- **FR-009**: Users MUST be able to control verbosity via `-v/--verbose` and
  `-q/--quiet`, and color via `--color`/`--no-color`.
- **FR-010**: The tool MUST expose `--version` and `--help`.
- **FR-011**: The `public` format MUST exclude the serial number, all unique
  device identifiers (hardware/provisioning UUID, device identifier), and
  network identifiers (Wi-Fi/Bluetooth MAC addresses, hostname) — including
  any such field not surfaced today, should it ever be added. The `simple`,
  `text`, `json`, `yaml`, and `markdown` formats MAY include them.
- **FR-012**: The tool MUST fail early with a clear error when run on a non-macOS
  platform.
- **FR-013**: When a source command fails or lacks permission, the tool MUST
  degrade affected fields to documented unknown/empty values with an actionable
  hint and MUST NOT crash the whole report.
- **FR-014**: Errors MUST be reported with enough context (message and, where
  applicable, a hint) to let a human or agent retry, downgrade, or escalate, and
  MUST exit with a non-zero status. The contract guarantees only that the exit
  status is non-zero on error; no specific code is promised, so automation MUST
  test for non-zero rather than a fixed value.
- **FR-015**: Color MUST be emitted only for TTY text output and MUST be
  suppressed when output is redirected to a file, `--no-color` is set, `NO_COLOR`
  is set, or `TERM=dumb`.

### CLI, Output, and Data Contracts

- **OC-001 (CLI surface)**: The command is `about-this-mac` with flags:
  `--format {text,json,yaml,markdown,public,simple}` (default `text`), `--json`,
  `--plain`, `--section {hardware,battery,all}` (default `all`),
  `-o/--output PATH` (`-` = stdout), `-v/--verbose`, `-q/--quiet`, `--color`,
  `--no-color`, `--version`, `--hardware-info`, `--power-info`,
  `--graphics-info`, `--storage-info`, `--memory-info`, `--audio-info`,
  `--network-info`, `--release-date`. `--format`/`--json`/`--plain` are mutually
  exclusive; `--verbose`/`--quiet` are mutually exclusive; `--color`/`--no-color`
  are mutually exclusive. The report writes to stdout (or the `--output` target);
  errors write to stderr; success exits 0 and errors exit non-zero (a specific
  error code is not part of the contract — see FR-014). `--help` lists all flags
  plus example invocations.
- **OC-002 (Output formats)**: Affected formats are `text`, `json`, `yaml`,
  `markdown`, `public`, and `simple`. `json` MUST parse as JSON; `yaml` MUST
  parse as YAML. `text` is the default human report; `markdown` is a document;
  `public` is a privacy-safe listing; `simple` is a concise owner summary.
- **OC-003 (Source data)**: Facts MUST come from the documented macOS sources:
  `system_profiler` (`SPHardwareDataType`, `SPDisplaysDataType`,
  `SPMemoryDataType`, `SPNVMeDataType`, `SPSerialATADataType`,
  `SPStorageDataType`, `SPPowerDataType`, `SPBluetoothDataType`,
  `SPNetworkDataType`, `SPAudioDataType`, `SPSoftwareDataType`), `sysctl`
  (`hw.memsize`, `hw.model`, `machdep.cpu.brand_string`, `hw.ncpu`,
  `kern.boottime`), `pmset -g batt`, `networksetup -listallhardwareports`,
  `netstat -i`, and Python `platform` APIs. Limited-permission fallback is
  documented unknown/empty values plus a hint (FR-013).
- **OC-004 (Privacy boundary)**: The `public` format MUST exclude three classes
  of sensitive data: (1) the serial number, (2) unique device identifiers
  (hardware/provisioning UUID, device identifier), and (3) network identifiers
  (Wi-Fi/Bluetooth MAC addresses, hostname). This exclusion applies even to
  fields not surfaced in `public` today — if any are later added, they MUST NOT
  appear in `public`. The serial number and unique device identifiers MAY appear
  in `text`, `json`, `yaml`, `markdown`, and `simple`. Any future change to
  where identifiers appear MUST update this contract and the privacy tests.
- **OC-005**: This specification documents existing behavior; it introduces no
  new contract changes beyond recording the current v0.2.2 surface as the
  baseline.

### Key Entities *(include if feature involves data)*

- **HardwareInfo**: The machine's identity and capabilities — model name, device
  identifier, model number, serial number, processor, core counts
  (CPU/performance/efficiency/GPU), graphics, Bluetooth chipset/firmware/
  transport, macOS version and build, uptime, release date, model size, and
  model year.
- **BatteryInfo**: The battery's condition — current charge, health percentage,
  full-charge and design capacity, manufacture date, cycle count, temperature
  (Celsius and Fahrenheit), charging power, and low-power-mode state.
- **MemoryInfo**: RAM configuration — total, type, speed, manufacturer, and ECC
  flag.
- **StorageInfo**: A storage device — name, model, revision, serial, size, type
  (NVMe/SATA), protocol, TRIM, SMART status, and removable/internal flags.
- **Report**: The composed, formatted output of the gathered entities for a
  chosen format and section, plus the privacy variant for public listings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `about-this-mac` with no arguments on a supported Mac
  produces a complete hardware + battery + system report and exits 0.
- **SC-002**: `--format json` output parses as valid JSON and `--format yaml`
  output parses as valid YAML, every time, with no manual cleanup.
- **SC-003**: `--format public` output contains zero occurrences of the device
  serial number, unique device identifiers, or network identifiers (MAC
  addresses, hostname) across all tested machines.
- **SC-004**: Each raw flag (`--hardware-info`, `--power-info`,
  `--graphics-info`, `--storage-info`, `--memory-info`, `--audio-info`,
  `--network-info`) prints the corresponding source output without invoking the
  formatted report path.
- **SC-005**: On a non-macOS host, the tool exits non-zero with a single clear
  message and no traceback.
- **SC-006**: Under restricted permissions or with no battery present, the tool
  still produces a report; unresolved fields render as a consistent "Unknown"
  marker rather than crashing.
- **SC-007**: A user can identify the Mac model, condition (battery health and
  cycle count), and key specs from the default report without consulting any
  other tool.
- **SC-008**: There is no hard runtime gate. End-to-end latency is dominated by
  the underlying macOS source commands (notably `system_profiler`), so the tool
  is held to "completes without hanging" rather than a fixed time budget. A
  regression is a hang or failure to terminate, not exceeding a second count.

## Assumptions

- The target environment is macOS 11 (Big Sur) or later with Python 3.10 or
  later, consistent with the project's stated requirements; non-macOS execution
  is out of scope beyond failing early.
- The documented macOS source commands remain available and their output formats
  remain stable enough to parse; format drift between macOS releases is handled
  by the gatherers and is out of scope for this baseline spec.
- This spec records the v0.2.2 surface as the contract baseline; it does not
  propose new flags, formats, or fields.
- Output is consumed locally; the tool does not transmit data off the device and
  no network credentials or secrets are involved.
- The `public`-format privacy boundary covers three classes of data — serial
  number, unique device identifiers (hardware/provisioning UUID, device
  identifier), and network identifiers (Wi-Fi/Bluetooth MAC addresses, hostname)
  — per the Clarifications session. Some of these are not surfaced in any format
  today; the exclusion is forward-looking so future fields cannot leak into
  `public`.
- Runtime performance is not gated by a fixed time budget (see SC-008); the tool
  inherits the latency of the macOS source commands it calls.
