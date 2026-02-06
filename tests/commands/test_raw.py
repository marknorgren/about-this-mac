"""Tests for raw output command."""

import io
from argparse import Namespace
from typing import List, cast
from unittest.mock import patch

from about_this_mac import MacInfoGatherer
from about_this_mac.commands.raw import run_raw_commands
from about_this_mac.output import Output


class FakeGatherer:
    has_full_permissions = True


def _fake_run_command(command: List[str], **kwargs: object) -> str:
    return f"cmd: {' '.join(str(c) for c in command)}"


def _fake_get_sysctl(key: str, **kwargs: object) -> str:
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

    p1 = patch("about_this_mac.commands.raw.run_command", side_effect=_fake_run_command)
    p2 = patch("about_this_mac.commands.raw.get_sysctl_value", side_effect=_fake_get_sysctl)
    with p1, p2:
        run_raw_commands(args, cast(MacInfoGatherer, FakeGatherer()), output)

    raw = buffer.getvalue()
    assert "Hardware Information (system_profiler SPHardwareDataType)" in raw
    assert "cmd: system_profiler SPHardwareDataType" in raw
    assert "hw.model: value:hw.model" in raw
