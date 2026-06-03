# Phase 1 Data Model: about-this-mac Information CLI

**Feature**: 001-mac-info-cli | **Date**: 2026-06-03

Entities mirror the dataclasses already defined in the codebase. Fields and
types are taken verbatim from the source; the "Privacy class" column records how
each field is treated at the `public`-format boundary (OC-004).

## HardwareInfo (`hardware/hardware_info.py`)

| Field | Type | Source | Privacy class (public) |
|-------|------|--------|------------------------|
| model_name | str | `system_profiler SPHardwareDataType` | Safe (shown) |
| device_identifier | str | `sysctl hw.model` / SPHardwareDataType | **Excluded** (unique device ID) |
| model_number | str | SPHardwareDataType | Safe |
| serial_number | str | SPHardwareDataType | **Excluded** (serial) |
| processor | str | SPHardwareDataType / `sysctl machdep.cpu.brand_string` | Safe (shown) |
| cpu_cores | int | `sysctl hw.ncpu` / SPHardwareDataType | Safe (shown) |
| performance_cores | int | SPHardwareDataType | Safe |
| efficiency_cores | int | SPHardwareDataType | Safe |
| gpu_cores | int | SPDisplaysDataType | Safe (shown) |
| graphics | List[Dict[str,str]] | `system_profiler SPDisplaysDataType` | Safe |
| bluetooth_chipset | str | SPBluetoothDataType | Safe (not in public) |
| bluetooth_firmware | str | SPBluetoothDataType | Safe (not in public) |
| bluetooth_transport | str | SPBluetoothDataType | Safe (not in public) |
| macos_version | str | `platform.mac_ver()` / SPSoftwareDataType | Safe |
| macos_build | str | SPSoftwareDataType | Safe |
| uptime | Optional[int] | `sysctl kern.boottime` | Safe |
| release_date | str | derived | Safe (shown) |
| model_size | str | derived | Safe (shown) |
| model_year | str | derived | Safe (shown) |

Note: Wi-Fi/Bluetooth MAC addresses and hostname are **not currently fields** on
any entity. Per OC-004 they remain **Excluded** from `public` if ever added.

## BatteryInfo (`battery/battery_info.py`)

| Field | Type | Source |
|-------|------|--------|
| current_charge | str | `system_profiler SPPowerDataType` / `pmset -g batt` |
| health_percentage | float | SPPowerDataType / ioreg |
| full_charge_capacity | str | SPPowerDataType / ioreg |
| design_capacity | str | ioreg |
| manufacture_date | str | ioreg |
| cycle_count | int | SPPowerDataType / ioreg |
| temperature_celsius | float | ioreg |
| temperature_fahrenheit | float | derived |
| charging_power | float | SPPowerDataType |
| low_power_mode | bool | SPPowerDataType / `pmset` |

All battery fields are owner/diagnostic facts. Battery is absent on desktop
Macs — fields degrade to documented unknown/empty values (FR-013, edge case).

## MemoryInfo (`hardware/hardware_info.py`)

| Field | Type | Source |
|-------|------|--------|
| total | str | `sysctl hw.memsize` / SPMemoryDataType |
| type | str | SPMemoryDataType |
| speed | str | SPMemoryDataType |
| manufacturer | str | SPMemoryDataType |
| ecc | bool | SPMemoryDataType |

## StorageInfo (`hardware/hardware_info.py`)

| Field | Type | Source |
|-------|------|--------|
| name | str | SPNVMeDataType / SPSerialATADataType / SPStorageDataType |
| model | str | as above |
| revision | str | as above |
| serial | str | as above (device serial — owner/diagnostic) |
| size | str | as above |
| type | str | NVMe / SATA |
| protocol | str | Apple Fabric / PCIe |
| trim | bool | as above |
| smart_status | str | as above |
| removable | bool | as above |
| internal | bool | as above |

## Report (composed)

The formatted output for a chosen `--format` and `--section`. Not a stored
entity — produced on demand by `commands/report.py` dispatching to one of the
six `utils/formatting.py` formatters. The `public` variant applies the OC-004
allowlist; all others may include serial/identifier fields.

## Validation / lifecycle rules

- Unresolved fields render as a consistent `UNKNOWN_VALUE` marker rather than
  raising (FR-013).
- `uptime` is the only intentionally nullable field (`Optional[int]`); formatters
  handle `None` without error.
- No field is mutated after gathering; entities are produced once per invocation.
