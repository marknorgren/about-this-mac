"""Tests for raw output command."""

import io
from argparse import Namespace
from typing import cast

from about_this_mac import MacInfoGatherer
from about_this_mac.commands.raw import run_raw_commands
from about_this_mac.output import Output


class FakeGatherer:
    def run_command(self, command: list, privileged: bool = False) -> str:
        return f"cmd: {' '.join(command)}"

    def get_sysctl_value(self, key: str) -> str:
        return f"value:{key}"


def test_run_raw_commands_hardware_output() -> None:
    buffer = io.StringIO()
    output = Output(file=buffer)
    args = Namespace(
        hardware_info=True,
        power_info=False,
        graphics_info=False,
        storage_info=False,
        memory_info=False,
        audio_info=False,
        network_info=False,
    )

    run_raw_commands(args, cast(MacInfoGatherer, FakeGatherer()), output)

    raw = buffer.getvalue()
    assert "Hardware Information (system_profiler SPHardwareDataType)" in raw
    assert "cmd: system_profiler SPHardwareDataType" in raw
    assert "hw.model: value:hw.model" in raw
