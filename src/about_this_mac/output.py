"""Output handling for CLI with structured output and error handling."""

import json
import logging
import sys
from typing import Any, Dict, NoReturn, Optional, TextIO


class CliError(Exception):
    """User-friendly CLI error with optional hint."""

    def __init__(self, message: str, hint: Optional[str] = None, exit_code: int = 1):
        super().__init__(message)
        self.hint = hint
        self.exit_code = exit_code


class Output:
    """Structured output handler supporting text and JSON modes."""

    def __init__(
        self,
        json_mode: bool = False,
        quiet: bool = False,
        file: Optional[TextIO] = None,
    ):
        self._json_mode = json_mode
        self._quiet = quiet
        self._file = file or sys.stdout

    def text(self, message: str) -> None:
        """Print text message (suppressed in JSON mode)."""
        if not self._json_mode:
            print(message, file=self._file)

    def json(self, data: Dict[str, Any]) -> None:
        """Print JSON data (only in JSON mode)."""
        if self._json_mode:
            print(json.dumps(data, indent=2), file=self._file)

    def raw(self, message: str) -> None:
        """Print raw output regardless of mode."""
        print(message, file=self._file)

    def info(self, message: str) -> None:
        """Print info message to stderr (respects quiet mode)."""
        if not self._quiet:
            print(message, file=sys.stderr)

    def error(self, message: str, hint: Optional[str] = None, exit_code: int = 1) -> NoReturn:
        """Print error and exit."""
        if self._json_mode:
            error_data: Dict[str, Any] = {"error": message}
            if hint:
                error_data["hint"] = hint
            print(json.dumps(error_data), file=sys.stderr)
        else:
            print(f"Error: {message}", file=sys.stderr)
            if hint:
                print(f"Hint: {hint}", file=sys.stderr)
        sys.exit(exit_code)


def handle_error(error: Exception, output: Output, verbose: bool = False) -> NoReturn:
    """Handle exceptions with appropriate output."""
    if isinstance(error, CliError):
        output.error(str(error), error.hint, exit_code=error.exit_code)
    elif verbose:
        logging.exception("Unexpected error")
        output.error(str(error))
    else:
        output.error(str(error))
