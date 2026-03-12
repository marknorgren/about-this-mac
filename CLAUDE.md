# CLAUDE

## Cloud agent environment

This repo provides a **devcontainer** (`.devcontainer/`) with **uv** and **just** preinstalled and on PATH. Use it in Cursor, GitHub Codespaces, or any devcontainer host so CI-parity commands work without bootstrapping.

If you're not in the devcontainer and `uv` or `just` are missing, bootstrap once (same as CI):

```sh
# uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"   # or add to your shell profile

# just (macOS with Homebrew)
brew install just
# Linux (script)
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
```

Then run the CI-parity checks below.

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
