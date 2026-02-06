"""Formatting utilities for about-this-mac."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import yaml

UNKNOWN_VALUE = "Unknown"
ANSI_RESET = "\x1b[0m"
ANSI_BOLD = "\x1b[1m"
ANSI_RED = "\x1b[31m"
ANSI_GREEN = "\x1b[32m"
ANSI_YELLOW = "\x1b[33m"
ANSI_BLUE = "\x1b[34m"
ANSI_MAGENTA = "\x1b[35m"
ANSI_ORANGE = "\x1b[38;5;208m"
ANSI_PURPLE = "\x1b[38;5;93m"
APPLE_RAINBOW = [
    ANSI_GREEN,
    ANSI_YELLOW,
    ANSI_ORANGE,
    ANSI_RED,
    ANSI_PURPLE,
    ANSI_BLUE,
]
STYLE_SUBSECTION = f"{ANSI_BOLD}{ANSI_BLUE}"


def _coerce_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _coerce_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def _stringify(value: Any, default: str = UNKNOWN_VALUE) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value if value.strip() else default
    return str(value)


def _format_float(value: Any, precision: int = 1, default: str = UNKNOWN_VALUE) -> str:
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return default


def _format_enabled(value: Optional[bool], default: str = UNKNOWN_VALUE) -> str:
    if value is None:
        return default
    return "Enabled" if value else "Disabled"


def _apply_style(value: str, style: str, use_color: bool) -> str:
    if not use_color:
        return value
    return f"{style}{value}{ANSI_RESET}"


def _section_style(index: int) -> str:
    if index < len(APPLE_RAINBOW):
        color = APPLE_RAINBOW[index]
    else:
        color = APPLE_RAINBOW[-1]
    return f"{ANSI_BOLD}{color}"


def _format_uptime_field(value: Any) -> str:
    """Format an uptime field that may be int seconds or a pre-formatted string."""
    if isinstance(value, int):
        if value < 0:
            return UNKNOWN_VALUE
        return format_uptime(value)
    return _stringify(value)


def format_size(size_bytes: Union[int, float]) -> str:
    """Format size in bytes to human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "512 GB", "2 TB")
    """
    try:
        size = float(size_bytes)
    except (TypeError, ValueError):
        return UNKNOWN_VALUE

    if size < 0:
        return UNKNOWN_VALUE
    if size >= 1024**4:  # TB
        return f"{size / (1024 ** 4):.0f} TB"
    if size >= 1024**3:  # GB
        return f"{size / (1024 ** 3):.0f} GB"
    if size >= 1024**2:  # MB
        return f"{size / (1024 ** 2):.0f} MB"
    return f"{int(size)} bytes"


def format_uptime(uptime_seconds: int) -> str:
    """Format uptime in seconds to human readable format.

    Args:
        uptime_seconds: Uptime in seconds

    Returns:
        Formatted string (e.g., "2 days 3 hours 45 minutes")
    """
    if uptime_seconds < 0:
        return UNKNOWN_VALUE

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


def format_bool(value: Optional[bool], unknown: str = UNKNOWN_VALUE) -> str:
    """Format boolean value as Yes/No string.

    Args:
        value: Boolean value

    Returns:
        "Yes" if True, "No" if False
    """
    if value is None or not isinstance(value, bool):
        return unknown
    return "Yes" if value else "No"


def format_output_as_json(data: Dict[str, Any]) -> str:
    """Format data as JSON string.

    Args:
        data: Data dictionary to format

    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def format_output_as_yaml(data: Dict[str, Any]) -> str:
    """Format data as YAML string.

    Args:
        data: Data dictionary to format

    Returns:
        Formatted YAML string
    """
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


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
        hw = _coerce_dict(data.get("hardware"))
        memory = _coerce_dict(hw.get("memory"))
        storage = _coerce_dict(hw.get("storage"))
        graphics = _coerce_list(hw.get("graphics"))

        output.extend(
            [
                "## Hardware Information",
                "",
                "### System",
                f"- **Model:** {_stringify(hw.get('model_name'))}",
                f"- **Identifier:** {_stringify(hw.get('device_identifier'))}",
                f"- **Model Number:** {_stringify(hw.get('model_number'))}",
                f"- **Serial Number:** {_stringify(hw.get('serial_number'))}",
                "",
                "### Processor",
                f"- **Chip:** {_stringify(hw.get('processor'))}",
                "- **CPU Cores:** "
                f"{_stringify(hw.get('cpu_cores'))} ({_stringify(hw.get('performance_cores'))} performance and "
                f"{_stringify(hw.get('efficiency_cores'))} efficiency)",
                f"- **GPU Cores:** {_stringify(hw.get('gpu_cores'))}",
                "",
                "### Memory",
                f"- **Total:** {_stringify(memory.get('total'))}",
                f"- **Type:** {_stringify(memory.get('type'))}",
                f"- **Speed:** {_stringify(memory.get('speed'))}",
                f"- **Manufacturer:** {_stringify(memory.get('manufacturer'))}",
                f"- **ECC:** {format_bool(memory.get('ecc'))}",
                "",
                "### Storage",
                f"- **Model:** {_stringify(storage.get('model'))}",
                f"- **Type:** {_stringify(storage.get('type'))}",
                f"- **Protocol:** {_stringify(storage.get('protocol'))}",
                f"- **Size:** {_stringify(storage.get('size'))}",
                f"- **SMART Status:** {_stringify(storage.get('smart_status'))}",
                f"- **TRIM Support:** {format_bool(storage.get('trim'))}",
                f"- **Internal:** {format_bool(storage.get('internal'))}",
                "",
                "### Graphics",
            ]
        )

        # Add graphics cards
        if graphics:
            for i, card in enumerate(graphics, 1):
                card_info = _coerce_dict(card)
                output.append(f"#### Card {i}")
                name = _stringify(card_info.get("name"), default="")
                vendor = _stringify(card_info.get("vendor"), default="")
                vram = _stringify(card_info.get("vram"), default="")
                resolution = _stringify(card_info.get("resolution"), default="")
                metal = _stringify(card_info.get("metal"), default="")
                if name:
                    output.append(f"- **Model:** {name}")
                if vendor:
                    output.append(f"- **Vendor:** {vendor}")
                if vram:
                    output.append(f"- **VRAM:** {vram}")
                if resolution:
                    output.append(f"- **Resolution:** {resolution}")
                if metal:
                    output.append(f"- **Metal Support:** {metal}")
                output.append("")
        else:
            output.append("*No graphics cards detected*")
            output.append("")

        output.extend(
            [
                "### Wireless",
                f"- **Bluetooth:** {_stringify(hw.get('bluetooth_chipset'))} "
                f"({_stringify(hw.get('bluetooth_firmware'))}) via {_stringify(hw.get('bluetooth_transport'))}",
                "",
                "### System Software",
                f"- **macOS Version:** {_stringify(hw.get('macos_version'))}",
                f"- **Build:** {_stringify(hw.get('macos_build'))}",
                f"- **Uptime:** {_format_uptime_field(hw.get('uptime'))}",
            ]
        )

    # Battery section if available
    if "battery" in data:
        bat = _coerce_dict(data.get("battery"))
        health = _format_float(bat.get("health_percentage"))
        health_display = f"{health}%" if health != UNKNOWN_VALUE else UNKNOWN_VALUE
        temp_c = _format_float(bat.get("temperature_celsius"))
        temp_f = _format_float(bat.get("temperature_fahrenheit"))
        if UNKNOWN_VALUE in (temp_c, temp_f):
            temp_display = UNKNOWN_VALUE
        else:
            temp_display = f"{temp_c}°C / {temp_f}°F"
        charging_power = _format_float(bat.get("charging_power"))
        charging_display = (
            f"{charging_power} Watts" if charging_power != UNKNOWN_VALUE else UNKNOWN_VALUE
        )

        output.extend(
            [
                "",
                "## Battery Information",
                "",
                f"- **Current Charge:** {_stringify(bat.get('current_charge'))}",
                f"- **Health:** {health_display}",
                f"- **Full Charge Capacity:** {_stringify(bat.get('full_charge_capacity'))}",
                f"- **Design Capacity:** {_stringify(bat.get('design_capacity'))}",
                f"- **Manufacture Date:** {_stringify(bat.get('manufacture_date'))}",
                f"- **Cycle Count:** {_stringify(bat.get('cycle_count'))}",
                f"- **Temperature:** {temp_display}",
                f"- **Charging Power:** {charging_display}",
                f"- **Low Power Mode:** {_format_enabled(bat.get('low_power_mode'))}",
            ]
        )

    return "\n".join(output)


