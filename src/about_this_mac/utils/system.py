"""System utilities for platform detection and permissions."""

import logging
import platform
import subprocess
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def check_macos() -> None:
    """Check if running on macOS and raise error if not."""
    if platform.system() != "Darwin":
        raise SystemError("This script only works on macOS")


def check_permissions(timeout: Optional[float] = None) -> bool:
    """Check if script has necessary permissions for full hardware info.

    Args:
        timeout: Optional timeout in seconds.

    Returns:
        True if script has full permissions, False otherwise.
    """
    try:
        subprocess.run(
            ["system_profiler", "SPHardwareDataType", "-json"],
            capture_output=True,
            check=True,
            timeout=timeout,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
        logger.warning(
            "Limited permissions detected. For full hardware information, run with: "
            "sudo python3 -m about_this_mac"
        )
        return False


def parse_system_profiler_data(data: Dict[str, Any], data_type: str) -> Optional[Dict[str, Any]]:
    """Parse system profiler JSON data for a specific data type.

    Args:
        data: Raw system profiler JSON data.
        data_type: The data type to extract (e.g., 'SPHardwareDataType').

    Returns:
        Parsed data dictionary or None if invalid data.
        Returns empty dict if data type is missing or empty list.
    """
    try:
        data_array = data.get(data_type)
        if data_array is None or not isinstance(data_array, list):
            return None

        if not data_array:
            return {}

        first_item = data_array[0]
        if not isinstance(first_item, dict):
            return None

        return first_item
    except (AttributeError, TypeError):
        return None


def is_apple_silicon() -> bool:
    """Check if running on Apple Silicon Mac.

    Returns:
        True if Apple Silicon, False if Intel.
    """
    processor = (platform.processor() or "").lower()
    if processor:
        return processor.startswith("arm")
    machine = (platform.machine() or "").lower()
    return machine in {"arm64", "aarch64"}
