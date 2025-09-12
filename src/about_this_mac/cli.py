#!/usr/bin/env python3

"""Command-line interface for about-this-mac."""

import argparse
import json
import logging
import sys
from dataclasses import asdict
from typing import Dict, Optional, Any

from about_this_mac import MacInfoGatherer
from about_this_mac import __version__
from about_this_mac.utils.formatting import (
    format_output_as_json,
    format_output_as_yaml,
    format_output_as_markdown,
)

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
    if format_type == "public":
        if not gatherer:
            gatherer = MacInfoGatherer()
        return gatherer.format_public_output(data)
    if format_type == "json":
        return format_output_as_json(data)
    if format_type == "yaml":
        return format_output_as_yaml(data)
    if format_type == "markdown":
        return format_output_as_markdown(data)
    # default: text
    # Build a plain-text block similar to markdown but without markup
    # Delegate to markdown and strip simple markers if desired; for now, reuse markdown then convert basic headings
    md = format_output_as_markdown(data)
    lines = []
    for line in md.splitlines():
        if line.startswith("# "):
            continue  # drop big title
        if line.startswith("## "):
            lines.extend(["", line[3:].upper(), "=" * len(line[3:])])
            continue
        if line.startswith("### "):
            title = line[4:]
            lines.extend([title, "-" * len(title)])
            continue
        if line.startswith("#### "):
            lines.append(line[5:] + ":")
            continue
        # Convert markdown list items
        if line.startswith("- **") and ":** " in line:
            # e.g., - **Model:** Value -> Model: Value
            try:
                key, val = line[3:].split("**:", 1)
                key = key.strip("* ")
                lines.append(f"{key}: {val.strip()}")
                continue
            except ValueError:
                pass
        if line.startswith("- "):
            lines.append(line[2:])
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


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
    parser.add_argument("--output", help="Save output to file")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed debug information",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

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
    parser.add_argument(
        "--release-date",
        action="store_true",
        help="Show raw release date information",
    )

    args = parser.parse_args()

    try:
        gatherer = MacInfoGatherer(verbose=args.verbose)

        if args.release_date:
            release_date = gatherer.get_release_date()
            if release_date:
                print(f"Release Date: {release_date}")
            else:
                print("Release date information not available")
            return

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
                        gatherer.run_command(["system_profiler", "SPHardwareDataType"], privileged=True),
                        "\nCPU Information (sysctl):",
                        "=" * 60,
                        f"hw.model: {gatherer.get_sysctl_value('hw.model')}",
                        f"hw.ncpu: {gatherer.get_sysctl_value('hw.ncpu')}",
                        "machdep.cpu.brand_string: "
                        f"{gatherer.get_sysctl_value('machdep.cpu.brand_string')}",
                    ]
                )

            if args.power_info:
                raw_data.extend(
                    [
                        "\nPower Information (system_profiler SPPowerDataType):",
                        "=" * 60,
                        gatherer.run_command(["system_profiler", "SPPowerDataType"], privileged=True),
                        "\nBattery Status (pmset):",
                        "=" * 60,
                        gatherer.run_command(["pmset", "-g", "batt"], privileged=False),
                    ]
                )

            if args.graphics_info:
                raw_data.extend(
                    [
                        "\nGraphics Information (system_profiler SPDisplaysDataType):",
                        "=" * 60,
                        gatherer.run_command(["system_profiler", "SPDisplaysDataType"], privileged=True),
                    ]
                )

            if args.storage_info:
                raw_data.extend(
                    [
                        "\nNVMe Storage Information (system_profiler SPNVMeDataType):",
                        "=" * 60,
                        gatherer.run_command(["system_profiler", "SPNVMeDataType"], privileged=True),
                        "\nSATA Storage Information (system_profiler SPSerialATADataType):",
                        "=" * 60,
                        gatherer.run_command(["system_profiler", "SPSerialATADataType"], privileged=True),
                        "\nGeneral Storage Information (system_profiler SPStorageDataType):",
                        "=" * 60,
                        gatherer.run_command(["system_profiler", "SPStorageDataType"], privileged=True),
                    ]
                )

            if args.memory_info:
                raw_data.extend(
                    [
                        "\nMemory Information (system_profiler SPMemoryDataType):",
                        "=" * 60,
                        gatherer.run_command(["system_profiler", "SPMemoryDataType"], privileged=True),
                        "\nMemory Size (sysctl):",
                        "=" * 60,
                        f"hw.memsize: {gatherer.get_sysctl_value('hw.memsize')}",
                    ]
                )

            if args.audio_info:
                raw_data.extend(
                    [
                        "\nAudio Information (system_profiler SPAudioDataType):",
                        "=" * 60,
                        gatherer.run_command(["system_profiler", "SPAudioDataType"], privileged=True),
                    ]
                )

            if args.network_info:
                raw_data.extend(
                    [
                        "\nNetwork Interfaces (networksetup):",
                        "=" * 60,
                        gatherer.run_command(
                            ["networksetup", "-listallhardwareports"],
                            privileged=False,
                        ),
                        "\nNetwork Status (netstat):",
                        "=" * 60,
                        gatherer.run_command(["netstat", "-i"], privileged=False),
                        "\nBluetooth Information (system_profiler SPBluetoothDataType):",
                        "=" * 60,
                        gatherer.run_command(["system_profiler", "SPBluetoothDataType"], privileged=True),
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

        # Handle output: only write to a file if --output is explicitly provided
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Output saved to {args.output}")
        else:
            print(output)

    except Exception as e:
        logger.error("An error occurred: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
