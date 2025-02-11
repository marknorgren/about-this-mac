"""Command execution utilities."""

import logging
import subprocess
from typing import List

logger = logging.getLogger(__name__)


def run_command(command: List[str], check: bool = True) -> str:
    """Run a shell command and return its output.

    Args:
        command: List of command parts to execute
        check: Whether to check the return code

    Returns:
        The command output as a string
    """
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.debug(f"Command failed: {' '.join(command)}")
        logger.debug(f"Error: {e.stderr}")
        return ""


def get_sysctl_value(key: str) -> str:
    """Get system information using sysctl.

    Args:
        key: The sysctl key to query

    Returns:
        The value as a string, or "Unknown" on error
    """
    try:
        result = subprocess.run(["sysctl", "-n", key], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return "Unknown"
