"""Shared test fixtures for about-this-mac tests."""
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """Mock subprocess.run for testing."""
    mock_run = MagicMock()
    monkeypatch.setattr('subprocess.run', mock_run)
    return mock_run

@pytest.fixture
def sample_ioreg_output():
    """Sample ioreg output for battery tests."""
    return '''
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
'''

@pytest.fixture
def sample_system_profiler_output():
    """Sample system_profiler output for hardware tests."""
    return '''
{
  "SPHardwareDataType" : [
    {
      "machine_model" : "MacBook Pro",
      "machine_name" : "MacBook Pro (14-inch, 2023)",
      "model_number" : "A2779",
      "serial_number" : "ABC123XYZ",
      "processor_name" : "Apple M2 Pro",
      "processor_speed" : "12-Core",
      "number_processors" : "proc 12:8:4",
      "memory" : "32 GB"
    }
  ]
}
'''
