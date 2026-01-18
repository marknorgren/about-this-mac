"""Tests for report generation command."""

import io
import json
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

from about_this_mac import MacInfoGatherer
from about_this_mac.commands import report
from about_this_mac.output import Output


@dataclass
class HardwareStub:
    model_name: str


class FakeGatherer:
    def get_hardware_info(self) -> HardwareStub:
        return HardwareStub(model_name="Test Mac")

    def get_battery_info(self) -> None:
        return None

    def format_simple_output(self, data: dict) -> str:
        return "simple-output"

    def format_public_output(self, data: dict) -> str:
        return "public-output"


def test_run_report_writes_file_and_info(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "report.json"
    args = Namespace(
        section="hardware",
        format="json",
        output=str(target),
        color=False,
        no_color=False,
    )
    output = Output()

    report.run_report(args, cast(MacInfoGatherer, FakeGatherer()), output)

    content = json.loads(target.read_text(encoding="utf-8"))
    assert content == {"hardware": {"model_name": "Test Mac"}}
    assert f"Output saved to {target}" in capsys.readouterr().err


def test_run_report_writes_stdout_when_no_output() -> None:
    buffer = io.StringIO()
    args = Namespace(
        section="hardware",
        format="json",
        output=None,
        color=False,
        no_color=False,
    )
    output = Output(file=buffer)

    report.run_report(args, cast(MacInfoGatherer, FakeGatherer()), output)

    assert json.loads(buffer.getvalue()) == {"hardware": {"model_name": "Test Mac"}}


def test_format_output_uses_simple_and_public() -> None:
    data = {"hardware": {"model_name": "Test Mac"}}

    gatherer = cast(MacInfoGatherer, FakeGatherer())
    assert report._format_output(data, "simple", gatherer) == "simple-output"
    assert report._format_output(data, "public", gatherer) == "public-output"
