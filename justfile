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