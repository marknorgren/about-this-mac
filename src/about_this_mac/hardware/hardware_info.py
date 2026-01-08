"""Hardware information gathering module."""

import json
import logging
import platform
import subprocess
import re
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from about_this_mac.battery import BatteryInfoGatherer
from about_this_mac.utils.command import run_command_result

logger = logging.getLogger(__name__)


@dataclass
class MemoryInfo:
    """Data class for memory information."""

    total: str
    type: str
    speed: str
    manufacturer: str
    ecc: bool


@dataclass
class StorageInfo:
    """Data class for storage information."""

    name: str
    model: str
    revision: str
    serial: str
    size: str
    type: str  # NVMe, SATA, etc.
    protocol: str  # Apple Fabric, PCIe, etc.
    trim: bool
    smart_status: str
    removable: bool
    internal: bool


@dataclass
class HardwareInfo:
    """Data class for hardware information."""

    model_name: str
    device_identifier: str
    model_number: str
    serial_number: str
    processor: str
    cpu_cores: int
    performance_cores: int
    efficiency_cores: int
    gpu_cores: int
    memory: MemoryInfo
    storage: StorageInfo
    graphics: List[Dict[str, str]]
    bluetooth_chipset: str
    bluetooth_firmware: str
    bluetooth_transport: str
    macos_version: str
    macos_build: str
    uptime: str


