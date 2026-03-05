# AGENTS

## Private push guardrails (Entire)

This repo uses a private mirror remote to keep Entire/session branch data off public remotes.

- Default push remote is `private` via `remote.pushDefault=private`.
- `core.hooksPath` is set to `.githooks`.
- `.githooks/pre-push` blocks refs matching Entire/session patterns (`refs/heads/entire/*`, `*entire*`, `*shadow*`) unless the remote is `private`.
- The same hook still runs `entire hooks git pre-push` for standard Entire behavior.

### Verify guardrails

```sh
git config --get remote.pushDefault
```

```sh
git config --get core.hooksPath
```

```sh
cat .githooks/pre-push
```

## CI parity checks (required before push/PR)

Run **all** checks CI runs, in this order:

```sh
uv sync --extra dev
just fmt-check
just type-check
just lint
uv run pytest --cov=src/about_this_mac --cov-report=term-missing:skip-covered --cov-report=html tests/
```

### Dogfood (matches CI job)

```sh
uv sync
about-this-mac --format text > reports/report.txt
about-this-mac --format json > reports/report.json
about-this-mac --format yaml > reports/report.yaml
about-this-mac --format markdown --output reports/report.md
about-this-mac --format public > reports/report_public.txt
about-this-mac --format simple > reports/report_simple.txt
about-this-mac --hardware-info > reports/raw_hardware.txt
about-this-mac --power-info > reports/raw_power.txt
about-this-mac --graphics-info > reports/raw_graphics.txt
about-this-mac --storage-info > reports/raw_storage.txt
about-this-mac --memory-info > reports/raw_memory.txt
about-this-mac --audio-info > reports/raw_audio.txt
about-this-mac --network-info > reports/raw_network.txt
```
