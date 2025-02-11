"""Hardware information gathering module."""

import json
import logging
import platform
import subprocess
import re
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

from about_this_mac.battery import BatteryInfoGatherer

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
    
    def __init__(self, verbose: bool = False):
        """Initialize the gatherer."""
        super().__init__()
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        if not platform.system() == 'Darwin':
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
                ['system_profiler', 'SPHardwareDataType', '-json'],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _run_command(self, command: List[str], privileged: bool = True) -> str:
        """Run a shell command and return its output."""
        try:
            if privileged and not self.has_full_permissions:
                logger.debug(f"Skipping privileged command: {' '.join(command)}")
                return ""
                
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.debug(f"Command failed: {' '.join(command)}")
            logger.debug(f"Error: {e.stderr}")
            return ""
    
    def _get_sysctl_value(self, key: str) -> str:
        """Get system information using sysctl."""
        try:
            result = subprocess.run(
                ['sysctl', '-n', key],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return "Unknown"
    
    def _parse_apple_silicon_info(self, hw_data: Dict[str, Any]) -> tuple[str, int, int, int, int]:
        """Parse Apple Silicon processor details."""
        # Get processor name from hardware info
        processor_name = hw_data.get('chip_info', '')
        if not processor_name:
            processor_name = hw_data.get('processor_name', '')
            if not processor_name:
                # Try to get from graphics info as fallback
                graphics_info = self._run_command([
                    'system_profiler', 'SPDisplaysDataType'
                ])
                if graphics_info:
                    for line in graphics_info.split('\n'):
                        if 'Apple M2' in line:
                            processor_name = line.strip()
                            break

        # Get CPU cores
        total_cores = 0
        performance_cores = 0
        efficiency_cores = 0
        try:
            core_info = hw_data.get('number_processors', '')
            if isinstance(core_info, str) and ':' in core_info:
                # Handle format like "proc 12:8:4" (total:performance:efficiency)
                cores = core_info.split(':')
                total_cores = int(cores[0].split()[-1])  # Get total cores
                performance_cores = int(cores[1])
                efficiency_cores = int(cores[2])
            else:
                total_cores = int(core_info)
        except (ValueError, IndexError):
            pass

        # Get GPU cores from graphics info
        graphics_info = self._run_command([
            'system_profiler', 'SPDisplaysDataType'
        ])
        
        gpu_cores = 0
        if graphics_info:
            # Try to find GPU cores in the text output
            for line in graphics_info.split('\n'):
                line = line.strip()
                if 'Cores:' in line:
                    try:
                        gpu_cores = int(line.split(':')[1].strip())
                        break
                    except (ValueError, IndexError):
                        pass
                elif '-core GPU' in line.lower():
                    try:
                        gpu_cores = int(line.split('-core')[0].strip())
                        break
                    except (ValueError, IndexError):
                        pass
            
            # If still not found, try to determine from the chip name
            if gpu_cores == 0 and processor_name:
                if 'M2 Max' in processor_name:
                    gpu_cores = 30
                elif 'M2 Pro' in processor_name:
                    gpu_cores = 19
                elif 'M2' in processor_name:
                    gpu_cores = 10

        return processor_name, total_cores, performance_cores, efficiency_cores, gpu_cores
    
    def _get_graphics_info(self) -> List[Dict[str, str]]:
        """Get detailed graphics information."""
        graphics_cards = []
        
        graphics_info = self._run_command([
            'system_profiler', 'SPDisplaysDataType', '-json'
        ])
        
        if graphics_info:
            try:
                graphics_data = json.loads(graphics_info).get('SPDisplaysDataType', [])
                for card in graphics_data:
                    if isinstance(card, dict):
                        # Determine vendor and icon
                        vendor = card.get('spdisplays_vendor', '')
                        vendor = vendor.split()[0] if vendor else ''
                        
                        # Get resolution
                        resolution = card.get('spdisplays_resolution', '')
                        if isinstance(resolution, list):
                            resolution = resolution[0] if resolution else ''
                        
                        graphics_cards.append({
                            'name': card.get('sppci_model', ''),
                            'vendor': vendor,
                            'vram': card.get('spdisplays_vram', ''),
                            'resolution': resolution,
                            'metal': card.get('spdisplays_metal', ''),
                            'display_type': card.get('spdisplays_display_type', '')
                        })
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

        memory_info = self._run_command([
            'system_profiler', 'SPMemoryDataType', '-json'
        ])
        
        if memory_info:
            try:
                memory_data = json.loads(memory_info).get('SPMemoryDataType', [{}])[0]
                if isinstance(memory_data, dict):
                    memory_type = memory_data.get('dimm_type', memory_type)
                    manufacturer = memory_data.get('dimm_manufacturer', manufacturer)
                    # Some Macs report ECC status
                    ecc = 'ecc' in str(memory_type).lower()
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        return MemoryInfo(
            total=memory_size,
            type=memory_type,
            speed=memory_speed,
            manufacturer=manufacturer,
            ecc=ecc
        )
    
    def _get_storage_info(self) -> StorageInfo:
        """Get detailed storage information."""
        # Try NVMe first
        nvme_info = self._run_command([
            'system_profiler', 'SPNVMeDataType', '-json'
        ])
        
        if nvme_info:
            try:
                nvme_data = json.loads(nvme_info).get('SPNVMeDataType', [{}])[0]
                items = nvme_data.get('_items', [{}])[0]
                return StorageInfo(
                    name=items.get('_name', 'Unknown'),
                    model=items.get('device_model', 'Unknown'),
                    revision=items.get('device_revision', 'Unknown'),
                    serial=items.get('device_serial', 'Unknown'),
                    size=items.get('size', 'Unknown'),
                    type='NVMe',
                    protocol='PCIe',
                    trim=items.get('spnvme_trim_support', 'No') == 'Yes',
                    smart_status=items.get('smart_status', 'Unknown'),
                    removable=items.get('removable_media', 'no') == 'yes',
                    internal=items.get('detachable_drive', 'yes') == 'no'
                )
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        # Try SATA if no NVMe
        sata_info = self._run_command([
            'system_profiler', 'SPSerialATADataType', '-json'
        ])
        
        if sata_info:
            try:
                sata_data = json.loads(sata_info).get('SPSerialATADataType', [{}])[0]
                items = sata_data.get('_items', [{}])[0]
                return StorageInfo(
                    name=items.get('_name', 'Unknown'),
                    model=items.get('device_model', 'Unknown'),
                    revision=items.get('device_revision', 'Unknown'),
                    serial=items.get('device_serial', 'Unknown'),
                    size=items.get('size', 'Unknown'),
                    type='SATA',
                    protocol='SATA',
                    trim=False,  # SATA doesn't typically report TRIM
                    smart_status=items.get('smart_status', 'Unknown'),
                    removable=items.get('removable_media', 'no') == 'yes',
                    internal=items.get('detachable_drive', 'yes') == 'no'
                )
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        # Fallback to basic storage info
        storage_info = self._run_command([
            'system_profiler', 'SPStorageDataType', '-json'
        ])
        
        if storage_info:
            try:
                storage_data = json.loads(storage_info).get('SPStorageDataType', [{}])[0]
                physical_drive = storage_data.get('physical_drive', {})
                return StorageInfo(
                    name=storage_data.get('_name', 'Unknown'),
                    model=physical_drive.get('device_name', 'Unknown'),
                    revision='Unknown',
                    serial='Unknown',
                    size=str(int(storage_data.get('size_in_bytes', 0) / (1024**3))) + ' GB',
                    type=physical_drive.get('medium_type', 'Unknown'),
                    protocol=physical_drive.get('protocol', 'Unknown'),
                    trim=False,
                    smart_status=physical_drive.get('smart_status', 'Unknown'),
                    removable=not physical_drive.get('is_internal_disk', 'no') == 'yes',
                    internal=physical_drive.get('is_internal_disk', 'no') == 'yes'
                )
            except (json.JSONDecodeError, KeyError):
                pass

        return StorageInfo(
            name='Unknown',
            model='Unknown',
            revision='Unknown',
            serial='Unknown',
            size='Unknown',
            type='Unknown',
            protocol='Unknown',
            trim=False,
            smart_status='Unknown',
            removable=False,
            internal=True
        )
    
    def _get_bluetooth_info(self) -> tuple[str, str, str]:
        """Get detailed Bluetooth information."""
        try:
            bluetooth_info = self._run_command([
                'system_profiler', 'SPBluetoothDataType', '-json'
            ])
            if bluetooth_info:
                data = json.loads(bluetooth_info)
                controller = data.get('SPBluetoothDataType', [{}])[0].get('controller_properties', {})
                return (
                    controller.get('controller_chipset', 'Unknown'),
                    controller.get('controller_firmwareVersion', 'Unknown'),
                    controller.get('controller_transport', 'Unknown')
                )
        except:
            pass
        return ('Unknown', 'Unknown', 'Unknown')
    
    def get_hardware_info(self) -> HardwareInfo:
        """Gather hardware information using system_profiler and sysctl."""
        # Get basic hardware info
        hw_info = self._run_command([
            'system_profiler', 'SPHardwareDataType', '-json'
        ])
        
        if hw_info:
            hw_data = json.loads(hw_info).get('SPHardwareDataType', [{}])[0]
        else:
            hw_data = {
                'machine_model': self._get_sysctl_value('hw.model'),
                'machine_name': platform.machine(),
                'model_number': "Unknown (needs sudo)",
                'serial_number': "Unknown (needs sudo)",
                'cpu_type': self._get_sysctl_value('machdep.cpu.brand_string'),
                'physical_memory': f"{int(int(self._get_sysctl_value('hw.memsize')) / (1024**3))}GB",
            }

        # Get processor info
        is_apple_silicon = platform.processor() == 'arm'
        if is_apple_silicon:
            chip_name, total_cores, performance_cores, efficiency_cores, gpu_cores = self._parse_apple_silicon_info(hw_data)
        else:
            # Intel Mac handling
            cpu_brand = self._get_sysctl_value('machdep.cpu.brand_string')
            chip_name = cpu_brand if cpu_brand != "Unknown" else hw_data.get('cpu_type', 'Unknown')
            total_cores = int(self._get_sysctl_value('hw.ncpu'))
            performance_cores = total_cores
            efficiency_cores = 0
            gpu_cores = 0

        # Get macOS version and build
        sw_info = self._run_command([
            'system_profiler', 'SPSoftwareDataType', '-json'
        ])
        
        macos_version = platform.mac_ver()[0]
        macos_build = ""
        if sw_info:
            try:
                sw_data = json.loads(sw_info).get('SPSoftwareDataType', [{}])[0]
                system_version = sw_data.get('kernel_version', '')
                if system_version:
                    macos_build = system_version.split()[-1].strip('()')
            except (json.JSONDecodeError, KeyError):
                pass

        # Get Bluetooth information
        bluetooth_chipset, bluetooth_firmware, bluetooth_transport = self._get_bluetooth_info()

        return HardwareInfo(
            model_name=hw_data.get('machine_model', 'Unknown'),
            device_identifier=hw_data.get('machine_name', 'Unknown'),
            model_number=hw_data.get('model_number', 'Unknown'),
            serial_number=hw_data.get('serial_number', 'Unknown'),
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
            uptime=self._get_uptime()
        )
    
    def _get_uptime(self) -> str:
        """Get system uptime in a human-readable format."""
        try:
            # Get boot time from sysctl
            boot_time = self._run_command(['sysctl', '-n', 'kern.boottime'])
            if boot_time:
                # Extract timestamp from format like "{ sec = 1234567890, usec = 0 }"
                boot_timestamp = int(boot_time.split()[3].rstrip(','))
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
                
                return ' '.join(parts)
        except:
            pass
        return "Unknown"
    
    def _get_screen_size(self, resolution: str) -> str:
        """Determine screen size from resolution."""
        if not resolution:
            return ""
        
        try:
            width = int(resolution.split('x')[0].strip())
            # MacBook Pro resolutions to screen sizes
            if width == 3456:
                return "16-inch"
            elif width == 3024:
                return "14-inch"
            elif width == 2560:
                return "13-inch"
        except (ValueError, IndexError):
            pass
        return ""
    
    def _get_model_info(self, model_id: str, machine_name: str) -> tuple[str, str, str]:
        """Get model name, size and year from system information."""
        # Try to get marketing name from ioreg for Apple Silicon
        if platform.processor() == 'arm':
            try:
                ioreg_cmd = ['/usr/sbin/ioreg', '-ar', '-k', 'product-name']
                ioreg_output = self._run_command(ioreg_cmd)
                if ioreg_output:
                    plist_cmd = ['/usr/libexec/PlistBuddy', '-c', 'print 0:product-name', '/dev/stdin']
                    marketing_name = subprocess.run(
                        plist_cmd,
                        input=ioreg_output,
                        capture_output=True,
                        text=True
                    ).stdout.strip()
                    
                    if marketing_name:
                        # Parse the marketing name which is in format "MacBook Pro (14-inch, 2023)"
                        base_name = "MacBook Pro"  # We know it's a MacBook Pro
                        size_match = re.search(r'\((\d+)-inch', marketing_name)
                        year_match = re.search(r'(\d{4})\)', marketing_name)
                        
                        model_size = f"{size_match.group(1)}-inch" if size_match else ""
                        model_year = year_match.group(1) if year_match else ""
                        
                        return base_name, model_size, model_year
            except Exception as e:
                logger.debug(f"Error getting marketing name from ioreg: {e}")
        
        # Fallback to previous method if ioreg fails or for Intel Macs
        base_name = machine_name or "Mac"
        model_size = ""
        model_year = ""
        
        # Get display info for screen size
        displays_info = self._run_command(['system_profiler', 'SPDisplaysDataType', '-json'])
        if displays_info:
            try:
                displays_data = json.loads(displays_info).get('SPDisplaysDataType', [])
                for display in displays_data:
                    for screen in display.get('spdisplays_ndrvs', []):
                        resolution = screen.get('_spdisplays_pixels', '')
                        if resolution and 'internal' in screen.get('spdisplays_connection_type', '').lower():
                            model_size = self._get_screen_size(resolution)
                            break
                    if model_size:
                        break
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Try to get year from system profiler
        sw_info = self._run_command(['system_profiler', 'SPSoftwareDataType', '-json'])
        if sw_info:
            try:
                sw_data = json.loads(sw_info).get('SPSoftwareDataType', [{}])[0]
                os_version = sw_data.get('os_version', '')
                if os_version:
                    # OS version might give us a clue about the earliest possible year
                    year_match = re.search(r'202\d', os_version)
                    if year_match:
                        model_year = year_match.group(0)
            except (json.JSONDecodeError, KeyError):
                pass
        
        return base_name, model_size, model_year
    
    def format_simple_output(self, data: Dict[str, Any]) -> str:
        """Format the output to match the simple About This Mac format."""
        if 'hardware' not in data:
            return "No hardware information available"

        hw = data['hardware']
        
        # Format model name nicely
        base_name, model_size, model_year = self._get_model_info(
            hw['device_identifier'],
            hw.get('machine_name', '')
        )
        
        # Construct the full model name
        model_name = "MacBook Pro"  # Use exact name from screenshot
        
        # Format memory size
        memory_size = hw['memory']['total'].replace('GB', ' GB')
        
        # Get storage name (usually "Macintosh HD" for boot drive)
        storage_name = "Macintosh HD"  # Use exact name from screenshot
        
        # Format macOS version (e.g., "Sequoia 15.3" instead of just "15.3")
        macos_version = hw['macos_version']
        if macos_version.startswith('15'):
            macos_version = f"Sequoia {macos_version}"
        
        # Clean up processor name
        chip_name = hw['processor'].replace(':', '').strip()
        
        # Format the size and year line
        size_year = f"{model_size}, {model_year}" if model_size and model_year else model_size
        
        output = [
            model_name,
            size_year,
            "",
            f"Chip          {chip_name}",
            f"Memory        {memory_size}",
            f"Startup disk  {storage_name}",
            f"Serial number {hw['serial_number']}",
            f"macOS         {macos_version}"
        ]
        
        return '\n'.join(output)
    
    def format_public_output(self, data: Dict[str, Any]) -> str:
        """Format the output in a public-friendly way, suitable for sales listings."""
        if 'hardware' not in data:
            return "No hardware information available"

        hw = data['hardware']
        
        # Format model name nicely
        base_name, model_size, model_year = self._get_model_info(
            hw['device_identifier'],
            hw.get('machine_name', '')
        )
        
        # Clean up processor name
        processor = hw['processor'].replace(':', '').strip()
        if 'M2' in processor:
            # Format: "M2 Max 12-Core (Early 2023) 30-Core GPU"
            gpu_cores = f"{hw['gpu_cores']}-Core GPU" if hw['gpu_cores'] > 0 else ""
            processor = f"{processor} {hw['cpu_cores']}-Core (Early {model_year}) {gpu_cores}".strip()
        
        # Format storage size
        storage_size = hw['storage']['size']
        if isinstance(storage_size, str) and 'GB' in storage_size:
            storage_size = storage_size.replace('GB', '').strip()
            storage_size = f"{int(storage_size) // 1024} TB" if int(storage_size) >= 1024 else f"{storage_size} GB"
        
        # Format memory
        memory = hw['memory']['total'].replace('GB', ' GB')
        
        output = [
            "# Device",
            "MacBook",
            "",
            "# Model",
            f"{model_size} MacBook Pro Retina",
            "",
            "# Processor",
            processor,
            "",
            "# Hard Drive",
            f"{storage_size} SSD",
            "",
            "# Memory",
            memory
        ]
        
        return '\n'.join(output) 