# Quickstart & Verification: about-this-mac Information CLI

**Feature**: 001-mac-info-cli | **Date**: 2026-06-03

One-command verification per spec story, plus the CI-parity gate. Run from repo
root on macOS. Reports are for local verification only — never commit real
machine output (public repo; `reports/` is gitignored).

## Setup

```sh
uv sync --extra dev
```

## CI-parity gate (required before push/PR)

```sh
just fmt-check
just type-check
just lint
uv run pytest --cov=src/about_this_mac --cov-report=term-missing:skip-covered tests/
```

**Evidence required**: all four commands exit 0; coverage report printed.

## Per-story verification

| Story | Command | Expected |
|-------|---------|----------|
| US1 default report | `about-this-mac` | Human text report; exit 0 |
| US1 section filter | `about-this-mac --section hardware` | Hardware only |
| US2 JSON | `about-this-mac --format json \| python -m json.tool` | Parses as JSON |
| US2 YAML | `about-this-mac --format yaml \| python -c 'import sys,yaml;yaml.safe_load(sys.stdin)'` | Parses as YAML |
| US2 file output | `about-this-mac --json -o /tmp/r.json` | File written |
| US3 public privacy | `about-this-mac --format public` | No serial / device ID / MAC / hostname present |
| US3 simple | `about-this-mac --format simple` | Concise summary incl. serial |
| US4 raw | `about-this-mac --hardware-info` | Raw SPHardwareDataType output |
| US5 help | `about-this-mac --help` | Usage + all flags + examples |
| US5 version | `about-this-mac --version` | Version string; exit 0 |

## Edge-case verification

| Edge case | How to verify | Expected |
|-----------|---------------|----------|
| Non-macOS | Unit test monkeypatches `platform.system` → `"Linux"` | Non-zero exit, single clear error |
| Conflicting formats | `about-this-mac --json --plain` | argparse usage error, non-zero exit |
| Output to file disables color | `about-this-mac --color -o /tmp/r.txt` | No ANSI codes in file |
| NO_COLOR honored | `NO_COLOR=1 about-this-mac` | No ANSI codes |

## Privacy spot-check (manual)

```sh
SERIAL=$(about-this-mac --format simple | grep -i "serial" | awk '{print $NF}')
about-this-mac --format public | grep -q "$SERIAL" && echo "LEAK" || echo "OK"
```

**Expected**: `OK` (serial absent from public output).

## Allowed side effects

- Reads from macOS system commands (`system_profiler`, `sysctl`, `pmset`,
  `networksetup`, `netstat`) and Python platform APIs.
- Writes only to stdout or the explicit `--output` path. No network, no
  persistent state, no credentials.

## Stop / escalation conditions

- Any CI-parity command fails → fix before push; do not proceed.
- Privacy spot-check prints `LEAK` → stop; the public-format allowlist has
  regressed (treat as a release blocker, Constitution Principle II).
- A gatherer raises an uncaught traceback under limited permissions → bug;
  it MUST degrade to unknown/empty + hint (FR-013).
