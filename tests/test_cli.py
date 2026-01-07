"""Minimal tests for CLI behavior regarding output formatting and file writing."""

import io
import os
from contextlib import redirect_stdout, redirect_stderr
from typing import List

import builtins
import types

import pytest

from dataclasses import dataclass


# Import dataclasses from the package to construct fake hardware info
from about_this_mac.hardware.hardware_info import HardwareInfo, MemoryInfo, StorageInfo


@dataclass
class FakeGatherer:
    """Fake gatherer to avoid running system commands in tests."""

    verbose: bool = False

    def get_hardware_info(self) -> HardwareInfo:
        memory = MemoryInfo(total="16 GB", type="LPDDR5", speed="6400 MHz", manufacturer="Apple", ecc=False)
        storage = StorageInfo(
            name="Apple SSD",
            model="Apple SSD",
            revision="1.0",
            serial="XYZ",
            size="512 GB",
            type="NVMe",
            protocol="PCIe",
            trim=True,
            smart_status="Verified",
            removable=False,
            internal=True,
        )
        return HardwareInfo(
            model_name="MacBook Pro",
            device_identifier="Mac14,5",
            model_number="A2779",
            serial_number="SER123",
            processor="Apple M2",
            cpu_cores=8,
            performance_cores=4,
            efficiency_cores=4,
            gpu_cores=10,
            memory=memory,
            storage=storage,
            graphics=[],
            bluetooth_chipset="Apple",
            bluetooth_firmware="1.0",
            bluetooth_transport="USB",
            macos_version="14.0",
            macos_build="23A344",
            uptime="2 days 3 hours",
        )

    def get_battery_info(self):  # pragma: no cover - unused in these tests
        return None

    # Methods used by CLI for raw modes are not needed in these tests


def run_cli(monkeypatch: pytest.MonkeyPatch, args: List[str], tmpdir) -> tuple[str, str]:
    """Helper to run CLI with patched gatherer and capture stdout/stderr."""
    import about_this_mac.cli as cli

    # Patch the gatherer used inside cli
    monkeypatch.setattr(cli, "MacInfoGatherer", FakeGatherer)

    # Change working directory to a temp dir to avoid stray files
    monkeypatch.chdir(tmpdir)

    # Patch sys.argv
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")
    monkeypatch.setattr("sys.argv", ["about-this-mac"] + args, raising=False)

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        cli.main()
    return stdout_buf.getvalue(), stderr_buf.getvalue()


def test_markdown_without_output_prints_to_stdout(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    output, errors = run_cli(monkeypatch, ["--format", "markdown"], tmp_path)
    assert output.startswith("# Mac System Information")
    assert errors == ""
    # Ensure no auto-saved markdown file exists
    files = list(os.listdir(tmp_path))
    assert not any(name.endswith(".md") for name in files)


def test_markdown_with_output_writes_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    target = tmp_path / "report.md"
    output, errors = run_cli(
        monkeypatch, ["--format", "markdown", "--output", str(target)], tmp_path
    )
    assert output == ""
    assert f"Output saved to {target}" in errors
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert content.startswith("# Mac System Information")
