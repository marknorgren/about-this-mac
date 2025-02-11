"""System utilities for platform detection and permissions."""
import logging
import platform
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def check_macos() -> None:
    """Check if running on macOS and raise error if not."""
    if not platform.system() == 'Darwin':
        raise SystemError("This script only works on macOS")

def check_permissions() -> bool:
    """Check if script has necessary permissions for full hardware info.
    
    Returns:
        True if script has full permissions, False otherwise
    """
    try:
        subprocess.run(
            ['system_profiler', 'SPHardwareDataType', '-json'],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        logger.warning(
            "Limited permissions detected. For full hardware information, run with: "
            "sudo python3 -m about_this_mac"
        )
        return False

def parse_system_profiler_data(data: Dict[str, Any], data_type: str) -> Optional[Dict[str, Any]]:
    """Parse system profiler JSON data for a specific data type.
    
    Args:
        data: Raw system profiler JSON data
        data_type: The data type to extract (e.g., 'SPHardwareDataType')
        
    Returns:
        Parsed data dictionary or None if not found
    """
    try:
        return data.get(data_type, [{}])[0]
    except (KeyError, IndexError):
        return None

def is_apple_silicon() -> bool:
    """Check if running on Apple Silicon Mac.
    
    Returns:
        True if Apple Silicon, False if Intel
    """
    return platform.processor() == 'arm' 