class MacInfoGatherer(BatteryInfoGatherer):
    """Class for gathering Mac hardware information."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the gatherer."""
        super().__init__()
        if verbose:
            logger.setLevel(logging.DEBUG)

        if not platform.system() == "Darwin":
            raise SystemError("This script only works on macOS")

        self.has_full_permissions = self._check_permissions()
        if not self.has_full_permissions:
            logger.warning(
                "Limited permissions detected. For full hardware information, run with: "
                "sudo python3 about-this-mac.py"
            )

    def _check_permissions(self) -> bool:
        """Check if script has necessary permissions."""
        try:
            # Try to access a privileged command
            subprocess.run(
                ["system_profiler", "SPHardwareDataType", "-json"], capture_output=True, check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _run_command(self, command: List[str], privileged: bool = False) -> str:
        """Run a shell command and return its output."""
        if privileged and not self.has_full_permissions:
            logger.debug("Skipping privileged command: %s", " ".join(command))
            return ""

        result = run_command_result(command, check=False)
        if result.ok:
            return result.stdout
        logger.debug("Command failed (exit %s): %s", result.returncode, " ".join(result.command))
        if result.stderr:
            logger.debug("Command stderr: %s", result.stderr)
        return ""

    # Public helpers for raw data access
    def run_command(self, command: List[str], privileged: bool = False) -> str:
        """Public wrapper to run commands with optional privilege gating."""
        return self._run_command(command, privileged=privileged)

    def get_sysctl_value(self, key: str) -> str:
        """Public wrapper for sysctl value retrieval."""
        return self._get_sysctl_value(key)

    def _get_sysctl_value(self, key: str) -> str:
        """Get system information using sysctl."""
        result = run_command_result(["sysctl", "-n", key], check=False)
        if result.ok and result.stdout:
            return result.stdout
        if not result.ok:
            logger.debug("sysctl failed (exit %s) for key %s", result.returncode, key)
            if result.stderr:
                logger.debug("sysctl stderr: %s", result.stderr)
        return "Unknown"

    def _parse_apple_silicon_info(self, hw_data: Dict[str, Any]) -> Tuple[str, int, int, int, int]:
        """Parse Apple Silicon processor details."""
        # Get processor name from hardware info
        processor_name = hw_data.get("chip_info", "")
        if not processor_name:
            processor_name = hw_data.get("processor_name", "")
            if not processor_name:
                # Try to get from graphics info as fallback
                graphics_info = self._run_command(
                    ["system_profiler", "SPDisplaysDataType"], privileged=True
                )
                if graphics_info:
                    for line in graphics_info.split("\n"):
                        if any(f"Apple M{i}" in line for i in range(1, 5)):
                            processor_name = line.strip()
                            break

        # Get CPU cores
        total_cores = 0
        performance_cores = 0
        efficiency_cores = 0
        try:
            core_info = hw_data.get("number_processors", "")
            if isinstance(core_info, str) and ":" in core_info:
                # Handle format like "proc 12:8:4" (total:performance:efficiency)
                core_parts = core_info.split(":")
                total_cores = int(core_parts[0].split()[-1])  # Get total cores
                performance_cores = int(core_parts[1])
                efficiency_cores = int(core_parts[2])
            else:
                total_cores = int(core_info)
        except (ValueError, IndexError):
            pass

        # Get GPU cores from graphics info
        graphics_info = self._run_command(
            ["system_profiler", "SPDisplaysDataType"], privileged=True
        )

        gpu_cores = 0
        if graphics_info:
            # Try to find GPU cores in the text output
            for line in graphics_info.split("\n"):
                line = line.strip()
                if "Cores:" in line:
                    try:
                        gpu_cores = int(line.split(":")[1].strip())
                        break
                    except (ValueError, IndexError):
                        pass
                elif "-core GPU" in line.lower():
                    try:
                        gpu_cores = int(line.split("-core")[0].strip())
                        break
                    except (ValueError, IndexError):
                        pass

            # If still not found, try to determine from the chip name
            if gpu_cores == 0 and processor_name:
                # Default GPU cores for different chips
                chip_gpu_cores = {
                    "M1": 7,
                    "M1 Pro": 14,
                    "M1 Max": 24,
                    "M1 Ultra": 48,
                    "M2": 10,
                    "M2 Pro": 19,
                    "M2 Max": 38,
                    "M2 Ultra": 76,
                    "M3": 10,
                    "M3 Pro": 18,
                    "M3 Max": 40,
                    "M4": 16,
                    "M4 Pro": 28,
                    "M4 Max": 40,
                }
                for chip, core_count in chip_gpu_cores.items():
                    if chip in processor_name:
                        gpu_cores = core_count
                        break

        return processor_name, total_cores, performance_cores, efficiency_cores, gpu_cores

    def _get_graphics_info(self) -> List[Dict[str, str]]:
        """Get detailed graphics information."""
        graphics_cards = []

        graphics_info = self._run_command(
            ["system_profiler", "SPDisplaysDataType", "-json"], privileged=True
        )

        if graphics_info:
            try:
                graphics_data = json.loads(graphics_info).get("SPDisplaysDataType", [])
                for card in graphics_data:
                    if isinstance(card, dict):
                        # Determine vendor and icon
                        vendor = card.get("spdisplays_vendor", "")
                        vendor = vendor.split()[0] if vendor else ""

                        # Get resolution
                        resolution = card.get("spdisplays_resolution", "")
                        if isinstance(resolution, list):
                            resolution = resolution[0] if resolution else ""

                        graphics_cards.append(
                            {
                                "name": card.get("sppci_model", ""),
                                "vendor": vendor,
                                "vram": card.get("spdisplays_vram", ""),
                                "resolution": resolution,
                                "metal": card.get("spdisplays_metal", ""),
                                "display_type": card.get("spdisplays_display_type", ""),
                            }
                        )
            except (json.JSONDecodeError, KeyError):
                pass

        return graphics_cards

    def _get_memory_info(self) -> MemoryInfo:
        """Get detailed memory information."""
        memory_size = f"{int(int(self._get_sysctl_value('hw.memsize')) / (1024**3))}GB"
        memory_type = "Unknown"
        memory_speed = "Unknown"
        manufacturer = "Unknown"
        ecc = False

        memory_info = self._run_command(
            ["system_profiler", "SPMemoryDataType", "-json"], privileged=True
        )

        if memory_info:
            try:
                memory_data = json.loads(memory_info).get("SPMemoryDataType", [{}])[0]
                if isinstance(memory_data, dict):
                    memory_type = memory_data.get("dimm_type", memory_type)
                    manufacturer = memory_data.get("dimm_manufacturer", manufacturer)
                    # Some Macs report ECC status
                    ecc = "ecc" in str(memory_type).lower()
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        return MemoryInfo(
            total=memory_size,
            type=memory_type,
            speed=memory_speed,
            manufacturer=manufacturer,
            ecc=ecc,
        )

    def _get_storage_info(self) -> StorageInfo:
        """Get detailed storage information."""
        # Try NVMe first
        nvme_info = self._run_command(
            ["system_profiler", "SPNVMeDataType", "-json"], privileged=True
        )

        if nvme_info:
            try:
                nvme_data = json.loads(nvme_info).get("SPNVMeDataType", [{}])[0]
                items = nvme_data.get("_items", [{}])[0]
                return StorageInfo(
                    name=items.get("_name", "Unknown"),
                    model=items.get("device_model", "Unknown"),
                    revision=items.get("device_revision", "Unknown"),
                    serial=items.get("device_serial", "Unknown"),
                    size=items.get("size", "Unknown"),
                    type="NVMe",
                    protocol="PCIe",
                    trim=items.get("spnvme_trim_support", "No") == "Yes",
                    smart_status=items.get("smart_status", "Unknown"),
                    removable=items.get("removable_media", "no") == "yes",
                    internal=items.get("detachable_drive", "yes") == "no",
                )
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        # Try SATA if no NVMe
        sata_info = self._run_command(
            ["system_profiler", "SPSerialATADataType", "-json"], privileged=True
        )

        if sata_info:
            try:
                sata_data = json.loads(sata_info).get("SPSerialATADataType", [{}])[0]
                items = sata_data.get("_items", [{}])[0]
                return StorageInfo(
                    name=items.get("_name", "Unknown"),
                    model=items.get("device_model", "Unknown"),
                    revision=items.get("device_revision", "Unknown"),
                    serial=items.get("device_serial", "Unknown"),
                    size=items.get("size", "Unknown"),
                    type="SATA",
                    protocol="SATA",
                    trim=False,  # SATA doesn't typically report TRIM
                    smart_status=items.get("smart_status", "Unknown"),
                    removable=items.get("removable_media", "no") == "yes",
                    internal=items.get("detachable_drive", "yes") == "no",
                )
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        # Fallback to basic storage info
        storage_info = self._run_command(
            ["system_profiler", "SPStorageDataType", "-json"], privileged=True
        )

        if storage_info:
            try:
                storage_data = json.loads(storage_info).get("SPStorageDataType", [{}])[0]
                physical_drive = storage_data.get("physical_drive", {})
                return StorageInfo(
                    name=storage_data.get("_name", "Unknown"),
                    model=physical_drive.get("device_name", "Unknown"),
                    revision="Unknown",
                    serial="Unknown",
                    size=str(int(storage_data.get("size_in_bytes", 0) / (1024**3))) + " GB",
                    type=physical_drive.get("medium_type", "Unknown"),
                    protocol=physical_drive.get("protocol", "Unknown"),
                    trim=False,
                    smart_status=physical_drive.get("smart_status", "Unknown"),
                    removable=not physical_drive.get("is_internal_disk", "no") == "yes",
                    internal=physical_drive.get("is_internal_disk", "no") == "yes",
                )
            except (json.JSONDecodeError, KeyError):
                pass

        return StorageInfo(
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
            internal=True,
        )

    def _get_bluetooth_info(self) -> Tuple[str, str, str]:
        """Get detailed Bluetooth information."""
        try:
            bluetooth_info = self._run_command(
                ["system_profiler", "SPBluetoothDataType", "-json"], privileged=True
            )
            if bluetooth_info:
                data = json.loads(bluetooth_info)
                controller = data.get("SPBluetoothDataType", [{}])[0].get(
                    "controller_properties", {}
                )
                return (
                    controller.get("controller_chipset", "Unknown"),
                    controller.get("controller_firmwareVersion", "Unknown"),
                    controller.get("controller_transport", "Unknown"),
                )
        except:
            pass
        return ("Unknown", "Unknown", "Unknown")

    def get_hardware_info(self) -> HardwareInfo:
        """Gather hardware information using system_profiler and sysctl."""
        # Get basic hardware info
        hw_info = self._run_command(
            ["system_profiler", "SPHardwareDataType", "-json"], privileged=True
        )

        if hw_info:
            hw_data = json.loads(hw_info).get("SPHardwareDataType", [{}])[0]
        else:
            hw_data = {
                "machine_model": self._get_sysctl_value("hw.model"),
                "machine_name": platform.machine(),
                "model_number": "Unknown (needs sudo)",
                "serial_number": "Unknown (needs sudo)",
                "cpu_type": self._get_sysctl_value("machdep.cpu.brand_string"),
                "physical_memory": f"{int(int(self._get_sysctl_value('hw.memsize')) / (1024**3))}GB",
            }

        # Get processor info
        is_apple_silicon = platform.processor() == "arm"
        if is_apple_silicon:
            chip_name, total_cores, performance_cores, efficiency_cores, gpu_cores = (
                self._parse_apple_silicon_info(hw_data)
            )
        else:
            # Intel Mac handling
            cpu_brand = self._get_sysctl_value("machdep.cpu.brand_string")
            chip_name = cpu_brand if cpu_brand != "Unknown" else hw_data.get("cpu_type", "Unknown")
            total_cores = int(self._get_sysctl_value("hw.ncpu"))
            performance_cores = total_cores
            efficiency_cores = 0
            gpu_cores = 0

        # Get macOS version and build
        sw_info = self._run_command(
            ["system_profiler", "SPSoftwareDataType", "-json"], privileged=True
        )

        macos_version = platform.mac_ver()[0]
        macos_build = ""
        if sw_info:
            try:
                sw_data = json.loads(sw_info).get("SPSoftwareDataType", [{}])[0]
                system_version = sw_data.get("kernel_version", "")
                if system_version:
                    macos_build = system_version.split()[-1].strip("()")
            except (json.JSONDecodeError, KeyError):
                pass

        # Get Bluetooth information
        bluetooth_chipset, bluetooth_firmware, bluetooth_transport = self._get_bluetooth_info()

        return HardwareInfo(
            model_name=hw_data.get("machine_model", "Unknown"),
            device_identifier=hw_data.get("machine_name", "Unknown"),
            model_number=hw_data.get("model_number", "Unknown"),
            serial_number=hw_data.get("serial_number", "Unknown"),
            processor=chip_name,
            cpu_cores=total_cores,
            performance_cores=performance_cores,
            efficiency_cores=efficiency_cores,
            gpu_cores=gpu_cores,
            memory=self._get_memory_info(),
            storage=self._get_storage_info(),
            graphics=self._get_graphics_info(),
            bluetooth_chipset=bluetooth_chipset,
            bluetooth_firmware=bluetooth_firmware,
            bluetooth_transport=bluetooth_transport,
            macos_version=macos_version,
            macos_build=macos_build,
            uptime=self._get_uptime(),
        )

    # Public wrapper for release date helper
    def get_release_date(self) -> Tuple[str, str, str]:
        return self._get_release_date()

    def _get_uptime(self) -> str:
        """Get system uptime in a human-readable format."""
        try:
            # Get boot time from sysctl
            boot_time = self._run_command(["sysctl", "-n", "kern.boottime"], privileged=False)
            if boot_time:
                # Extract timestamp from format like "{ sec = 1234567890, usec = 0 }"
                boot_timestamp = int(boot_time.split()[3].rstrip(","))
                current_time = int(time.time())
                uptime_seconds = current_time - boot_timestamp

                days = uptime_seconds // 86400
                uptime_seconds %= 86400
                hours = uptime_seconds // 3600
                uptime_seconds %= 3600
                minutes = uptime_seconds // 60

                parts = []
                if days > 0:
                    parts.append(f"{days} {'day' if days == 1 else 'days'}")
                if hours > 0:
                    parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
                if minutes > 0:
                    parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")

                return " ".join(parts)
        except:
            pass
        return "Unknown"

    def _get_screen_size(self, resolution: str) -> str:
        """Determine screen size from resolution."""
        if not resolution:
            return ""

        try:
            width = int(resolution.split("x")[0].strip())
            # Common MacBook resolutions to screen sizes
            resolutions = {
                3456: "16-inch",  # M1/M2/M3 Pro/Max 16"
                3024: "14-inch",  # M1/M2/M3 Pro/Max 14"
                2560: "13-inch",  # M1/M2 13"
                2880: "15-inch",  # M2 15"
                2304: "12-inch",  # 12" MacBook
                1440: "13-inch",  # Older 13" models
                1680: "13-inch",  # Older 13" models
                1920: "15-inch",  # Older 15" models
                2880: "15-inch",  # Retina 15" models
            }
            return resolutions.get(width, "")
        except (ValueError, IndexError):
            pass
        return ""

    def _get_release_date(self) -> Tuple[str, str, str]:
        """Get the release date of the machine.
        Returns:
            Tuple of (formatted_date, raw_value, key_used)
        """
        try:
            # Try different ioreg keys that might contain the release date
            ioreg_keys = [
                "product-release-date",
                "product-release",
                "product-name",
                "target-type",
            ]

            for key in ioreg_keys:
                ioreg_cmd = ["/usr/sbin/ioreg", "-ar", "-k", key]
                ioreg_output = self._run_command(ioreg_cmd, privileged=False)
                if ioreg_output:
                    plist_cmd = [
                        "/usr/libexec/PlistBuddy",
                        "-c",
                        f"print 0:{key}",
                        "/dev/stdin",
                    ]
                    try:
                        release_info = subprocess.run(
                            plist_cmd,
                            input=ioreg_output,
                            capture_output=True,
                            text=True,
                            check=True,
                        ).stdout.strip()

                        if release_info:
                            # Try different date formats

                            # Format 1: Direct date (2024-03)
                            if "-" in release_info:
                                try:
                                    date_parts = release_info.split("-")
                                    if len(date_parts) >= 2:
                                        year = date_parts[0]
                                        month = int(date_parts[1])
                                        month_names = [
                                            "",
                                            "Jan",
                                            "Feb",
                                            "Mar",
                                            "Apr",
                                            "May",
                                            "Jun",
                                            "Jul",
                                            "Aug",
                                            "Sep",
                                            "Oct",
                                            "Nov",
                                            "Dec",
                                        ]
                                        return f"{month_names[month]} {year}", release_info, key
                                except (ValueError, IndexError):
                                    pass

                            # Format 2: Marketing name with date (MacBook Pro (14-inch, 2024))
                            date_match = re.search(r"\(.*?(\d{4})\)", release_info)
                            if date_match:
                                year = date_match.group(1)
                                # For new models, assume March if no month info
                                if year == "2024":
                                    return f"Mar {year}", release_info, key
                                return year, release_info, key

                            # Format 3: Target type with date (J416c)
                            if key == "target-type" and release_info.startswith("J"):
                                # Try to get the date from system profiler as fallback
                                hw_info = self._run_command(
                                    ["system_profiler", "SPHardwareDataType", "-json"],
                                    privileged=True,
                                )
                                if hw_info:
                                    try:
                                        hw_data = json.loads(hw_info).get(
                                            "SPHardwareDataType", [{}]
                                        )[0]
                                        model_id = hw_data.get("machine_model", "")
                                        if "Mac16,6" in model_id:  # Latest model
                                            return "Mar 2024", release_info, key
                                    except (json.JSONDecodeError, KeyError):
                                        pass
                    except subprocess.CalledProcessError:
                        continue

            # If no date found, try to determine from processor info
            graphics_info = self._run_command(
                ["system_profiler", "SPDisplaysDataType"], privileged=True
            )
            if "M4" in graphics_info:
                return "Mar 2024", "Detected from M4 chip", "graphics-info"
            elif "M3" in graphics_info:
                return "Oct 2023", "Detected from M3 chip", "graphics-info"
            elif "M2" in graphics_info:
                return "Jan 2023", "Detected from M2 chip", "graphics-info"
            elif "M1" in graphics_info:
                return "Nov 2020", "Detected from M1 chip", "graphics-info"

        except Exception as e:
            logger.debug(f"Error getting release date: {e}")
        return "", "", ""

    def _get_model_info(self) -> Tuple[str, str, str]:
        """Get model name, size and year from system information."""
        model_size = ""
        model_year = ""

        # Try to get marketing name from ioreg for Apple Silicon
        if platform.processor() == "arm":
            try:
                ioreg_cmd = ["/usr/sbin/ioreg", "-ar", "-k", "product-name"]
                ioreg_output = self._run_command(ioreg_cmd, privileged=False)
                if ioreg_output:
                    plist_cmd = [
                        "/usr/libexec/PlistBuddy",
                        "-c",
                        "print 0:product-name",
                        "/dev/stdin",
                    ]
                    marketing_name = subprocess.run(
                        plist_cmd, input=ioreg_output, capture_output=True, text=True, check=True
                    ).stdout.strip()

                    if marketing_name:
                        # Parse the marketing name which is in format "MacBook Pro (14-inch, 2023)"
                        model_size_match = re.search(r"\((\d+)-inch", marketing_name)
                        year_match = re.search(r"(\d{4})\)", marketing_name)

                        if model_size_match:
                            model_size = f"{model_size_match.group(1)}-inch"
                        if year_match:
                            model_year = year_match.group(1)

            except Exception as e:
                logger.debug(f"Error getting marketing name from ioreg: {e}")

        # If we don't have the size yet, try to get it from display info
        if not model_size:
            displays_info = self._run_command(
                ["system_profiler", "SPDisplaysDataType", "-json"], privileged=True
            )
            if displays_info:
                try:
                    displays_data = json.loads(displays_info).get("SPDisplaysDataType", [])
                    for display in displays_data:
                        for screen in display.get("spdisplays_ndrvs", []):
                            resolution = screen.get("_spdisplays_pixels", "")
                            if (
                                resolution
                                and "internal"
                                in screen.get("spdisplays_connection_type", "").lower()
                            ):
                                detected_size = self._get_screen_size(resolution)
                                if detected_size:
                                    model_size = detected_size
                                break
                        if model_size:
                            break
                except (json.JSONDecodeError, KeyError):
                    pass

        # Try to get the release date first
        release_date, raw_value, key_used = self._get_release_date()
        if release_date:
            # Extract year from release date (e.g., "Mar 2024" -> "2024")
            year_match = re.search(r"20\d{2}", release_date)
            if year_match:
                model_year = year_match.group(0)

        # If we still don't have the year, try other methods
        if not model_year:
            # Try system profiler
            sw_info = self._run_command(
                ["system_profiler", "SPSoftwareDataType", "-json"], privileged=True
            )
            if sw_info:
                try:
                    sw_data = json.loads(sw_info).get("SPSoftwareDataType", [{}])[0]
                    os_version = sw_data.get("os_version", "")
                    if os_version:
                        year_match = re.search(r"202\d", os_version)
                        if year_match:
                            model_year = year_match.group(0)
                except (json.JSONDecodeError, KeyError):
                    pass

            # If still no year, try to determine from processor
            if not model_year:
                processor = self._run_command(
                    ["sysctl", "-n", "machdep.cpu.brand_string"], privileged=False
                )
                if "M4" in processor or "M4" in str(self._get_graphics_info()):
                    model_year = "2024"
                elif "M3" in processor:
                    model_year = "2023"
                elif "M2" in processor:
                    model_year = "2022"
                elif "M1" in processor:
                    model_year = "2020"

        # Set defaults if we still don't have values
        if not model_size:
            model_size = "Unknown"
        if not model_year:
            model_year = "Unknown"

        return "MacBook Pro", model_size, model_year

    def format_simple_output(self, data: Dict[str, Any]) -> str:
        """Format the output to match the simple About This Mac format."""
        if "hardware" not in data:
            return "No hardware information available"

        hw = data["hardware"]

        # Format model name nicely
        _, model_size, _ = self._get_model_info()  # Don't use the year from here

        # Get the release date
        release_date, raw_value, key_used = self._get_release_date()

        # Construct the full model name
        model_name = "MacBook Pro"

        # Format the size and date line
        if release_date:
            size_date = f"{model_size}, {release_date}"
        else:
            size_date = model_size

        # Format memory size
        memory_size = hw["memory"]["total"].replace("GB", " GB")

        # Get storage name (usually "Macintosh HD" for boot drive)
        storage_name = "Macintosh HD"  # Use exact name from screenshot

        # Format macOS version (e.g., "Sequoia 15.3" instead of just "15.3")
        macos_version = hw["macos_version"]
        if macos_version.startswith("15"):
            macos_version = f"Sequoia {macos_version}"
        elif macos_version.startswith("14"):
            macos_version = f"Sonoma {macos_version}"
        elif macos_version.startswith("13"):
            macos_version = f"Ventura {macos_version}"
        elif macos_version.startswith("12"):
            macos_version = f"Monterey {macos_version}"
        elif macos_version.startswith("11"):
            macos_version = f"Big Sur {macos_version}"

        # Clean up processor name
        chip_name = hw["processor"].replace(":", "").strip()
        if not chip_name:
            # Try to determine from graphics info
            graphics = str(hw["graphics"])
            for i in range(1, 5):
                if f"M{i}" in graphics:
                    variants = ["", "Pro", "Max", "Ultra"]
                    for variant in variants:
                        variant_name = f"M{i} {variant}".strip()
                        if variant_name in graphics:
                            chip_name = f"Apple {variant_name}"
                            break
                    break

        output = [
            model_name,
            size_date,
            "",
            f"Chip          {chip_name}",
            f"Memory        {memory_size}",
            f"Startup disk  {storage_name}",
            f"Serial number {hw['serial_number']}",
            f"macOS         {macos_version}",
        ]

        return "\n".join(output)

    def format_public_output(self, data: Dict[str, Any]) -> str:
        """Format the output in a public-friendly way, suitable for sales listings."""
        if "hardware" not in data:
            return "No hardware information available"

        hw = data["hardware"]

        # Format model name nicely
        _, model_size, model_year = self._get_model_info()

        # Get release date
        release_date, _, _ = self._get_release_date()

        # Clean up processor name
        processor = hw["processor"].replace(":", "").strip()
        if "M2" in processor:
            # Format: "M2 Max 12-Core (Early 2023) 30-Core GPU"
            gpu_cores = f"{hw['gpu_cores']}-Core GPU" if hw["gpu_cores"] > 0 else ""
            processor = (
                f"{processor} {hw['cpu_cores']}-Core (Early {model_year}) {gpu_cores}".strip()
            )

        # Format storage size
        storage_size = hw["storage"]["size"]
        if isinstance(storage_size, str) and "GB" in storage_size:
            storage_size = storage_size.replace("GB", "").strip()
            storage_size = (
                f"{int(storage_size) // 1024} TB"
                if int(storage_size) >= 1024
                else f"{storage_size} GB"
            )

        # Format memory
        memory = hw["memory"]["total"].replace("GB", " GB")

        output = [
            "# Device",
            "MacBook",
            "",
            "# Model",
            f"{model_size} MacBook Pro Retina",
            "",
            "# Release Date",
            release_date if release_date else f"Released in {model_year}",
            "",
            "# Processor",
            processor,
            "",
            "# Hard Drive",
            f"{storage_size} SSD",
            "",
            "# Memory",
            memory,
        ]

        return "\n".join(output)
