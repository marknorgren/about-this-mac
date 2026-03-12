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

    release_date_mock = MagicMock(return_value=("Jan 2023", "2023-01", "product-release"))
    model_info_mock = MagicMock(return_value=("MacBook Pro", "14-inch", "2023"))

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
        "_get_release_date",
        release_date_mock,
    )
    monkeypatch.setattr(
        gatherer,
        "_get_model_info",
        model_info_mock,
    )

    info = gatherer.get_hardware_info()

    assert info.model_name == "MacBook Pro"
    assert info.device_identifier == "Mac14,5"
    assert info.release_date == "Jan 2023"
    model_info_mock.assert_called_once()
    assert model_info_mock.call_args.kwargs["release_date"] == "Jan 2023"
    release_date_mock.assert_called_once()
