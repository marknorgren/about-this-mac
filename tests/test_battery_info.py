"""Tests for battery info module."""

from unittest.mock import patch, MagicMock

import pytest

from about_this_mac.battery.battery_info import BatteryInfo, BatteryInfoGatherer
from about_this_mac.utils.command import CommandResult

# Sample ioreg output for testing
SAMPLE_IOREG_OUTPUT = """
+-o AppleSmartBattery  <class AppleSmartBattery, id 0x100000123, registered, matched, active, busy 0 (0 ms), retain 8>
    {
      "AppleRawCurrentCapacity" = 3584
      "AppleRawMaxCapacity" = 4837
      "DesignCapacity" = 6075
      "CycleCount" = 228
      "Temperature" = 3029
      "Voltage" = 12300
      "Amperage" = -915
      "ManufactureDate" = <00 00 07 07 0c 1a>
    }
"""


def test_battery_info_creation() -> None:
    """Test creating a BatteryInfo object with valid data."""
    battery_info = BatteryInfo(
        current_charge="3584 mAh",
        health_percentage=79.6,
        full_charge_capacity="4837 mAh",
        design_capacity="6075 mAh",
        manufacture_date="2022-12-26",
        cycle_count=228,
        temperature_celsius=30.3,
        temperature_fahrenheit=86.6,
        charging_power=9.9,
        low_power_mode=False,
    )

    assert battery_info.current_charge == "3584 mAh"
    assert battery_info.health_percentage == pytest.approx(79.6)
    assert battery_info.full_charge_capacity == "4837 mAh"
    assert battery_info.design_capacity == "6075 mAh"
    assert battery_info.manufacture_date == "2022-12-26"
    assert battery_info.cycle_count == 228
    assert battery_info.temperature_celsius == pytest.approx(30.3)
    assert battery_info.temperature_fahrenheit == pytest.approx(86.6)
    assert battery_info.charging_power == pytest.approx(9.9)
    assert battery_info.low_power_mode is False


def _result(
    command: list, stdout: str = "", stderr: str = "", returncode: int = 0
) -> CommandResult:
    return CommandResult(command=command, stdout=stdout, stderr=stderr, returncode=returncode)


@patch("about_this_mac.battery.battery_info.run_command_result")
def test_battery_info_gathering(mock_run: MagicMock) -> None:
    """Test gathering battery information from system."""
    mock_run.side_effect = [
        _result(["ioreg", "-r", "-n", "AppleSmartBattery"], stdout=SAMPLE_IOREG_OUTPUT),
        _result(["pmset", "-g"], stdout="lowpowermode 0"),
    ]

    gatherer = BatteryInfoGatherer()
    battery_info = gatherer.get_battery_info()

    assert battery_info is not None
    assert battery_info.current_charge == "3584 mAh"
    assert battery_info.health_percentage == pytest.approx(
        79.62, rel=1e-2
    )  # Allow 1% relative tolerance
    assert battery_info.full_charge_capacity == "4837 mAh"
    assert battery_info.design_capacity == "6075 mAh"
    assert battery_info.cycle_count == 228
    assert battery_info.temperature_celsius == pytest.approx(
        30.29, rel=1e-3
    )  # Allow 0.1% relative tolerance
    assert battery_info.temperature_fahrenheit == pytest.approx(
        86.522, rel=1e-3
    )  # Allow 0.1% relative tolerance
    assert battery_info.charging_power == pytest.approx(
        11.2545, rel=1e-3
    )  # Allow 0.1% relative tolerance
    assert battery_info.low_power_mode is False


@patch("about_this_mac.battery.battery_info.run_command_result")
def test_battery_info_gathering_no_battery(mock_run: MagicMock) -> None:
    """Test gathering battery information when no battery is present."""
    mock_run.return_value = _result(
        ["ioreg", "-r", "-n", "AppleSmartBattery"], stderr="No battery found", returncode=1
    )

    gatherer = BatteryInfoGatherer()
    battery_info = gatherer.get_battery_info()

    assert battery_info is None


@patch("about_this_mac.battery.battery_info.run_command_result")
def test_battery_info_gathering_with_low_power_mode(mock_run: MagicMock) -> None:
    """Test gathering battery information with low power mode enabled."""
    mock_run.side_effect = [
        _result(["ioreg", "-r", "-n", "AppleSmartBattery"], stdout=SAMPLE_IOREG_OUTPUT),
        _result(["pmset", "-g"], stdout="lowpowermode 1"),
    ]

    gatherer = BatteryInfoGatherer()
    battery_info = gatherer.get_battery_info()

    assert battery_info is not None
    assert battery_info.low_power_mode is True
