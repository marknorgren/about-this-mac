"""Tests for formatting utility functions."""
import json
import yaml
from datetime import datetime
from about_this_mac.utils.formatting import (
    format_size,
    format_uptime,
    format_bool,
    format_output_as_json,
    format_output_as_yaml,
    format_output_as_markdown,
)

def test_format_size_bytes():
    """Test formatting size in bytes."""
    assert format_size(500) == "500 bytes"

def test_format_size_mb():
    """Test formatting size in megabytes."""
    assert format_size(1024 * 1024 * 500) == "500 MB"

def test_format_size_gb():
    """Test formatting size in gigabytes."""
    assert format_size(1024 * 1024 * 1024 * 64) == "64 GB"

def test_format_size_tb():
    """Test formatting size in terabytes."""
    assert format_size(1024 * 1024 * 1024 * 1024 * 2) == "2 TB"

def test_format_uptime_minutes():
    """Test formatting uptime with only minutes."""
    assert format_uptime(45 * 60) == "45 minutes"

def test_format_uptime_hours():
    """Test formatting uptime with hours and minutes."""
    assert format_uptime(3 * 3600 + 45 * 60) == "3 hours 45 minutes"

def test_format_uptime_days():
    """Test formatting uptime with days, hours, and minutes."""
    uptime = 2 * 86400 + 3 * 3600 + 45 * 60
    assert format_uptime(uptime) == "2 days 3 hours 45 minutes"

def test_format_uptime_zero():
    """Test formatting zero uptime."""
    assert format_uptime(0) == "0 minutes"

def test_format_bool_true():
    """Test formatting boolean True value."""
    assert format_bool(True) == "Yes"

def test_format_bool_false():
    """Test formatting boolean False value."""
    assert format_bool(False) == "No"

def test_format_output_as_json():
    """Test formatting output as JSON."""
    data = {'test': 'value', 'number': 42}
    result = format_output_as_json(data)
    assert json.loads(result) == data
    assert '"test": "value"' in result
    assert '"number": 42' in result

def test_format_output_as_yaml():
    """Test formatting output as YAML."""
    data = {'test': 'value', 'number': 42}
    result = format_output_as_yaml(data)
    assert yaml.safe_load(result) == data
    assert 'test: value' in result
    assert 'number: 42' in result

def test_format_output_as_markdown_minimal():
    """Test formatting minimal output as markdown."""
    data = {}
    result = format_output_as_markdown(data)
    assert "# Mac System Information" in result
    assert "*Generated on" in result

def test_format_output_as_markdown_with_hardware():
    """Test formatting hardware info as markdown."""
    data = {
        'hardware': {
            'model_name': 'MacBook Pro',
            'device_identifier': 'Mac14,5',
            'model_number': 'A2779',
            'serial_number': 'ABC123',
            'processor': 'Apple M2 Max',
            'cpu_cores': 12,
            'performance_cores': 8,
            'efficiency_cores': 4,
            'gpu_cores': 30,
            'memory': {
                'total': '64 GB',
                'type': 'LPDDR5',
                'speed': '6400 MHz',
                'manufacturer': 'Apple',
                'ecc': True
            },
            'storage': {
                'model': 'Apple SSD',
                'type': 'NVMe',
                'protocol': 'PCIe',
                'size': '2 TB',
                'smart_status': 'Verified',
                'trim': True,
                'internal': True
            },
            'graphics': [
                {
                    'name': 'Apple M2 Max',
                    'vendor': 'Apple',
                    'vram': '64 GB',
                    'resolution': '3456x2234',
                    'metal': 'Metal 3'
                }
            ],
            'bluetooth_chipset': 'Apple',
            'bluetooth_firmware': '1.0',
            'bluetooth_transport': 'USB',
            'macos_version': '14.0',
            'macos_build': '23A344',
            'uptime': '2 days 3 hours'
        }
    }
    result = format_output_as_markdown(data)
    
    # Check main sections
    assert "## Hardware Information" in result
    assert "### System" in result
    assert "### Processor" in result
    assert "### Memory" in result
    assert "### Storage" in result
    assert "### Graphics" in result
    assert "### Wireless" in result
    assert "### System Software" in result
    
    # Check specific values
    assert "**Model:** MacBook Pro" in result
    assert "**Chip:** Apple M2 Max" in result
    assert "**Total:** 64 GB" in result
    assert "**SMART Status:** Verified" in result
    assert "**Metal Support:** Metal 3" in result

def test_format_output_as_markdown_with_battery():
    """Test formatting battery info as markdown."""
    data = {
        'battery': {
            'current_charge': '3584 mAh',
            'health_percentage': 79.6,
            'full_charge_capacity': '4837 mAh',
            'design_capacity': '6075 mAh',
            'manufacture_date': '2022-12-26',
            'cycle_count': 228,
            'temperature_celsius': 30.29,
            'temperature_fahrenheit': 86.52,
            'charging_power': 0.0,
            'low_power_mode': False
        }
    }
    result = format_output_as_markdown(data)
    
    # Check battery section
    assert "## Battery Information" in result
    assert "**Current Charge:** 3584 mAh" in result
    assert "**Health:** 79.6%" in result
    assert "**Temperature:** 30.3°C / 86.5°F" in result
    assert "**Low Power Mode:** Disabled" 