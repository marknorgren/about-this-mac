#!/usr/bin/env python3

import argparse
import json
import logging
import os
import platform
import subprocess
import sys
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Optional, Any
import time
import re

__version__ = "0.1.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BatteryInfo:
    current_charge: str
    health_percentage: float
    full_charge_capacity: str
    design_capacity: str
    manufacture_date: str
    cycle_count: int
    temperature: float
    charging_power: float
    low_power_mode: bool

@dataclass
class MemoryInfo:
    total: str
    type: str
    speed: str
    manufacturer: str
    ecc: bool

@dataclass
class StorageInfo:
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
    graphics: list[dict]
    bluetooth_chipset: str
    bluetooth_firmware: str
    bluetooth_transport: str
    macos_version: str
    macos_build: str
    uptime: str

class MacInfoGatherer:
    def __init__(self, verbose: bool = False):
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        if not sys.platform.startswith('darwin'):
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

    def _run_command(self, command: list[str], privileged: bool = True) -> str:
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

    def get_battery_info(self) -> Optional[BatteryInfo]:
        """Gather battery information using system_profiler."""
        try:
            battery_info = self._run_command([
                'system_profiler', 'SPPowerDataType', '-json'
            ])
            
            if not battery_info:
                # Try pmset as fallback for basic battery info
                pmset_info = self._run_command(['pmset', '-g', 'batt'], privileged=False)
                if pmset_info and 'InternalBattery' in pmset_info:
                    # Parse pmset output for basic battery info
                    lines = pmset_info.split('\n')
                    for line in lines:
                        if 'InternalBattery' in line:
                            try:
                                charge = line.split('\t')[1].split(';')[0].strip()
                                return BatteryInfo(
                                    current_charge=charge,
                                    health_percentage=0.0,
                                    full_charge_capacity="Unknown",
                                    design_capacity="Unknown",
                                    manufacture_date="Unknown",
                                    cycle_count=0,
                                    temperature=0.0,
                                    charging_power=0.0,
                                    low_power_mode=False
                                )
                            except:
                                pass
                logger.warning("No battery found or insufficient permissions")
                return None
            
            data = json.loads(battery_info)
            power_data = data.get('SPPowerDataType', [{}])[0]
            battery_data = next(
                (item for item in power_data.get('sppower_battery_info', [])
                 if isinstance(item, dict)), 
                {}
            )
            
            if not battery_data:
                logger.warning("No battery found - device might be a desktop Mac")
                return None
            
            return BatteryInfo(
                current_charge=battery_data.get('sppower_battery_charge_info', 'Unknown'),
                health_percentage=float(battery_data.get('sppower_battery_health_info', '0').rstrip('%')),
                full_charge_capacity=battery_data.get('sppower_battery_full_charge_capacity', 'Unknown'),
                design_capacity=battery_data.get('sppower_battery_design_capacity', 'Unknown'),
                manufacture_date=battery_data.get('sppower_battery_manufacture_date', 'Unknown'),
                cycle_count=int(battery_data.get('sppower_battery_cycle_count', '0')),
                temperature=float(battery_data.get('sppower_battery_temperature', '0')),
                charging_power=float(battery_data.get('sppower_battery_charging_power', '0')),
                low_power_mode=bool(battery_data.get('sppower_battery_low_power_mode', False))
            )
        except Exception as e:
            logger.error(f"Error getting battery info: {e}")
            return None

    def _parse_apple_silicon_info(self, hw_data: dict) -> tuple[str, int, int, int, int]:
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

    def _get_graphics_info(self) -> list[dict]:
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

        # Get storage info
        storage_info = self._run_command(['df', '-h', '/'], privileged=False)
        storage_lines = storage_info.split('\n')
        if len(storage_lines) >= 2:
            _, total, used, available, *_ = storage_lines[1].split()
        else:
            total, available = "Unknown", "Unknown"

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

