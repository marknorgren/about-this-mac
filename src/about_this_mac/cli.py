#!/usr/bin/env python3

"""Command-line interface for about-this-mac."""

import argparse
import json
import logging
import os
import platform
import subprocess
import sys
import time
import yaml
from dataclasses import asdict
from datetime import datetime
from typing import Dict, Optional, Any

from about_this_mac import (
    BatteryInfo,
    BatteryInfoGatherer,
    MacInfoGatherer,
    HardwareInfo,
    MemoryInfo,
    StorageInfo,
)
from about_this_mac import __version__

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def format_output(
    data: Dict[str, Any], format_type: str, gatherer: Optional[MacInfoGatherer] = None
) -> str:
    """Format the output according to the specified format."""
    if format_type == "simple":
        if not gatherer:
            gatherer = MacInfoGatherer()
        return gatherer.format_simple_output(data)
    elif format_type == "public":
        if not gatherer:
            gatherer = MacInfoGatherer()
        return gatherer.format_public_output(data)
    elif format_type == "json":
        return json.dumps(data, indent=2)
    elif format_type == "yaml":
        return yaml.dump(data, sort_keys=False)
    elif format_type == "markdown":
        output = []

        # Add title and timestamp
        output.extend(
            [
                "# Mac System Information",
                "",
                f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                "",
            ]
        )

        # Hardware section
        if "hardware" in data:
            hw = data["hardware"]
            output.extend(
                [
                    "## Hardware Information",
                    "",
                    "### System",
                    f"- **Model:** {hw['model_name']}",
                    f"- **Identifier:** {hw['device_identifier']}",
                    f"- **Model Number:** {hw['model_number']}",
                    f"- **Serial Number:** {hw['serial_number']}",
                    "",
                    "### Processor",
                    f"- **Chip:** {hw['processor']}",
                    f"- **CPU Cores:** {hw['cpu_cores']} ({hw['performance_cores']} performance and {hw['efficiency_cores']} efficiency)",
                    f"- **GPU Cores:** {hw['gpu_cores']}",
                    "",
                    "### Memory",
                    f"- **Total:** {hw['memory']['total']}",
                    f"- **Type:** {hw['memory']['type']}",
                    f"- **Speed:** {hw['memory']['speed']}",
                    f"- **Manufacturer:** {hw['memory']['manufacturer']}",
                    f"- **ECC:** {'Yes' if hw['memory']['ecc'] else 'No'}",
                    "",
                    "### Storage",
                    f"- **Model:** {hw['storage']['model']}",
                    f"- **Type:** {hw['storage']['type']}",
                    f"- **Protocol:** {hw['storage']['protocol']}",
                    f"- **Size:** {hw['storage']['size']}",
                    f"- **SMART Status:** {hw['storage']['smart_status']}",
                    f"- **TRIM Support:** {'Yes' if hw['storage']['trim'] else 'No'}",
                    f"- **Internal:** {'Yes' if hw['storage']['internal'] else 'No'}",
                    "",
                    "### Graphics",
                ]
            )

            # Add graphics cards
            if hw["graphics"]:
                for i, card in enumerate(hw["graphics"], 1):
                    output.append(f"#### Card {i}")
                    if card["name"]:
                        output.append(f"- **Model:** {card['name']}")
                    if card["vendor"]:
                        output.append(f"- **Vendor:** {card['vendor']}")
                    if card["vram"]:
                        output.append(f"- **VRAM:** {card['vram']}")
                    if card["resolution"]:
                        output.append(f"- **Resolution:** {card['resolution']}")
                    if card["metal"]:
                        output.append(f"- **Metal Support:** {card['metal']}")
                    output.append("")  # Add newline after each card
            else:
                output.append("*No graphics cards detected*\n")

            output.extend(
                [
                    "### Wireless",
                    f"- **Bluetooth:** {hw['bluetooth_chipset']} ({hw['bluetooth_firmware']}) via {hw['bluetooth_transport']}",
                    "",
                    "### System Software",
                    f"- **macOS Version:** {hw['macos_version']}",
                    f"- **Build:** {hw['macos_build']}",
                    f"- **Uptime:** {hw['uptime']}",
                ]
            )

        # Battery section if available
        if "battery" in data:
            bat = data["battery"]
            output.extend(
                [
                    "",
                    "## Battery Information",
                    "",
                    f"- **Current Charge:** {bat['current_charge']}",
                    f"- **Health:** {bat['health_percentage']:.1f}%",
                    f"- **Full Charge Capacity:** {bat['full_charge_capacity']}",
                    f"- **Design Capacity:** {bat['design_capacity']}",
                    f"- **Manufacture Date:** {bat['manufacture_date']}",
                    f"- **Cycle Count:** {bat['cycle_count']}",
                    f"- **Temperature:** {bat['temperature_celsius']:.1f}°C / {bat['temperature_fahrenheit']:.1f}°F",
                    f"- **Charging Power:** {bat['charging_power']:.1f} Watts",
                    f"- **Low Power Mode:** {'Enabled' if bat['low_power_mode'] else 'Disabled'}",
                ]
            )

        return "\n".join(output)
    else:  # text format
        output = []

        # Hardware section first
        if "hardware" in data:
            hw = data["hardware"]
            output.extend(
                [
                    "\nHARDWARE INFORMATION",
                    "===================",
                    f"Model: {hw['model_name']}",
                    f"Identifier: {hw['device_identifier']}",
                    f"Model Number: {hw['model_number']}",
                    f"Serial Number: {hw['serial_number']}",
                    "",
                    "Processor",
                    "---------",
                    hw["processor"],
                    f"CPU Cores: {hw['cpu_cores']} ({hw['performance_cores']} performance and {hw['efficiency_cores']} efficiency)",
                    f"GPU Cores: {hw['gpu_cores']}",
                    "",
                    "Memory",
                    "------",
                    f"Total: {hw['memory']['total']}",
                    f"Type: {hw['memory']['type']}",
                    f"Speed: {hw['memory']['speed']}",
                    f"Manufacturer: {hw['memory']['manufacturer']}",
                    f"ECC: {'Yes' if hw['memory']['ecc'] else 'No'}",
                    "",
                    "Storage",
                    "-------",
                    f"Model: {hw['storage']['model']}",
                    f"Type: {hw['storage']['type']}",
                    f"Protocol: {hw['storage']['protocol']}",
                    f"Size: {hw['storage']['size']}",
                    f"SMART Status: {hw['storage']['smart_status']}",
                    f"TRIM Support: {'Yes' if hw['storage']['trim'] else 'No'}",
                    f"Internal: {'Yes' if hw['storage']['internal'] else 'No'}",
                    "",
                    "Graphics",
                    "--------",
                ]
            )

            # Add graphics cards
            if hw["graphics"]:
                for i, card in enumerate(hw["graphics"], 1):
                    card_info = [f"Card {i}:"]
                    if card["name"]:
                        card_info.append(f"  Model: {card['name']}")
                    if card["vendor"]:
                        card_info.append(f"  Vendor: {card['vendor']}")
                    if card["vram"]:
                        card_info.append(f"  VRAM: {card['vram']}")
                    if card["resolution"]:
                        card_info.append(f"  Resolution: {card['resolution']}")
                    if card["metal"]:
                        card_info.append(f"  Metal Support: {card['metal']}")
                    output.extend(card_info)
            else:
                output.append("No graphics cards detected")

            output.extend(
                [
                    "",
                    "Wireless",
                    "--------",
                    f"Bluetooth: {hw['bluetooth_chipset']} ({hw['bluetooth_firmware']}) via {hw['bluetooth_transport']}",
                    "",
                    "System",
                    "------",
                    f"macOS Version: {hw['macos_version']}",
                    f"Build: {hw['macos_build']}",
                    f"Uptime: {hw['uptime']}",
                ]
            )

        # Battery section if available
        if "battery" in data:
            bat = data["battery"]
            output.extend(
                [
                    "\nBATTERY INFORMATION",
                    "==================",
                    f"Current Charge: {bat['current_charge']}",
                    f"Health: {bat['health_percentage']:.1f}%",
                    f"Full Charge Capacity: {bat['full_charge_capacity']}",
                    f"Design Capacity: {bat['design_capacity']}",
                    f"Manufacture Date: {bat['manufacture_date']}",
                    f"Cycle Count: {bat['cycle_count']}",
                    f"Temperature: {bat['temperature_celsius']:.1f}°C / {bat['temperature_fahrenheit']:.1f}°F",
                    f"Charging Power: {bat['charging_power']:.1f} Watts",
                    f"Low Power Mode: {'Enabled' if bat['low_power_mode'] else 'Disabled'}",
                ]
            )

        return "\n".join(output)


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Gather detailed information about your Mac.")
    parser.add_argument(
        "--format",
        choices=["text", "json", "yaml", "markdown", "public", "simple"],
        default="text",
        help='Output format (use "public" for sales-friendly output)',
    )
    parser.add_argument(
        "--section",
        choices=["hardware", "battery", "all"],
        default="all",
        help="Information section to display",
    )
    parser.add_argument(
        "--output", help="Save output to file (default: auto-generate filename for markdown)"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed debug information")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Add raw data mode arguments
    parser.add_argument(
        "--hardware-info",
        action="store_true",
        help="Show raw hardware information from system_profiler SPHardwareDataType",
    )
    parser.add_argument(
        "--power-info",
        action="store_true",
        help="Show raw power information from system_profiler SPPowerDataType",
    )
    parser.add_argument(
        "--graphics-info",
        action="store_true",
        help="Show raw graphics information from system_profiler SPDisplaysDataType",
    )
    parser.add_argument(
        "--storage-info",
        action="store_true",
        help="Show raw storage information from system_profiler SP{NVMe,SerialATA,Storage}DataType",
    )
    parser.add_argument(
        "--memory-info",
        action="store_true",
        help="Show raw memory information from system_profiler SPMemoryDataType",
    )
    parser.add_argument(
        "--audio-info",
        action="store_true",
        help="Show raw audio information from system_profiler SPAudioDataType",
    )
    parser.add_argument(
        "--network-info",
        action="store_true",
        help="Show raw network information from system_profiler SPNetworkDataType",
    )

    args = parser.parse_args()

    try:
        gatherer = MacInfoGatherer(verbose=args.verbose)

        # Handle raw data mode requests
        if any(
            [
                args.hardware_info,
                args.power_info,
                args.graphics_info,
                args.storage_info,
                args.memory_info,
                args.audio_info,
                args.network_info,
            ]
        ):
            raw_data = []

            if args.hardware_info:
                raw_data.extend(
                    [
                        "\nHardware Information (system_profiler SPHardwareDataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPHardwareDataType"]),
                        "\nCPU Information (sysctl):",
                        "=" * 60,
                        f"hw.model: {gatherer._get_sysctl_value('hw.model')}",
                        f"hw.ncpu: {gatherer._get_sysctl_value('hw.ncpu')}",
                        f"machdep.cpu.brand_string: {gatherer._get_sysctl_value('machdep.cpu.brand_string')}",
                    ]
                )

            if args.power_info:
                raw_data.extend(
                    [
                        "\nPower Information (system_profiler SPPowerDataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPPowerDataType"]),
                        "\nBattery Status (pmset):",
                        "=" * 60,
                        gatherer._run_command(["pmset", "-g", "batt"], privileged=False),
                    ]
                )

            if args.graphics_info:
                raw_data.extend(
                    [
                        "\nGraphics Information (system_profiler SPDisplaysDataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPDisplaysDataType"]),
                    ]
                )

            if args.storage_info:
                raw_data.extend(
                    [
                        "\nNVMe Storage Information (system_profiler SPNVMeDataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPNVMeDataType"]),
                        "\nSATA Storage Information (system_profiler SPSerialATADataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPSerialATADataType"]),
                        "\nGeneral Storage Information (system_profiler SPStorageDataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPStorageDataType"]),
                    ]
                )

            if args.memory_info:
                raw_data.extend(
                    [
                        "\nMemory Information (system_profiler SPMemoryDataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPMemoryDataType"]),
                        "\nMemory Size (sysctl):",
                        "=" * 60,
                        f"hw.memsize: {gatherer._get_sysctl_value('hw.memsize')}",
                    ]
                )

            if args.audio_info:
                raw_data.extend(
                    [
                        "\nAudio Information (system_profiler SPAudioDataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPAudioDataType"]),
                    ]
                )

            if args.network_info:
                raw_data.extend(
                    [
                        "\nNetwork Interfaces (networksetup):",
                        "=" * 60,
                        gatherer._run_command(
                            ["networksetup", "-listallhardwareports"], privileged=False
                        ),
                        "\nNetwork Status (netstat):",
                        "=" * 60,
                        gatherer._run_command(["netstat", "-i"], privileged=False),
                        "\nBluetooth Information (system_profiler SPBluetoothDataType):",
                        "=" * 60,
                        gatherer._run_command(["system_profiler", "SPBluetoothDataType"]),
                    ]
                )

            print("\n".join(raw_data))
            return

        # Gather information based on requested section
        data = {}
        if args.section in ["hardware", "all"]:
            data["hardware"] = asdict(gatherer.get_hardware_info())
        if args.section in ["battery", "all"]:
            battery_info = gatherer.get_battery_info()
            if battery_info:
                data["battery"] = asdict(battery_info)

        # Format the output
        output = format_output(data, args.format, gatherer)

        # Handle output
        if args.output or args.format == "markdown":
            output_file = args.output
            if not output_file and args.format == "markdown":
                # Generate default filename for markdown
                model_name = data["hardware"]["model_name"].replace(" ", "-").lower()
                date_str = datetime.now().strftime("%Y-%m-%d")
                output_file = f"mac-info-{model_name}-{date_str}.md"

            with open(output_file, "w") as f:
                f.write(output)
            print(f"Output saved to {output_file}")
        else:
            print(output)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
