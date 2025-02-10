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

No installation required. Run directly from GitHub:

```sh
curl -sSL https://raw.githubusercontent.com/user/repo/main/about-this-mac.py | python3
```

Or clone and run locally:

```sh
git clone https://github.com/user/about-this-mac.git
cd about-this-mac
pip install -r requirements.txt
```

## Usage

### Basic Usage

The script can run in two modes:

1. **Standard Mode** - Basic information without administrator privileges:

```sh
python3 about-this-mac.py
```

2. **Full Information Mode** - Complete system information with administrator privileges:

```sh
sudo python3 about-this-mac.py
```

### Raw Data Mode

View raw output from specific data sources:

```sh
# View raw hardware information
python3 about-this-mac.py --hardware-info

# View raw battery information
python3 about-this-mac.py --power-info

# View raw graphics information
python3 about-this-mac.py --graphics-info

# View raw storage information
python3 about-this-mac.py --storage-info

# View raw memory information
python3 about-this-mac.py --memory-info

# View raw audio information
python3 about-this-mac.py --audio-info

# View raw network information
python3 about-this-mac.py --network-info
```

### Output Formats

```sh
# Output as JSON
python3 about-this-mac.py --format json

# Output as YAML
python3 about-this-mac.py --format yaml

# Output specific sections
python3 about-this-mac.py --section battery
python3 about-this-mac.py --section hardware
```

### Options

- `--format`: Output format (text, json, yaml)
- `--section`: Specific section to display (hardware, battery, all)
- `--output`: Save output to file
- `--verbose`: Show detailed debug information
- `--hardware-info`: Show raw hardware information
- `--power-info`: Show raw power information
- `--graphics-info`: Show raw graphics information
- `--storage-info`: Show raw storage information
- `--memory-info`: Show raw memory information
- `--audio-info`: Show raw audio information
- `--network-info`: Show raw network information

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
