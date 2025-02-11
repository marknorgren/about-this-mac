"""Utility functions for about-this-mac."""

from .command import run_command, get_sysctl_value
from .system import (
    check_macos,
    check_permissions,
    parse_system_profiler_data,
    is_apple_silicon,
)
from .formatting import (
    format_size,
    format_uptime,
    format_bool,
    format_output_as_json,
    format_output_as_yaml,
    format_output_as_markdown,
)

__all__ = [
    "run_command",
    "get_sysctl_value",
    "check_macos",
    "check_permissions",
    "parse_system_profiler_data",
    "is_apple_silicon",
    "format_size",
    "format_uptime",
    "format_bool",
    "format_output_as_json",
    "format_output_as_yaml",
    "format_output_as_markdown",
]
