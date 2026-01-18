#!/usr/bin/env python3

"""Command-line interface for about-this-mac."""

import argparse
import logging

from about_this_mac import MacInfoGatherer, __version__
from about_this_mac.commands.raw import has_raw_args, run_raw_commands
from about_this_mac.commands.report import run_report
from about_this_mac.output import CliError, Output, handle_error


def _create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    description = "Gather detailed information about your Mac."
    examples = "\n".join(
        [
            "Examples:",
            "  about-this-mac",
            "  about-this-mac --section hardware",
            "  about-this-mac --format json",
            "  about-this-mac --plain --output report.txt",
            "  about-this-mac --hardware-info",
        ]
    )
    parser = argparse.ArgumentParser(
        description=description,
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Format options
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--format",
        choices=["text", "json", "yaml", "markdown", "public", "simple"],
        default="text",
        help='Output format (use "public" for sales-friendly output)',
    )
    format_group.add_argument(
        "--json",
        action="store_const",
        const="json",
        dest="format",
        help='Shorthand for "--format json"',
    )
    format_group.add_argument(
        "--plain",
        action="store_const",
        const="text",
        dest="format",
        help='Shorthand for "--format text"',
    )

    # Section and output
    parser.add_argument(
        "--section",
        choices=["hardware", "battery", "all"],
        default="all",
        help="Information section to display",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Save output to file (use '-' for stdout)",
    )

    # Verbosity
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed debug information",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-essential output",
    )

    # Color control
    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument(
        "--color",
        action="store_true",
        help="Force colored output",
    )
    color_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Raw data mode arguments
    parser.add_argument(
        "--hardware-info",
        action="store_true",
        help="Show raw hardware information from system_profiler SPHardwareDataType",
    )
    parser.add_argument(
        "--power-info",
        action="store_true",
        help="Show raw power information from system_profiler SPPowerDataType",
    )
    parser.add_argument(
        "--graphics-info",
        action="store_true",
        help="Show raw graphics information from system_profiler SPDisplaysDataType",
    )
    parser.add_argument(
        "--storage-info",
        action="store_true",
        help="Show raw storage information from system_profiler SP{NVMe,SerialATA,Storage}DataType",
    )
    parser.add_argument(
        "--memory-info",
        action="store_true",
        help="Show raw memory information from system_profiler SPMemoryDataType",
    )
    parser.add_argument(
        "--audio-info",
        action="store_true",
        help="Show raw audio information from system_profiler SPAudioDataType",
    )
    parser.add_argument(
        "--network-info",
        action="store_true",
        help="Show raw network information from system_profiler SPNetworkDataType",
    )
    parser.add_argument(
        "--release-date",
        action="store_true",
        help="Show raw release date information",
    )

    return parser


def _configure_logging(verbose: bool, quiet: bool) -> None:
    """Configure logging based on verbosity settings."""
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True,
    )


def main() -> None:
    """Main entry point for the CLI."""
    parser = _create_parser()
    args = parser.parse_args()

    _configure_logging(args.verbose, args.quiet)

    output = Output(
        json_mode=args.format == "json",
        quiet=args.quiet,
    )

    try:
        gatherer = MacInfoGatherer(verbose=args.verbose)

        # Handle release date command
        if args.release_date:
            release_date = gatherer.get_release_date()
            if release_date:
                output.raw(f"Release Date: {release_date}")
            else:
                raise CliError("Release date information not available")
            return

        # Handle raw data commands
        if has_raw_args(args):
            run_raw_commands(args, gatherer, output)
            return

        # Default: generate report
        run_report(args, gatherer, output)

    except Exception as e:
        handle_error(e, output, args.verbose)


if __name__ == "__main__":
    main()
