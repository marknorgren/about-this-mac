"""Tests for command utilities."""

import subprocess
from unittest.mock import patch, MagicMock

from about_this_mac.utils.command import run_command, get_sysctl_value


def test_run_command_success() -> None:
    """Test successful command execution."""
    with patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.stdout = "test output\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        result = run_command(["echo", "test"])

        assert result == "test output"
        mock_run.assert_called_once_with(
            ["echo", "test"], capture_output=True, text=True, check=True
        )


def test_run_command_failure() -> None:
    """Test command execution failure."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["test"], stderr="error")

        result = run_command(["test"])

        assert result == ""
        mock_run.assert_called_once()


def test_run_command_no_check() -> None:
    """Test command execution without return code checking."""
    with patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.stdout = "test output\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        result = run_command(["echo", "test"], check=False)

        assert result == "test output"
        mock_run.assert_called_once_with(
            ["echo", "test"], capture_output=True, text=True, check=False
        )


def test_get_sysctl_value_success() -> None:
    """Test successful sysctl value retrieval."""
    with patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.stdout = "12345\n"
        mock_run.return_value = mock_process

        result = get_sysctl_value("hw.memsize")

        assert result == "12345"
        mock_run.assert_called_once_with(
            ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=True
        )


def test_get_sysctl_value_failure() -> None:
    """Test sysctl value retrieval failure."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["sysctl"], stderr="error")

        result = get_sysctl_value("invalid.key")

        assert result == "Unknown"
        mock_run.assert_called_once()
