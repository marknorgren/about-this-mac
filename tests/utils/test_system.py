"""Tests for system utilities."""

import subprocess
from typing import Dict, Any
from unittest.mock import patch, MagicMock

import pytest

from about_this_mac.utils.system import (
    check_macos,
    check_permissions,
    parse_system_profiler_data,
    is_apple_silicon,
)


def test_check_macos_on_macos() -> None:
    """Test macOS check on macOS."""
    with patch("platform.system", return_value="Darwin"):
        check_macos()  # Should not raise


def test_check_macos_on_linux() -> None:
    """Test macOS check on Linux."""
    with patch("platform.system", return_value="Linux"):
        with pytest.raises(SystemError, match="This script only works on macOS"):
            check_macos()


def test_check_permissions_with_sudo() -> None:
    """Test permission check with sudo access."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        assert check_permissions() is True
        mock_run.assert_called_once()


def test_check_permissions_without_sudo() -> None:
    """Test permission check without sudo access."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["system_profiler"])
        assert check_permissions() is False
        mock_run.assert_called_once()


def test_parse_system_profiler_data_success() -> None:
    """Test parsing system profiler data successfully."""
    test_data: Dict[str, Any] = {
        "SPHardwareDataType": [{"model_name": "MacBook Pro", "processor_name": "Apple M2 Max"}]
    }
    result = parse_system_profiler_data(test_data, "SPHardwareDataType")
    assert result == {"model_name": "MacBook Pro", "processor_name": "Apple M2 Max"}


def test_parse_system_profiler_data_missing_type() -> None:
    """Test parsing system profiler data with missing type."""
    test_data: Dict[str, Any] = {"OtherDataType": []}
    result = parse_system_profiler_data(test_data, "SPHardwareDataType")
    assert result is None  # Missing type is treated as invalid data


def test_parse_system_profiler_data_empty_list() -> None:
    """Test parsing system profiler data with empty list."""
    test_data: Dict[str, Any] = {"SPHardwareDataType": []}
    result = parse_system_profiler_data(test_data, "SPHardwareDataType")
    assert result == {}  # Empty list returns empty dict


def test_parse_system_profiler_data_invalid() -> None:
    """Test parsing system profiler data with invalid data."""
    test_data: Dict[str, Any] = {"SPHardwareDataType": None}
    result = parse_system_profiler_data(test_data, "SPHardwareDataType")
    assert result is None  # Invalid data returns None


def test_is_apple_silicon_on_m2() -> None:
    """Test Apple Silicon detection on M2."""
    with patch("platform.processor", return_value="arm"):
        assert is_apple_silicon() is True


def test_is_apple_silicon_on_intel() -> None:
    """Test Apple Silicon detection on Intel."""
    with patch("platform.processor", return_value="i386"):
        assert is_apple_silicon() is False
