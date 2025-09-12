"""Formatting utilities for about-this-mac."""

import json
from datetime import datetime
from typing import Dict, Any

import yaml


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "512 GB", "2 TB")
    """
    if size_bytes >= 1024**4:  # TB
        return f"{size_bytes / (1024 ** 4):.0f} TB"
    elif size_bytes >= 1024**3:  # GB
        return f"{size_bytes / (1024 ** 3):.0f} GB"
    elif size_bytes >= 1024**2:  # MB
        return f"{size_bytes / (1024 ** 2):.0f} MB"
    else:
        return f"{size_bytes} bytes"


def format_uptime(uptime_seconds: int) -> str:
    """Format uptime in seconds to human readable format.

    Args:
        uptime_seconds: Uptime in seconds

    Returns:
        Formatted string (e.g., "2 days 3 hours 45 minutes")
    """
    days = uptime_seconds // 86400
    uptime_seconds %= 86400
    hours = uptime_seconds // 3600
    uptime_seconds %= 3600
    minutes = uptime_seconds // 60

    parts = []
    if days > 0:
        parts.append(f"{days} {'day' if days == 1 else 'days'}")
    if hours > 0:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if minutes > 0:
        parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")

    return " ".join(parts) if parts else "0 minutes"


def format_bool(value: bool) -> str:
    """Format boolean value as Yes/No string.

    Args:
        value: Boolean value

    Returns:
        "Yes" if True, "No" if False
    """
    return "Yes" if value else "No"


def format_output_as_json(data: Dict[str, Any]) -> str:
    """Format data as JSON string.

    Args:
        data: Data dictionary to format

    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=2)


def format_output_as_yaml(data: Dict[str, Any]) -> str:
    """Format data as YAML string.

    Args:
        data: Data dictionary to format

    Returns:
        Formatted YAML string
    """
    return yaml.dump(data, sort_keys=False)


def format_output_as_markdown(data: Dict[str, Any]) -> str:
    """Format data as markdown string.

    Args:
        data: Data dictionary to format

    Returns:
        Formatted markdown string
    """
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
                f"- **ECC:** {format_bool(hw['memory']['ecc'])}",
                "",
                "### Storage",
                f"- **Model:** {hw['storage']['model']}",
                f"- **Type:** {hw['storage']['type']}",
                f"- **Protocol:** {hw['storage']['protocol']}",
                f"- **Size:** {hw['storage']['size']}",
                f"- **SMART Status:** {hw['storage']['smart_status']}",
                f"- **TRIM Support:** {format_bool(hw['storage']['trim'])}",
                f"- **Internal:** {format_bool(hw['storage']['internal'])}",
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


def format_output_as_text(data: Dict[str, Any]) -> str:
    """Format data as a plain text report similar to About This Mac text output.

    Args:
        data: Data dictionary to format

    Returns:
        Formatted plain text string
    """
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
                "CPU Cores: "
                f"{hw['cpu_cores']} ({hw['performance_cores']} performance and {hw['efficiency_cores']} efficiency)",
                f"GPU Cores: {hw['gpu_cores']}",
                "",
                "Memory",
                "------",
                f"Total: {hw['memory']['total']}",
                f"Type: {hw['memory']['type']}",
                f"Speed: {hw['memory']['speed']}",
                f"Manufacturer: {hw['memory']['manufacturer']}",
                f"ECC: {format_bool(hw['memory']['ecc'])}",
                "",
                "Storage",
                "-------",
                f"Model: {hw['storage']['model']}",
                f"Type: {hw['storage']['type']}",
                f"Protocol: {hw['storage']['protocol']}",
                f"Size: {hw['storage']['size']}",
                f"SMART Status: {hw['storage']['smart_status']}",
                f"TRIM Support: {format_bool(hw['storage']['trim'])}",
                f"Internal: {format_bool(hw['storage']['internal'])}",
                "",
                "Graphics",
                "--------",
            ]
        )

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
