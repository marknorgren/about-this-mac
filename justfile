# List available recipes
default:
    @just --list

# Install dependencies
setup:
    uv pip install -r requirements.txt

# Install in development mode
dev-setup:
    uv pip install -e ".[dev]"

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src/about_this_mac --cov-report=term-missing --cov-report=html

# Run tests in watch mode
test-watch:
    uv run pytest-watch

# Format code with black
fmt:
    uv run black src tests

# Check if code is formatted without modifying
fmt-check:
    uv run black --check src tests

# Run type checking
type-check:
    uv run mypy src tests

# Run linting
lint:
    uv run pylint src tests

# Run all checks (format check, type check, lint, test)
check: fmt-check type-check lint test

# Run basic hardware info (no sudo required)
info:
    uv run python src/about_this_mac/cli.py

# Run with full hardware info (requires sudo)
info-full:
    sudo uv run python src/about_this_mac/cli.py

# Get simple output like "About This Mac"
simple:
    uv run python src/about_this_mac/cli.py --format simple

# Get sales-friendly public output
public:
    uv run python src/about_this_mac/cli.py --format public

# Save detailed markdown report
report:
    uv run python src/about_this_mac/cli.py --format markdown

# Get raw hardware information
raw-hardware:
    uv run python src/about_this_mac/cli.py --hardware-info

# Get raw power/battery information
raw-power:
    uv run python src/about_this_mac/cli.py --power-info

# Get raw graphics information
raw-graphics:
    uv run python src/about_this_mac/cli.py --graphics-info

# Get raw storage information
raw-storage:
    uv run python src/about_this_mac/cli.py --storage-info

# Get raw memory information
raw-memory:
    uv run python src/about_this_mac/cli.py --memory-info

# Get raw audio information
raw-audio:
    uv run python src/about_this_mac/cli.py --audio-info

# Get raw network information
raw-network:
    uv run python src/about_this_mac/cli.py --network-info

# Get raw release date information
raw-release-date:
    uv run python src/about_this_mac/cli.py --release-date

# Get all information in JSON format
json:
    uv run python src/about_this_mac/cli.py --format json

# Get all information in YAML format
yaml:
    uv run python src/about_this_mac/cli.py --format yaml

# Run with verbose logging
verbose:
    uv run python src/about_this_mac/cli.py --verbose

# Bump version, update CHANGELOG.md, commit, tag, and push
release:
    uv run semantic-release version
    git push --follow-tags

# Dry run: print what the next version would be without making changes
release-dry-run:
    uv run semantic-release version --print

# ------- Go port -------

# Build the Go binary into go/bin/about-this-mac
go-build:
    cd go && go build -o bin/about-this-mac ./cmd/about-this-mac

# Run Go tests
go-test:
    cd go && go test ./...

# Run the Go binary (pass args after --, e.g. `just go-run -- --format simple`)
go-run *args:
    cd go && go run ./cmd/about-this-mac {{args}}

# Build a universal-binary Go release (arm64 + amd64 → lipo)
go-release:
    cd go && \
      GOOS=darwin GOARCH=arm64 go build -o bin/about-this-mac-arm64 ./cmd/about-this-mac && \
      GOOS=darwin GOARCH=amd64 go build -o bin/about-this-mac-amd64 ./cmd/about-this-mac && \
      lipo -create -output bin/about-this-mac bin/about-this-mac-arm64 bin/about-this-mac-amd64 && \
      rm bin/about-this-mac-arm64 bin/about-this-mac-amd64

# ------- Rust port -------

# Build the Rust binary (debug)
rust-build:
    cd rust && cargo build

# Run Rust tests
rust-test:
    cd rust && cargo test

# Run the Rust binary (pass args after --, e.g. `just rust-run -- --format simple`)
rust-run *args:
    cd rust && cargo run -- {{args}}

# Build a universal-binary Rust release (arm64 + x86_64 → lipo)
rust-release:
    cd rust && \
      cargo build --release --target aarch64-apple-darwin && \
      cargo build --release --target x86_64-apple-darwin && \
      lipo -create \
        -output target/about-this-mac \
        target/aarch64-apple-darwin/release/about-this-mac \
        target/x86_64-apple-darwin/release/about-this-mac

# ------- Fixtures + parity -------

# Capture every system_profiler/sysctl/ioreg output + Python golden outputs.
# Run on a real Mac. Defaults to tests/fixtures/local/ (gitignored).
capture-fixtures dir="tests/fixtures/local":
    ./scripts/capture-fixtures.sh {{dir}}

# Run both ports against the same fixture dir and diff against Python golden
# output. Requires `just capture-fixtures` to have run first.
parity dir="tests/fixtures/local":
    cd go && go run ./cmd/about-this-mac --fixture-dir ../{{dir}}/cmd --format simple > /tmp/atm-go-simple.txt
    cd rust && cargo run --quiet -- --fixture-dir ../{{dir}}/cmd --format simple > /tmp/atm-rust-simple.txt
    diff -u {{dir}}/golden/report.simple.txt /tmp/atm-go-simple.txt && echo "Go: simple OK"
    diff -u {{dir}}/golden/report.simple.txt /tmp/atm-rust-simple.txt && echo "Rust: simple OK"

# ------- Cleanup -------

# Clean generated files
clean:
    rm -f mac-info-*.md
    rm -f mac-info-*.json
    rm -f mac-info-*.yaml
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov
    rm -rf dist
    rm -rf build
    rm -rf *.egg-info
    find . -type d -name "__pycache__" -exec rm -r {} + 