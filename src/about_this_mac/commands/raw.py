"""Raw data output commands for system profiler data."""

import logging
from argparse import Namespace
from typing import List, Sequence

from about_this_mac import MacInfoGatherer
from about_this_mac.output import Output
from about_this_mac.utils.command import get_sysctl_value, run_command

logger = logging.getLogger(__name__)


def _run_cmd(command: Sequence[str], privileged: bool, has_full_permissions: bool) -> str:
    """Run a command, skipping privileged commands when permissions are limited."""
    if privileged and not has_full_permissions:
        logger.debug("Skipping privileged command: %s", " ".join(str(c) for c in command))
        return ""
    return run_command(command, check=False)


def _get_hardware_info(perms: bool) -> List[str]:
    """Get raw hardware information."""
    return [
        "\nHardware Information (system_profiler SPHardwareDataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPHardwareDataType"], privileged=True, has_full_permissions=perms),
        "\nCPU Information (sysctl):",
        "=" * 60,
        f"hw.model: {get_sysctl_value('hw.model')}",
        f"hw.ncpu: {get_sysctl_value('hw.ncpu')}",
        f"machdep.cpu.brand_string: {get_sysctl_value('machdep.cpu.brand_string')}",
    ]


def _get_power_info(perms: bool) -> List[str]:
    """Get raw power information."""
    return [
        "\nPower Information (system_profiler SPPowerDataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPPowerDataType"], privileged=True, has_full_permissions=perms),
        "\nBattery Status (pmset):",
        "=" * 60,
        _run_cmd(["pmset", "-g", "batt"], privileged=False, has_full_permissions=perms),
    ]


def _get_graphics_info(perms: bool) -> List[str]:
    """Get raw graphics information."""
    return [
        "\nGraphics Information (system_profiler SPDisplaysDataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPDisplaysDataType"], privileged=True, has_full_permissions=perms),
    ]


def _get_storage_info(perms: bool) -> List[str]:
    """Get raw storage information."""
    return [
        "\nNVMe Storage Information (system_profiler SPNVMeDataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPNVMeDataType"], privileged=True, has_full_permissions=perms),
        "\nSATA Storage Information (system_profiler SPSerialATADataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPSerialATADataType"], privileged=True, has_full_permissions=perms),
        "\nGeneral Storage Information (system_profiler SPStorageDataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPStorageDataType"], privileged=True, has_full_permissions=perms),
    ]


def _get_memory_info(perms: bool) -> List[str]:
    """Get raw memory information."""
    return [
        "\nMemory Information (system_profiler SPMemoryDataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPMemoryDataType"], privileged=True, has_full_permissions=perms),
        "\nMemory Size (sysctl):",
        "=" * 60,
        f"hw.memsize: {get_sysctl_value('hw.memsize')}",
    ]


def _get_audio_info(perms: bool) -> List[str]:
    """Get raw audio information."""
    return [
        "\nAudio Information (system_profiler SPAudioDataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPAudioDataType"], privileged=True, has_full_permissions=perms),
    ]


def _get_network_info(perms: bool) -> List[str]:
    """Get raw network information."""
    return [
        "\nNetwork Interfaces (networksetup):",
        "=" * 60,
        _run_cmd(["networksetup", "-listallhardwareports"], privileged=False, has_full_permissions=perms),
        "\nNetwork Status (netstat):",
        "=" * 60,
        _run_cmd(["netstat", "-i"], privileged=False, has_full_permissions=perms),
        "\nBluetooth Information (system_profiler SPBluetoothDataType):",
        "=" * 60,
        _run_cmd(["system_profiler", "SPBluetoothDataType"], privileged=True, has_full_permissions=perms),
    ]


def has_raw_args(args: Namespace) -> bool:
    """Check if any raw data arguments are set."""
    return any(
        [
            args.hardware_info,
            args.power_info,
            args.graphics_info,
            args.storage_info,
            args.memory_info,
            args.audio_info,
            args.network_info,
        ]
    )


def run_raw_commands(args: Namespace, gatherer: MacInfoGatherer, output: Output) -> None:
    """Execute raw data commands based on CLI arguments."""
    perms = gatherer.has_full_permissions
    raw_data: List[str] = []

    if args.hardware_info:
        raw_data.extend(_get_hardware_info(perms))

    if args.power_info:
        raw_data.extend(_get_power_info(perms))

    if args.graphics_info:
        raw_data.extend(_get_graphics_info(perms))

    if args.storage_info:
        raw_data.extend(_get_storage_info(perms))

    if args.memory_info:
        raw_data.extend(_get_memory_info(perms))

    if args.audio_info:
        raw_data.extend(_get_audio_info(perms))

    if args.network_info:
        raw_data.extend(_get_network_info(perms))

    output.raw("\n".join(raw_data))