def format_output_as_text(data: Dict[str, Any], use_color: bool = False) -> str:
    """Format data as a plain text report similar to About This Mac text output.

    Args:
        data: Data dictionary to format
        use_color: Whether to apply ANSI color to headings.

    Returns:
        Formatted plain text string
    """
    output = []

    heading_index = 0

    def add_section(title: str, underline: str = "=") -> None:
        nonlocal heading_index
        style = _section_style(heading_index)
        heading_index += 1
        styled_title = _apply_style(title, style, use_color)
        styled_underline = _apply_style(underline * len(title), style, use_color)
        output.extend([styled_title, styled_underline])

    def add_subsection(title: str) -> None:
        nonlocal heading_index
        style = _section_style(heading_index)
        heading_index += 1
        styled_title = _apply_style(title, style, use_color)
        styled_underline = _apply_style("-" * len(title), style, use_color)
        output.extend([styled_title, styled_underline])

    # Hardware section first
    if "hardware" in data:
        hw = _coerce_dict(data.get("hardware"))
        memory = _coerce_dict(hw.get("memory"))
        storage = _coerce_dict(hw.get("storage"))
        graphics = _coerce_list(hw.get("graphics"))

        add_section("HARDWARE INFORMATION")
        output.extend(
            [
                f"Model: {_stringify(hw.get('model_name'))}",
                f"Identifier: {_stringify(hw.get('device_identifier'))}",
                f"Model Number: {_stringify(hw.get('model_number'))}",
                f"Serial Number: {_stringify(hw.get('serial_number'))}",
                "",
            ]
        )

        add_subsection("Processor")
        output.extend(
            [
                _stringify(hw.get("processor")),
                "CPU Cores: "
                f"{_stringify(hw.get('cpu_cores'))} ({_stringify(hw.get('performance_cores'))} performance and "
                f"{_stringify(hw.get('efficiency_cores'))} efficiency)",
                f"GPU Cores: {_stringify(hw.get('gpu_cores'))}",
                "",
            ]
        )

        add_subsection("Memory")
        output.extend(
            [
                f"Total: {_stringify(memory.get('total'))}",
                f"Type: {_stringify(memory.get('type'))}",
                f"Speed: {_stringify(memory.get('speed'))}",
                f"Manufacturer: {_stringify(memory.get('manufacturer'))}",
                f"ECC: {format_bool(memory.get('ecc'))}",
                "",
            ]
        )

        add_subsection("Storage")
        output.extend(
            [
                f"Model: {_stringify(storage.get('model'))}",
                f"Type: {_stringify(storage.get('type'))}",
                f"Protocol: {_stringify(storage.get('protocol'))}",
                f"Size: {_stringify(storage.get('size'))}",
                f"SMART Status: {_stringify(storage.get('smart_status'))}",
                f"TRIM Support: {format_bool(storage.get('trim'))}",
                f"Internal: {format_bool(storage.get('internal'))}",
                "",
            ]
        )

        add_subsection("Graphics")
        if graphics:
            for i, card in enumerate(graphics, 1):
                card_info = _coerce_dict(card)
                lines = [f"Card {i}:"]
                name = _stringify(card_info.get("name"), default="")
                vendor = _stringify(card_info.get("vendor"), default="")
                vram = _stringify(card_info.get("vram"), default="")
                resolution = _stringify(card_info.get("resolution"), default="")
                metal = _stringify(card_info.get("metal"), default="")
                if name:
                    lines.append(f"  Model: {name}")
                if vendor:
                    lines.append(f"  Vendor: {vendor}")
                if vram:
                    lines.append(f"  VRAM: {vram}")
                if resolution:
                    lines.append(f"  Resolution: {resolution}")
                if metal:
                    lines.append(f"  Metal Support: {metal}")
                output.extend(lines)
        else:
            output.append("No graphics cards detected")

        output.append("")
        add_subsection("Wireless")
        output.append(
            f"Bluetooth: {_stringify(hw.get('bluetooth_chipset'))} "
            f"({_stringify(hw.get('bluetooth_firmware'))}) via {_stringify(hw.get('bluetooth_transport'))}"
        )
        output.append("")
        add_subsection("System")
        output.extend(
            [
                f"macOS Version: {_stringify(hw.get('macos_version'))}",
                f"Build: {_stringify(hw.get('macos_build'))}",
                f"Uptime: {_format_uptime_field(hw.get('uptime'))}",
            ]
        )

    # Battery section if available
    if "battery" in data:
        bat = _coerce_dict(data.get("battery"))
        health = _format_float(bat.get("health_percentage"))
        health_display = f"{health}%" if health != UNKNOWN_VALUE else UNKNOWN_VALUE
        temp_c = _format_float(bat.get("temperature_celsius"))
        temp_f = _format_float(bat.get("temperature_fahrenheit"))
        if UNKNOWN_VALUE in (temp_c, temp_f):
            temp_display = UNKNOWN_VALUE
        else:
            temp_display = f"{temp_c}°C / {temp_f}°F"
        charging_power = _format_float(bat.get("charging_power"))
        charging_display = (
            f"{charging_power} Watts" if charging_power != UNKNOWN_VALUE else UNKNOWN_VALUE
        )

        if output:
            output.append("")
        add_section("BATTERY INFORMATION")
        output.extend(
            [
                f"Current Charge: {_stringify(bat.get('current_charge'))}",
                f"Health: {health_display}",
                f"Full Charge Capacity: {_stringify(bat.get('full_charge_capacity'))}",
                f"Design Capacity: {_stringify(bat.get('design_capacity'))}",
                f"Manufacture Date: {_stringify(bat.get('manufacture_date'))}",
                f"Cycle Count: {_stringify(bat.get('cycle_count'))}",
                f"Temperature: {temp_display}",
                f"Charging Power: {charging_display}",
                f"Low Power Mode: {_format_enabled(bat.get('low_power_mode'))}",
            ]
        )

    return "\n".join(output)