def format_output(data: Dict[str, Any], format_type: str) -> str:
    """Format the output according to the specified format."""
    if format_type == 'json':
        return json.dumps(data, indent=2)
    elif format_type == 'yaml':
        return yaml.dump(data, sort_keys=False)
    elif format_type == 'markdown':
        output = []
        
        # Add title and timestamp
        output.extend([
            "# Mac System Information",
            "",
            f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ""
        ])
        
        # Hardware section
        if 'hardware' in data:
            hw = data['hardware']
            output.extend([
                "## Hardware Information",
                "",
                "### System",
                f"- **Model:** {hw['model_name']}",
                f"- **Identifier:** {hw['device_identifier']}",
                f"- **Model Number:** {hw['model_number']}",
                f"- **Serial Number:** {hw['serial_number']}",
                "",
                "### Processor",
                f"- **Chip:** {hw['processor']}",
                f"- **CPU Cores:** {hw['cpu_cores']} ({hw['performance_cores']} performance and {hw['efficiency_cores']} efficiency)",
                f"- **GPU Cores:** {hw['gpu_cores']}",
                "",
                "### Memory",
                f"- **Total:** {hw['memory']['total']}",
                f"- **Type:** {hw['memory']['type']}",
                f"- **Speed:** {hw['memory']['speed']}",
                f"- **Manufacturer:** {hw['memory']['manufacturer']}",
                f"- **ECC:** {'Yes' if hw['memory']['ecc'] else 'No'}",
                "",
                "### Storage",
                f"- **Model:** {hw['storage']['model']}",
                f"- **Type:** {hw['storage']['type']}",
                f"- **Protocol:** {hw['storage']['protocol']}",
                f"- **Size:** {hw['storage']['size']}",
                f"- **SMART Status:** {hw['storage']['smart_status']}",
                f"- **TRIM Support:** {'Yes' if hw['storage']['trim'] else 'No'}",
                f"- **Internal:** {'Yes' if hw['storage']['internal'] else 'No'}",
                "",
                "### Graphics"
            ])
            
            # Add graphics cards
            if hw['graphics']:
                for i, card in enumerate(hw['graphics'], 1):
                    output.append(f"#### Card {i}")
                    if card['name']:
                        output.append(f"- **Model:** {card['name']}")
                    if card['vendor']:
                        output.append(f"- **Vendor:** {card['vendor']}")
                    if card['vram']:
                        output.append(f"- **VRAM:** {card['vram']}")
                    if card['resolution']:
                        output.append(f"- **Resolution:** {card['resolution']}")
                    if card['metal']:
                        output.append(f"- **Metal Support:** {card['metal']}")
                    output.append("")
            else:
                output.append("*No graphics cards detected*\n")
            
            output.extend([
                "### Wireless",
                f"- **Bluetooth:** {hw['bluetooth_chipset']} ({hw['bluetooth_firmware']}) via {hw['bluetooth_transport']}",
                "",
                "### System Software",
                f"- **macOS Version:** {hw['macos_version']}",
                f"- **Build:** {hw['macos_build']}",
                f"- **Uptime:** {hw['uptime']}"
            ])
        
        # Battery section if available
        if 'battery' in data:
            bat = data['battery']
            output.extend([
                "",
                "## Battery Information",
                "",
                f"- **Current Charge:** {bat['current_charge']}",
                f"- **Health:** {bat['health_percentage']}%",
                f"- **Full Charge Capacity:** {bat['full_charge_capacity']}",
                f"- **Design Capacity:** {bat['design_capacity']}",
                f"- **Manufacture Date:** {bat['manufacture_date']}",
                f"- **Cycle Count:** {bat['cycle_count']}",
                f"- **Temperature:** {bat['temperature']}°C",
                f"- **Charging Power:** {bat['charging_power']} Watts",
                f"- **Low Power Mode:** {'Enabled' if bat['low_power_mode'] else 'Disabled'}"
            ])
            
        return '\n'.join(output)
    else:  # text format
        output = []
        
        # Hardware section first
        if 'hardware' in data:
            hw = data['hardware']
            output.extend([
                "\nHARDWARE INFORMATION",
                "===================",
                f"Model: {hw['model_name']}",
                f"Identifier: {hw['device_identifier']}",
                f"Model Number: {hw['model_number']}",
                f"Serial Number: {hw['serial_number']}",
                "",
                "Processor",
                "---------",
                hw['processor'],
                f"CPU Cores: {hw['cpu_cores']} ({hw['performance_cores']} performance and {hw['efficiency_cores']} efficiency)",
                f"GPU Cores: {hw['gpu_cores']}",
                "",
                "Memory",
                "------",
                f"Total: {hw['memory']['total']}",
                f"Type: {hw['memory']['type']}",
                f"Speed: {hw['memory']['speed']}",
                f"Manufacturer: {hw['memory']['manufacturer']}",
                f"ECC: {'Yes' if hw['memory']['ecc'] else 'No'}",
                "",
                "Storage",
                "-------",
                f"Model: {hw['storage']['model']}",
                f"Type: {hw['storage']['type']}",
                f"Protocol: {hw['storage']['protocol']}",
                f"Size: {hw['storage']['size']}",
                f"SMART Status: {hw['storage']['smart_status']}",
                f"TRIM Support: {'Yes' if hw['storage']['trim'] else 'No'}",
                f"Internal: {'Yes' if hw['storage']['internal'] else 'No'}",
                "",
                "Graphics",
                "--------"
            ])
            
            # Add graphics cards
            if hw['graphics']:
                for i, card in enumerate(hw['graphics'], 1):
                    card_info = [f"Card {i}:"]
                    if card['name']:
                        card_info.append(f"  Model: {card['name']}")
                    if card['vendor']:
                        card_info.append(f"  Vendor: {card['vendor']}")
                    if card['vram']:
                        card_info.append(f"  VRAM: {card['vram']}")
                    if card['resolution']:
                        card_info.append(f"  Resolution: {card['resolution']}")
                    if card['metal']:
                        card_info.append(f"  Metal Support: {card['metal']}")
                    output.extend(card_info)
            else:
                output.append("No graphics cards detected")
            
            output.extend([
                "",
                "Wireless",
                "--------",
                f"Bluetooth: {hw['bluetooth_chipset']} ({hw['bluetooth_firmware']}) via {hw['bluetooth_transport']}",
                "",
                "System",
                "------",
                f"macOS Version: {hw['macos_version']}",
                f"Build: {hw['macos_build']}",
                f"Uptime: {hw['uptime']}"
            ])
        
        # Battery section if available
        if 'battery' in data:
            bat = data['battery']
            output.extend([
                "\nBATTERY INFORMATION",
                "==================",
                f"Current Charge: {bat['current_charge']}",
                f"Health: {bat['health_percentage']}%",
                f"Full Charge Capacity: {bat['full_charge_capacity']}",
                f"Design Capacity: {bat['design_capacity']}",
                f"Manufacture Date: {bat['manufacture_date']}",
                f"Cycle Count: {bat['cycle_count']}",
                f"Temperature: {bat['temperature']}°C",
                f"Charging Power: {bat['charging_power']} Watts",
                f"Low Power Mode: {'Enabled' if bat['low_power_mode'] else 'Disabled'}"
            ])
            
        return '\n'.join(output)

