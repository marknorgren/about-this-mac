# about-this-mac

A lightweight CLI tool to gather detailed information about your Mac, including hardware, battery, and system details. Ideal for documentation or resale purposes.

## Features

### **Hardware Information**

- **Model** (e.g., MacBook Pro 14-inch, 2023, M2)
- **Device Identifier** (e.g., Mac14,5)
- **Model Number** (e.g., A2779 (LL/A))
- **Processor** (e.g., Apple M2)
- **Memory** (RAM Size)
- **Storage** (Available & Total Disk Space)
- **Graphics** (GPU Information)
- **Audio Devices**
- **Network Interfaces**
- **Bluetooth Status**
- **macOS Version**

### **Battery Information**

- **Battery Charge** (e.g., `4903 mAh`)
- **Battery Health** (e.g., `80.8%`)
- **Full Charge Capacity** (e.g., `4909 mAh`)
- **Design Capacity** (e.g., `6075 mAh`)
- **Manufacture Date** (e.g., `2022-12-26`)
- **Charge Cycles** (e.g., `228`)
- **Battery Temperature** (e.g., `33.1°C`)
- **Charging Power** (e.g., `0.0 Watts`)
- **Low Power Mode** (Enabled/Disabled)

## Data Sources

The script uses various macOS system commands to gather information:

### Hardware Information

- `system_profiler SPHardwareDataType`: Basic hardware info (model, serial, processor)
- `system_profiler SPDisplaysDataType`: Graphics and display information
- `system_profiler SPMemoryDataType`: Memory configuration
- `system_profiler SPNVMeDataType`: NVMe storage details
- `system_profiler SPSerialATADataType`: SATA storage details
- `system_profiler SPStorageDataType`: General storage information
- `sysctl hw.memsize`: Total memory size
- `sysctl hw.model`: Machine model
- `sysctl machdep.cpu.brand_string`: CPU information (Intel Macs)
- `sysctl hw.ncpu`: CPU core count

### Power Information

- `system_profiler SPPowerDataType`: Battery and power information
- `pmset -g batt`: Basic battery status (fallback)

### Network Information

- `system_profiler SPBluetoothDataType`: Bluetooth status
- `networksetup -listallhardwareports`: Network interfaces
- `netstat -i`: Network interfaces (fallback)

### System Information

- `system_profiler SPSoftwareDataType`: macOS version and build
- `system_profiler SPAudioDataType`: Audio devices
- `sysctl kern.boottime`: System uptime
- `platform.mac_ver()`: macOS version (Python API)

## Requirements

- macOS 11.0 (Big Sur) or later
- Python 3.8 or later
- PyYAML package (installed automatically)

## Installation

### Quick Run (No Install)

Run directly without installing using `uvx`:

```sh
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run directly from GitHub
uvx --from git+https://github.com/marknorgren/about-this-mac.git about-this-mac
uvx --from git+https://github.com/marknorgren/about-this-mac.git about-this-mac --format json
```

### Install as CLI Tool

**uv tool** (recommended):
```sh
uv tool install git+https://github.com/marknorgren/about-this-mac.git
about-this-mac
```

**pipx**:
```sh
pipx install git+https://github.com/marknorgren/about-this-mac.git
about-this-mac
```

**pip** (in a venv):
```sh
python -m venv ~/.venvs/about-this-mac
source ~/.venvs/about-this-mac/bin/activate
pip install git+https://github.com/marknorgren/about-this-mac.git
about-this-mac
```

### Development Setup

```sh
git clone https://github.com/marknorgren/about-this-mac.git
cd about-this-mac
uv sync --extra dev
uv run about-this-mac
```

### Installation Methods Compared

| Method | Isolated | Global CLI | Best For |
|--------|----------|------------|----------|
| `uvx` | Yes | No (temp) | One-off runs, trying it out |
| `uv tool install` | Yes | Yes | Daily use, fast installs |
| `pipx install` | Yes | Yes | Daily use, if you don't have uv |
| `pip install` (venv) | Yes | No | Project-specific use |
| `pip install` (system) | No | Yes | Not recommended |

