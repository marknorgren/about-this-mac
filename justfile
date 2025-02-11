# List available recipes
default:
    @just --list

# Install dependencies
setup:
    pip install -r requirements.txt

# Install in development mode
dev-setup:
    pip install -e ".[dev]"

# Run tests
test:
    pytest

# Run tests with coverage
test-cov:
    pytest --cov=src/about_this_mac --cov-report=term-missing --cov-report=html

# Run tests in watch mode
test-watch:
    pytest-watch

# Format code with black
fmt:
    black src tests

# Run type checking
type-check:
    mypy src tests

# Run linting
lint:
    pylint src tests

# Run all checks (format, type check, lint, test)
check: fmt type-check lint test

# Run basic hardware info (no sudo required)
info:
    python3 src/about_this_mac/cli.py

# Run with full hardware info (requires sudo)
info-full:
    sudo python3 src/about_this_mac/cli.py

# Get simple output like "About This Mac"
simple:
    python3 src/about_this_mac/cli.py --format simple

# Get sales-friendly public output
public:
    python3 src/about_this_mac/cli.py --format public

# Save detailed markdown report
report:
    python3 src/about_this_mac/cli.py --format markdown

# Get raw hardware information
raw-hardware:
    python3 src/about_this_mac/cli.py --hardware-info

# Get raw power/battery information
raw-power:
    python3 src/about_this_mac/cli.py --power-info

# Get raw graphics information
raw-graphics:
    python3 src/about_this_mac/cli.py --graphics-info

# Get raw storage information
raw-storage:
    python3 src/about_this_mac/cli.py --storage-info

# Get raw memory information
raw-memory:
    python3 src/about_this_mac/cli.py --memory-info

# Get raw audio information
raw-audio:
    python3 src/about_this_mac/cli.py --audio-info

# Get raw network information
raw-network:
    python3 src/about_this_mac/cli.py --network-info

# Get all information in JSON format
json:
    python3 src/about_this_mac/cli.py --format json

# Get all information in YAML format
yaml:
    python3 src/about_this_mac/cli.py --format yaml

# Run with verbose logging
verbose:
    python3 src/about_this_mac/cli.py --verbose

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