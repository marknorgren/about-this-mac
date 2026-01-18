"""Raw data output commands for system profiler data."""

from argparse import Namespace
from typing import List

from about_this_mac import MacInfoGatherer
from about_this_mac.output import Output


def _get_hardware_info(gatherer: MacInfoGatherer) -> List[str]:
    """Get raw hardware information."""
    return [
        "\nHardware Information (system_profiler SPHardwareDataType):",
        "=" * 60,
        gatherer.run_command(["system_profiler", "SPHardwareDataType"], privileged=True),
        "\nCPU Information (sysctl):",
        "=" * 60,
        f"hw.model: {gatherer.get_sysctl_value('hw.model')}",
        f"hw.ncpu: {gatherer.get_sysctl_value('hw.ncpu')}",
        f"machdep.cpu.brand_string: {gatherer.get_sysctl_value('machdep.cpu.brand_string')}",
    ]


def _get_power_info(gatherer: MacInfoGatherer) -> List[str]:
    """Get raw power information."""
    return [
        "\nPower Information (system_profiler SPPowerDataType):",
        "=" * 60,
        gatherer.run_command(["system_profiler", "SPPowerDataType"], privileged=True),
        "\nBattery Status (pmset):",
        "=" * 60,
        gatherer.run_command(["pmset", "-g", "batt"], privileged=False),
    ]


def _get_graphics_info(gatherer: MacInfoGatherer) -> List[str]:
    """Get raw graphics information."""
    return [
        "\nGraphics Information (system_profiler SPDisplaysDataType):",
        "=" * 60,
        gatherer.run_command(["system_profiler", "SPDisplaysDataType"], privileged=True),
    ]


def _get_storage_info(gatherer: MacInfoGatherer) -> List[str]:
    """Get raw storage information."""
    return [
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


def _get_memory_info(gatherer: MacInfoGatherer) -> List[str]:
    """Get raw memory information."""
    return [
        "\nMemory Information (system_profiler SPMemoryDataType):",
        "=" * 60,
        gatherer.run_command(["system_profiler", "SPMemoryDataType"], privileged=True),
        "\nMemory Size (sysctl):",
        "=" * 60,
        f"hw.memsize: {gatherer.get_sysctl_value('hw.memsize')}",
    ]


def _get_audio_info(gatherer: MacInfoGatherer) -> List[str]:
    """Get raw audio information."""
    return [
        "\nAudio Information (system_profiler SPAudioDataType):",
        "=" * 60,
        gatherer.run_command(["system_profiler", "SPAudioDataType"], privileged=True),
    ]


def _get_network_info(gatherer: MacInfoGatherer) -> List[str]:
    """Get raw network information."""
    return [
        "\nNetwork Interfaces (networksetup):",
        "=" * 60,
        gatherer.run_command(["networksetup", "-listallhardwareports"], privileged=False),
        "\nNetwork Status (netstat):",
        "=" * 60,
        gatherer.run_command(["netstat", "-i"], privileged=False),
        "\nBluetooth Information (system_profiler SPBluetoothDataType):",
        "=" * 60,
        gatherer.run_command(["system_profiler", "SPBluetoothDataType"], privileged=True),
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
    raw_data: List[str] = []

    if args.hardware_info:
        raw_data.extend(_get_hardware_info(gatherer))

    if args.power_info:
        raw_data.extend(_get_power_info(gatherer))

    if args.graphics_info:
        raw_data.extend(_get_graphics_info(gatherer))

    if args.storage_info:
        raw_data.extend(_get_storage_info(gatherer))

    if args.memory_info:
        raw_data.extend(_get_memory_info(gatherer))

    if args.audio_info:
        raw_data.extend(_get_audio_info(gatherer))

    if args.network_info:
        raw_data.extend(_get_network_info(gatherer))

    output.raw("\n".join(raw_data))
