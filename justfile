# List available recipes
default:
    @just --list

# Install dependencies
setup:
    pip install -r requirements.txt

# Run basic hardware info (no sudo required)
info:
    python3 about-this-mac.py

# Run with full hardware info (requires sudo)
info-full:
    sudo python3 about-this-mac.py

# Get simple output like "About This Mac"
simple:
    python3 about-this-mac.py --format simple

# Get sales-friendly public output
public:
    python3 about-this-mac.py --format public

# Save detailed markdown report
report:
    python3 about-this-mac.py --format markdown

# Get raw hardware information
raw-hardware:
    python3 about-this-mac.py --hardware-info

# Get raw power/battery information
raw-power:
    python3 about-this-mac.py --power-info

# Get raw graphics information
raw-graphics:
    python3 about-this-mac.py --graphics-info

# Get raw storage information
raw-storage:
    python3 about-this-mac.py --storage-info

# Get raw memory information
raw-memory:
    python3 about-this-mac.py --memory-info

# Get raw audio information
raw-audio:
    python3 about-this-mac.py --audio-info

# Get raw network information
raw-network:
    python3 about-this-mac.py --network-info

# Get all information in JSON format
json:
    python3 about-this-mac.py --format json

# Get all information in YAML format
yaml:
    python3 about-this-mac.py --format yaml

# Run with verbose logging
verbose:
    python3 about-this-mac.py --verbose

# Run tests (placeholder for future test implementation)
test:
    echo "No tests implemented yet"

# Format code with black
fmt:
    black about-this-mac.py

# Run linting
lint:
    pylint about-this-mac.py

# Clean generated files
clean:
    rm -f mac-info-*.md
    rm -f mac-info-*.json
    rm -f mac-info-*.yaml
    find . -type d -name "__pycache__" -exec rm -r {} + 