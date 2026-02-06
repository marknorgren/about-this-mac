"""Battery information gathering module."""

import re
import logging
from dataclasses import dataclass
from typing import Optional, List

from about_this_mac.utils.command import run_command_result

logger = logging.getLogger(__name__)


@dataclass
class BatteryInfo:
    """Data class for battery information."""

    current_charge: str
    health_percentage: float
    full_charge_capacity: str
    design_capacity: str
    manufacture_date: str
    cycle_count: int
    temperature_celsius: float
    temperature_fahrenheit: float
    charging_power: float
    low_power_mode: bool


class BatteryInfoGatherer:
    """Class for gathering battery information from the system."""

    def _run_command(self, command: List[str]) -> str:
        """Run a shell command and return its output."""
        result = run_command_result(command, check=False)
        if result.ok:
            return result.stdout
        logger.debug("Command failed (exit %s): %s", result.returncode, " ".join(result.command))
        if result.stderr:
            logger.debug("Command stderr: %s", result.stderr)
        return ""

    def _get_value(
        self, key: str, ioreg_output: str, default: Optional[int] = None
    ) -> Optional[int]:
        """Extract a value from ioreg output."""
        match = re.search(rf'"{key}"\s*=\s*(\d+)', ioreg_output)
        if not match:
            # Try hex value
            match = re.search(rf'"{key}"\s*=\s*<([^>]+)>', ioreg_output)
            if match:
                try:
                    # Convert hex string to integer
                    hex_str = match.group(1).replace(" ", "")
                    return int(hex_str, 16)
                except ValueError:
                    return default
        return int(match.group(1)) if match else default

    def _parse_manufacture_date(self, ioreg_output: str) -> str:
        """Parse manufacture date from battery data."""
        try:
            mfg_data_match = re.search(r'"ManufactureDate"\s*=\s*<([^>]+)>', ioreg_output)
            if mfg_data_match:
                mfg_data = mfg_data_match.group(1).replace(" ", "")
                if len(mfg_data) >= 16:
                    year = int(mfg_data[12:14], 16)
                    month = int(mfg_data[14:16], 16)
                    day = int(mfg_data[16:18], 16) if len(mfg_data) >= 18 else 1
                    if 0 <= year <= 99 and 1 <= month <= 12 and 1 <= day <= 31:
                        year += 2000  # Assume 20xx
                        return f"{year}-{month:02d}-{day:02d}"
        except Exception as e:
            logger.debug(f"Error parsing manufacture date: {e}")
        return "Unknown"

    def get_battery_info(self) -> Optional[BatteryInfo]:
        """Gather battery information using IORegistry."""
        try:
            # Get raw battery data from IORegistry
            ioreg_output = self._run_command(["ioreg", "-r", "-n", "AppleSmartBattery"])

            if not ioreg_output:
                logger.warning("No battery found in IORegistry")
                return None

            # Get raw values
            current_capacity = self._get_value("AppleRawCurrentCapacity", ioreg_output)
            max_capacity = self._get_value("AppleRawMaxCapacity", ioreg_output)
            design_capacity = self._get_value("DesignCapacity", ioreg_output)
            cycle_count = self._get_value(
                "CycleCount", ioreg_output, 0
            )  # Default to 0 for cycle count
            temperature = self._get_value("Temperature", ioreg_output)
            voltage = self._get_value("Voltage", ioreg_output, 0)  # Default to 0 for voltage
            logger.debug(f"Raw voltage value: {voltage} mV")

            # Amperage is special - it's signed and may be very large when negative
            amperage = 0
            amperage_match = re.search(r'"Amperage"\s*=\s*(-?\d+)', ioreg_output)
            if amperage_match:
                amperage = int(amperage_match.group(1))
                logger.debug(f"Raw amperage value: {amperage} mA")

            if not all([current_capacity, max_capacity, design_capacity]):
                logger.warning("Could not get essential battery information")
                return None

            # Calculate charging power (in Watts)
            # Amperage is signed (negative when discharging)
            # Voltage is in mV, Amperage in mA
            try:
                voltage_val = voltage if voltage is not None else 0
                charging_power = abs(float(voltage_val) * float(amperage)) / 1000000.0
                if charging_power > 1000:  # Sanity check - no MacBook uses more than 1000W
                    charging_power = 0.0
                logger.debug(f"Calculated charging power: {charging_power} W")
            except (ValueError, OverflowError):
                charging_power = 0.0
                logger.debug("Error calculating charging power, defaulting to 0.0 W")

            # Temperature is in 100ths of degrees Celsius
            temp_val = temperature if temperature is not None else 0
            temp_celsius = float(temp_val) / 100.0
            temp_fahrenheit = (temp_celsius * 9 / 5) + 32

            # Get manufacture date
            manufacture_date = self._parse_manufacture_date(ioreg_output)

            # Check if low power mode is enabled
            low_power_mode = False
            try:
                power_mode = self._run_command(["pmset", "-g"])
                low_power_mode = "lowpowermode 1" in power_mode.lower()
            except OSError:
                pass

            # Ensure we have non-None values for required fields
            current_capacity_val = current_capacity if current_capacity is not None else 0
            max_capacity_val = max_capacity if max_capacity is not None else 0
            design_capacity_val = design_capacity if design_capacity is not None else 1
            cycle_count_val = cycle_count if cycle_count is not None else 0

            return BatteryInfo(
                current_charge=f"{current_capacity_val} mAh",
                health_percentage=float(max_capacity_val) / float(design_capacity_val) * 100,
                full_charge_capacity=f"{max_capacity_val} mAh",
                design_capacity=f"{design_capacity_val} mAh",
                manufacture_date=manufacture_date,
                cycle_count=cycle_count_val,
                temperature_celsius=temp_celsius,
                temperature_fahrenheit=temp_fahrenheit,
                charging_power=charging_power,
                low_power_mode=low_power_mode,
            )
        except Exception as e:
            logger.error(f"Error getting battery info: {e}")
            return None
