"""Root package for about-this-mac."""

from .battery import BatteryInfo, BatteryInfoGatherer
from .hardware import MacInfoGatherer, HardwareInfo, MemoryInfo, StorageInfo

__version__ = "0.2.2"

__all__ = [
    "BatteryInfo",
    "BatteryInfoGatherer",
    "MacInfoGatherer",
    "HardwareInfo",
    "MemoryInfo",
    "StorageInfo",
]
