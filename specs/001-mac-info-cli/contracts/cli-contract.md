# CLI Contract: about-this-mac

**Feature**: 001-mac-info-cli | **Date**: 2026-06-03 | Source of truth: `src/about_this_mac/cli.py`

The command-line interface is the product boundary (Constitution Principle I).
This contract records the shipped v0.2.2 surface as the baseline.

## Command

```text
about-this-mac [options]
```

## Options

| Flag | Values / default | Behavior |
|------|------------------|----------|
| `--format` | `text` (default), `json`, `yaml`, `markdown`, `public`, `simple` | Select output format. |
| `--json` | — | Shorthand for `--format json`. |
| `--plain` | — | Shorthand for `--format text`. |
| `--section` | `hardware`, `battery`, `all` (default) | Restrict report to a section. |
| `-o`, `--output` | PATH (`-` = stdout) | Write report to a file. |
| `-v`, `--verbose` | — | DEBUG-level logging. |
| `-q`, `--quiet` | — | Suppress non-essential output (ERROR level). |
| `--color` | — | Force colored text output. |
| `--no-color` | — | Disable colored output. |
| `--version` | — | Print version, exit 0. |
| `--hardware-info` | — | Raw `system_profiler SPHardwareDataType`. |
| `--power-info` | — | Raw `system_profiler SPPowerDataType`. |
| `--graphics-info` | — | Raw `system_profiler SPDisplaysDataType`. |
| `--storage-info` | — | Raw `SP{NVMe,SerialATA,Storage}DataType`. |
| `--memory-info` | — | Raw `system_profiler SPMemoryDataType`. |
| `--audio-info` | — | Raw `system_profiler SPAudioDataType`. |
| `--network-info` | — | Raw `system_profiler SPNetworkDataType`. |
| `--release-date` | — | Print resolved model release date, or error if unavailable. |

## Mutual exclusivity

- `--format` / `--json` / `--plain` are mutually exclusive.
- `--verbose` / `--quiet` are mutually exclusive.
- `--color` / `--no-color` are mutually exclusive.

Violations are rejected by `argparse` with a usage error and non-zero exit.

## Dispatch precedence (`cli.py:main`)

1. `--release-date` → print and return.
2. Any raw `--*-info` flag (`has_raw_args`) → run raw command(s) and return.
3. Otherwise → generate the formatted report.

## I/O and exit contract

- **stdout**: the report (or the `--output` target file).
- **stderr**: errors and warnings.
- **Exit 0**: success.
- **Exit non-zero**: any error. The contract guarantees only *non-zero*; no
  specific code is promised (spec FR-014). Scripts MUST test `!= 0`, not `== 1`.

## Format guarantees (OC-002)

- `json` output MUST parse as JSON.
- `yaml` output MUST parse as YAML.
- `text` is the default human report (color only on TTY; respects `NO_COLOR`,
  `TERM=dumb`, `--no-color`, and file output — FR-015).
- `markdown` is a document; `public` is a privacy-safe listing; `simple` is a
  concise owner summary.

## Privacy guarantee (OC-004)

`--format public` MUST NOT contain the serial number, unique device identifiers
(hardware/provisioning UUID, device identifier), or network identifiers
(MAC addresses, hostname) — including any such field added in future. All other
formats MAY include serial number and unique device identifiers.

## Platform guarantee

Non-macOS hosts MUST fail early (`SystemError`, surfaced as a non-zero exit)
before any gathering (FR-012).
