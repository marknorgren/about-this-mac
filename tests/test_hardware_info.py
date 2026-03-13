"""Tests for hardware information gathering."""

from unittest.mock import MagicMock

import pytest

from about_this_mac.hardware.hardware_info import MacInfoGatherer, MemoryInfo, StorageInfo


def test_get_hardware_info_uses_single_release_date_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_hardware_info should fetch release metadata once and reuse it."""
    gatherer = object.__new__(MacInfoGatherer)
    gatherer._battery = MagicMock()
    gatherer._cached_hw_json = """
    {
      "SPHardwareDataType": [
        {
          "machine_model": "MacBook Pro",
          "machine_name": "MacBook Pro (14-inch, 2023)",
          "model_number": "A2779",
          "serial_number": "SER123"
        }
      ]
    }
    """
    gatherer.has_full_permissions = True

    monkeypatch.setattr(
        "about_this_mac.hardware.hardware_info.platform.mac_ver", lambda: ("14.4", "", "")
    )
    monkeypatch.setattr("about_this_mac.hardware.hardware_info.platform.processor", lambda: "arm")

    model_metadata_mock = MagicMock(return_value=("MacBook Pro", "14-inch", "2023", "Jan 2023"))

    monkeypatch.setattr(
        gatherer,
        "_parse_apple_silicon_info",
        MagicMock(return_value=("Apple M2 Pro", 12, 8, 4, 19)),
    )
    monkeypatch.setattr(
        gatherer,
        "_run_command",
        MagicMock(
            return_value='{"SPSoftwareDataType":[{"kernel_version":"Darwin 23.4.0 (23E214)"}]}'
        ),
    )
    monkeypatch.setattr(gatherer, "_get_sysctl_value", MagicMock(return_value="Mac14,5"))
    monkeypatch.setattr(
        gatherer,
        "_get_memory_info",
        MagicMock(
            return_value=MemoryInfo(
                total="16 GB",
                type="LPDDR5",
                speed="6400 MHz",
                manufacturer="Apple",
                ecc=False,
            )
        ),
    )
    monkeypatch.setattr(
        gatherer,
        "_get_storage_info",
        MagicMock(
            return_value=StorageInfo(
                name="Apple SSD",
                model="Apple SSD",
                revision="1.0",
                serial="SSD123",
                size="512 GB",
                type="NVMe",
                protocol="PCIe",
                trim=True,
                smart_status="Verified",
                removable=False,
                internal=True,
            )
        ),
    )
    monkeypatch.setattr(gatherer, "_get_graphics_info", MagicMock(return_value=[]))
    monkeypatch.setattr(
        gatherer, "_get_bluetooth_info", MagicMock(return_value=("Apple", "1.0", "USB"))
    )
    monkeypatch.setattr(gatherer, "_get_uptime", MagicMock(return_value=183600))
    monkeypatch.setattr(
        gatherer,
        "_get_model_metadata",
        model_metadata_mock,
    )

    info = gatherer.get_hardware_info()

    assert info.model_name == "MacBook Pro"
    assert info.device_identifier == "Mac14,5"
    assert info.release_date == "Jan 2023"
    model_metadata_mock.assert_called_once_with(
        {
            "machine_model": "MacBook Pro",
            "machine_name": "MacBook Pro (14-inch, 2023)",
            "model_number": "A2779",
            "serial_number": "SER123",
        }
    )


def test_get_hardware_info_handles_unknown_sysctl_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown sysctl values should not crash fallback hardware collection."""
    gatherer = object.__new__(MacInfoGatherer)
    gatherer._battery = MagicMock()
    gatherer._cached_hw_json = ""
    gatherer.has_full_permissions = False

    monkeypatch.setattr("about_this_mac.hardware.hardware_info.platform.machine", lambda: "x86_64")
    monkeypatch.setattr(
        "about_this_mac.hardware.hardware_info.platform.mac_ver", lambda: ("14.4", "", "")
    )
    monkeypatch.setattr("about_this_mac.hardware.hardware_info.platform.processor", lambda: "i386")
    monkeypatch.setattr(gatherer, "_run_command", MagicMock(return_value=""))
    monkeypatch.setattr(gatherer, "_get_sysctl_value", MagicMock(return_value="Unknown"))
    monkeypatch.setattr(
        gatherer,
        "_get_memory_info",
        MagicMock(
            return_value=MemoryInfo(
                total="Unknown",
                type="Unknown",
                speed="Unknown",
                manufacturer="Unknown",
                ecc=False,
            )
        ),
    )
    monkeypatch.setattr(
        gatherer,
        "_get_storage_info",
        MagicMock(
            return_value=StorageInfo(
                name="Unknown",
                model="Unknown",
                revision="Unknown",
                serial="Unknown",
                size="Unknown",
                type="Unknown",
                protocol="Unknown",
                trim=False,
                smart_status="Unknown",
                removable=False,
                internal=False,
            )
        ),
    )
    monkeypatch.setattr(gatherer, "_get_graphics_info", MagicMock(return_value=[]))
    monkeypatch.setattr(
        gatherer, "_get_bluetooth_info", MagicMock(return_value=("Unknown", "Unknown", "Unknown"))
    )
    monkeypatch.setattr(gatherer, "_get_uptime", MagicMock(return_value=None))
    monkeypatch.setattr(
        gatherer,
        "_get_model_metadata",
        MagicMock(return_value=("Mac", "", "", "Unknown")),
    )

    info = gatherer.get_hardware_info()

    assert info.processor == "Unknown"
    assert info.cpu_cores == 0
    assert info.performance_cores == 0
    assert info.efficiency_cores == 0
    assert info.device_identifier == "x86_64"