def main():
    parser = argparse.ArgumentParser(
        description='Gather detailed information about your Mac.'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'yaml', 'markdown'],
        default='text',
        help='Output format'
    )
    parser.add_argument(
        '--section',
        choices=['hardware', 'battery', 'all'],
        default='all',
        help='Information section to display'
    )
    parser.add_argument(
        '--output',
        help='Save output to file (default: auto-generate filename for markdown)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed debug information'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    # Add raw data mode arguments
    parser.add_argument(
        '--hardware-info',
        action='store_true',
        help='Show raw hardware information from system_profiler SPHardwareDataType'
    )
    parser.add_argument(
        '--power-info',
        action='store_true',
        help='Show raw power information from system_profiler SPPowerDataType'
    )
    parser.add_argument(
        '--graphics-info',
        action='store_true',
        help='Show raw graphics information from system_profiler SPDisplaysDataType'
    )
    parser.add_argument(
        '--storage-info',
        action='store_true',
        help='Show raw storage information from system_profiler SP{NVMe,SerialATA,Storage}DataType'
    )
    parser.add_argument(
        '--memory-info',
        action='store_true',
        help='Show raw memory information from system_profiler SPMemoryDataType'
    )
    parser.add_argument(
        '--audio-info',
        action='store_true',
        help='Show raw audio information from system_profiler SPAudioDataType'
    )
    parser.add_argument(
        '--network-info',
        action='store_true',
        help='Show raw network information from system_profiler SPNetworkDataType'
    )

    args = parser.parse_args()

    try:
        gatherer = MacInfoGatherer(verbose=args.verbose)
        
        # Handle raw data mode requests
        if any([args.hardware_info, args.power_info, args.graphics_info,
                args.storage_info, args.memory_info, args.audio_info,
                args.network_info]):
            raw_data = []
            
            if args.hardware_info:
                raw_data.extend([
                    "\nHardware Information (system_profiler SPHardwareDataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPHardwareDataType']),
                    "\nCPU Information (sysctl):",
                    "=" * 60,
                    f"hw.model: {gatherer._get_sysctl_value('hw.model')}",
                    f"hw.ncpu: {gatherer._get_sysctl_value('hw.ncpu')}",
                    f"machdep.cpu.brand_string: {gatherer._get_sysctl_value('machdep.cpu.brand_string')}"
                ])
            
            if args.power_info:
                raw_data.extend([
                    "\nPower Information (system_profiler SPPowerDataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPPowerDataType']),
                    "\nBattery Status (pmset):",
                    "=" * 60,
                    gatherer._run_command(['pmset', '-g', 'batt'], privileged=False)
                ])
            
            if args.graphics_info:
                raw_data.extend([
                    "\nGraphics Information (system_profiler SPDisplaysDataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPDisplaysDataType'])
                ])
            
            if args.storage_info:
                raw_data.extend([
                    "\nNVMe Storage Information (system_profiler SPNVMeDataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPNVMeDataType']),
                    "\nSATA Storage Information (system_profiler SPSerialATADataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPSerialATADataType']),
                    "\nGeneral Storage Information (system_profiler SPStorageDataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPStorageDataType'])
                ])
            
            if args.memory_info:
                raw_data.extend([
                    "\nMemory Information (system_profiler SPMemoryDataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPMemoryDataType']),
                    "\nMemory Size (sysctl):",
                    "=" * 60,
                    f"hw.memsize: {gatherer._get_sysctl_value('hw.memsize')}"
                ])
            
            if args.audio_info:
                raw_data.extend([
                    "\nAudio Information (system_profiler SPAudioDataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPAudioDataType'])
                ])
            
            if args.network_info:
                raw_data.extend([
                    "\nNetwork Interfaces (networksetup):",
                    "=" * 60,
                    gatherer._run_command(['networksetup', '-listallhardwareports'], privileged=False),
                    "\nNetwork Status (netstat):",
                    "=" * 60,
                    gatherer._run_command(['netstat', '-i'], privileged=False),
                    "\nBluetooth Information (system_profiler SPBluetoothDataType):",
                    "=" * 60,
                    gatherer._run_command(['system_profiler', 'SPBluetoothDataType'])
                ])
            
            print('\n'.join(raw_data))
            return
        
        # Gather information based on requested section
        data = {}
        if args.section in ['hardware', 'all']:
            data['hardware'] = asdict(gatherer.get_hardware_info())
        if args.section in ['battery', 'all']:
            battery_info = gatherer.get_battery_info()
            if battery_info:
                data['battery'] = asdict(battery_info)

        # Format the output
        output = format_output(data, args.format)

        # Handle output
        if args.output or args.format == 'markdown':
            output_file = args.output
            if not output_file and args.format == 'markdown':
                # Generate default filename for markdown
                model_name = data['hardware']['model_name'].replace(' ', '-').lower()
                date_str = datetime.now().strftime('%Y-%m-%d')
                output_file = f"mac-info-{model_name}-{date_str}.md"
            
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"Output saved to {output_file}")
        else:
            print(output)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 