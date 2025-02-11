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

### From GitHub (Development)

Clone the repository and install in development mode:

```sh
git clone https://github.com/user/about-this-mac.git
cd about-this-mac
just setup  # Install dependencies
just dev-setup  # Install in development mode
```

### From GitHub (Direct Use)

You can install directly from GitHub:

```sh
python3 -m pip install git+https://github.com/user/about-this-mac.git
```

After installation, you can run the tool using the `about-this-mac` command:

```sh
about-this-mac
```

## Usage

### Quick Start

If you've cloned the repository, you can use `just` commands for common operations. To see available commands:

```sh
just
```

### Command Line Options

You can run the tool with various options:

```sh
# Basic usage (after installation from GitHub)
about-this-mac

# With specific format
about-this-mac --format [text|json|yaml|markdown|public|simple]

# Show specific section
about-this-mac --section [hardware|battery|all]

# Save to file
about-this-mac --output report.md

# Show verbose output
about-this-mac --verbose

# Show raw information
about-this-mac --hardware-info  # Raw hardware info
about-this-mac --power-info     # Raw power info
about-this-mac --graphics-info  # Raw graphics info
about-this-mac --storage-info   # Raw storage info
about-this-mac --memory-info    # Raw memory info
about-this-mac --audio-info     # Raw audio info
about-this-mac --network-info   # Raw network info
```

### Permission Levels

The script provides different levels of information based on permissions:

#### Without sudo (Basic Information):

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