**Key differences:**

- **uvx**: Downloads and runs in a temporary environment. Nothing persists after the command finishes. Ideal for quick one-off usage.
- **uv tool install**: Installs in an isolated environment (~/.local/share/uv/tools/) but adds the CLI to your PATH. Fast, clean, recommended.
- **pipx install**: Same isolation concept as uv tool, but slower. Use if you prefer pipx or don't have uv.
- **pip install (venv)**: Installs into a specific virtual environment. You must activate the venv to use the CLI.
- **pip install (system)**: Installs into your system Python. Can cause conflicts with other packages. Avoid.

### Updating

**uv tool**:
```sh
uv tool upgrade about-this-mac
```

**pipx**:
```sh
pipx upgrade about-this-mac
```

**pip** (in venv):
```sh
pip install --upgrade git+https://github.com/marknorgren/about-this-mac.git
```

**uvx**: No update needed - always fetches the latest version.

## Usage

### Quick Start

If you've cloned the repository, you can use `just` commands for common operations. To see available commands:

```sh
just
```

Or run directly with uv:

```sh
uv sync --extra dev
uv run about-this-mac
```

### Command Line Options

You can run the tool with various options:

```sh
# Basic usage (after installation from GitHub)
about-this-mac

# With specific format
about-this-mac --format [text|json|yaml|markdown|public|simple]
about-this-mac --json     # shorthand for --format json
about-this-mac --plain    # shorthand for --format text

# Show specific section
about-this-mac --section [hardware|battery|all]

# Save to file
about-this-mac --output report.md
about-this-mac -o -       # write to stdout explicitly

# Show verbose output
about-this-mac --verbose
about-this-mac --quiet

# Show raw information
about-this-mac --hardware-info  # Raw hardware info
about-this-mac --power-info     # Raw power info
about-this-mac --graphics-info  # Raw graphics info
about-this-mac --storage-info   # Raw storage info
about-this-mac --memory-info    # Raw memory info
about-this-mac --audio-info     # Raw audio info
about-this-mac --network-info   # Raw network info

# Color controls (text output only)
about-this-mac --color
about-this-mac --no-color
```

### Permission Levels

The script provides different levels of information based on permissions:

#### Without sudo (Basic Information)

- Basic hardware model
- Memory size
- Storage information
- Network interfaces
- Basic battery status (if available)
- macOS version

#### With sudo (Full Information):

- Detailed hardware specifications
- Complete battery health and status
- Graphics card details
- Detailed audio device information
- Full system profiler data

### Output Formats

1. **Text** (default): Detailed information in a readable format
2. **Simple**: Basic information similar to About This Mac
3. **Public**: Sales-friendly format for listings
4. **JSON**: Structured data in JSON format
5. **YAML**: Structured data in YAML format
6. **Markdown**: Formatted report with sections and details

Color is applied only to text output, only when writing to a TTY. It respects
`NO_COLOR` and `TERM=dumb`, and is disabled automatically when writing to a file.

## Project Structure

```
src/about_this_mac/
├── __init__.py          # Public API exports
├── __main__.py          # Entry point
├── cli.py               # Argument parsing and dispatch
├── output.py            # Output handler (text/JSON) and CliError
├── commands/
│   ├── __init__.py
│   ├── raw.py           # Raw data commands (--hardware-info, etc.)
│   └── report.py        # Main report generation
├── battery/
│   ├── __init__.py
│   └── battery_info.py  # Battery data gathering
├── hardware/
│   ├── __init__.py
│   └── hardware_info.py # Hardware data gathering
└── utils/
    ├── __init__.py
    ├── command.py       # Command execution wrapper
    ├── formatting.py    # Output formatters (JSON, YAML, Markdown, text)
    └── system.py        # Platform checks and parsing
```

## Error Handling

If you encounter any issues:

1. For basic information, run without sudo
2. For complete information, run with sudo
3. Run with `--verbose` flag for detailed error information
4. Check system logs for any hardware access issues
5. Verify Python version compatibility

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using conventional commits
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
