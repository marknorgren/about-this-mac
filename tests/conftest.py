"""Test fixtures for about-this-mac."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_subprocess_run(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock subprocess.run for testing."""
    mock_run = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def sample_ioreg_output() -> str:
    """Sample ioreg output for battery tests."""
    return """
+-o AppleSmartBattery  <class AppleSmartBattery, id 0x100000123, registered, matched, active, busy 0 (0 ms), retain 8>
    {
      "AppleRawCurrentCapacity" = 1000
      "AppleRawMaxCapacity" = 2000
      "DesignCapacity" = 2500
      "CycleCount" = 100
      "Temperature" = 3000
      "Voltage" = 10000
      "Amperage" = -500
      "ManufactureDate" = <00 00 07 07 0c 1a>
    }
"""


@pytest.fixture
def sample_system_profiler_output() -> str:
    """Sample system_profiler output for hardware tests."""
    return """
{
  "SPHardwareDataType" : [
    {
      "machine_model" : "MacBook Pro",
      "machine_name" : "MacBook Pro (14-inch, 2023)",
      "model_number" : "TESTMODEL",
      "serial_number" : "TEST123456",
      "processor_name" : "Test Processor",
      "processor_speed" : "12-Core",
      "number_processors" : "proc 12:8:4",
      "memory" : "32 GB"
    }
  ]
}
"""
