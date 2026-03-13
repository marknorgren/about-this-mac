"""Report generation command for system information."""

import os
import sys
from argparse import Namespace
from dataclasses import asdict
from typing import Any, Dict, Optional

from about_this_mac import MacInfoGatherer
from about_this_mac.output import Output
from about_this_mac.utils.formatting import (
    format_output_as_json,
    format_output_as_markdown,
    format_output_as_public,
    format_output_as_simple,
    format_output_as_text,
    format_output_as_yaml,
)


def _should_use_color(
    format_type: str, output_target: Optional[str], force: bool, disable: bool
) -> bool:
    """Determine if color output should be used."""
    if format_type != "text" or disable:
        return False

    output_is_stdout = output_target in (None, "-")
    if not output_is_stdout:
        return False

    if force:
        return True

    if os.environ.get("NO_COLOR"):
        return False

    if os.environ.get("TERM", "").lower() == "dumb":
        return False

    return sys.stdout.isatty()


def _format_output(
    data: Dict[str, Any],
    format_type: str,
    use_color: bool = False,
) -> str:
    """Format the output according to the specified format."""
    if format_type == "simple":
        return format_output_as_simple(data)
    elif format_type == "public":
        return format_output_as_public(data)
    elif format_type == "json":
        return format_output_as_json(data)
    elif format_type == "yaml":
        return format_output_as_yaml(data)
    elif format_type == "markdown":
        return format_output_as_markdown(data)
    else:
        return format_output_as_text(data, use_color=use_color)


def run_report(args: Namespace, gatherer: MacInfoGatherer, output: Output) -> None:
    """Generate and output the system report."""
    data: Dict[str, Any] = {}

    if args.section in ["hardware", "all"]:
        data["hardware"] = asdict(gatherer.get_hardware_info())

    if args.section in ["battery", "all"]:
        battery_info = gatherer.get_battery_info()
        if battery_info:
            data["battery"] = asdict(battery_info)

    use_color = _should_use_color(args.format, args.output, args.color, args.no_color)
    formatted = _format_output(data, args.format, use_color=use_color)

    if args.output and args.output != "-":
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted)
        output.info(f"Output saved to {args.output}")
    else:
        output.raw(formatted)
