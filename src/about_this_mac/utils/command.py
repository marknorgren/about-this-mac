"""Command execution utilities."""

from dataclasses import dataclass
import logging
import shlex
import subprocess
from typing import Any, Dict, List, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandResult:
    """Result for a command execution."""

    command: List[str]
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        """Return True when the command succeeded."""
        return self.returncode == 0


def _format_command(command: Sequence[str]) -> str:
    try:
        return shlex.join(command)
    except TypeError:
        return " ".join(str(part) for part in command)


def _normalize_returncode(returncode: Optional[int]) -> int:
    if isinstance(returncode, int):
        return returncode
    return 0


def _normalize_output(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    if isinstance(value, str):
        return value
    return str(value)


def run_command_result(  # pylint: disable=too-many-positional-arguments
    command: Sequence[str],
    check: bool = True,
    timeout: Optional[float] = None,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[str] = None,
    strip: bool = True,
) -> CommandResult:
    """Run a shell command and return stdout/stderr/returncode.

    Args:
        command: Command and arguments to execute.
        check: Whether to check the return code (non-zero treated as failure).
        timeout: Optional timeout in seconds.
        env: Optional environment overrides.
        cwd: Optional working directory.
        strip: Whether to trim stdout/stderr.

    Returns:
        CommandResult containing stdout, stderr, and return code.
    """
    command_list = [str(part) for part in command]
    kwargs: Dict[str, Any] = {"capture_output": True, "text": True}
    if timeout is not None:
        kwargs["timeout"] = timeout
    if env is not None:
        kwargs["env"] = env
    if cwd is not None:
        kwargs["cwd"] = cwd

    try:
        completed = subprocess.run(command_list, check=check, **kwargs)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if strip:
            stdout = stdout.strip()
            stderr = stderr.strip()
        return CommandResult(
            command=command_list,
            stdout=stdout,
            stderr=stderr,
            returncode=_normalize_returncode(getattr(completed, "returncode", 0)),
        )
    except subprocess.CalledProcessError as exc:
        stdout = _normalize_output(exc.stdout)
        stderr = _normalize_output(exc.stderr)
        if strip:
            stdout = stdout.strip()
            stderr = stderr.strip()
        logger.debug("Command failed: %s", _format_command(command_list))
        if stderr:
            logger.debug("Command stderr: %s", stderr)
        return CommandResult(
            command=command_list,
            stdout=stdout,
            stderr=stderr,
            returncode=_normalize_returncode(getattr(exc, "returncode", 1)),
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _normalize_output(exc.stdout)
        stderr = _normalize_output(exc.stderr)
        if strip:
            stdout = stdout.strip()
            stderr = stderr.strip()
        logger.debug("Command timed out: %s", _format_command(command_list))
        return CommandResult(command=command_list, stdout=stdout, stderr=stderr, returncode=124)
    except FileNotFoundError as exc:
        logger.debug("Command not found: %s", _format_command(command_list))
        return CommandResult(command=command_list, stdout="", stderr=str(exc), returncode=127)
    except OSError as exc:
        logger.debug("Command failed to start: %s", _format_command(command_list))
        return CommandResult(command=command_list, stdout="", stderr=str(exc), returncode=127)


def run_command(  # pylint: disable=too-many-positional-arguments
    command: Sequence[str],
    check: bool = True,
    timeout: Optional[float] = None,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[str] = None,
    strip: bool = True,
) -> str:
    """Run a shell command and return its output.

    Args:
        command: Command and arguments to execute.
        check: Whether to check the return code.
        timeout: Optional timeout in seconds.
        env: Optional environment overrides.
        cwd: Optional working directory.
        strip: Whether to trim stdout.

    Returns:
        The command output as a string (empty string on failure when check=True).
    """
    result = run_command_result(
        command=command,
        check=check,
        timeout=timeout,
        env=env,
        cwd=cwd,
        strip=strip,
    )
    if check and not result.ok:
        return ""
    return result.stdout


def get_sysctl_value(key: str, default: str = "Unknown", timeout: Optional[float] = None) -> str:
    """Get system information using sysctl.

    Args:
        key: The sysctl key to query.
        default: Value to return on failure.
        timeout: Optional timeout in seconds.

    Returns:
        The value as a string, or the default on error.
    """
    kwargs: Dict[str, Any] = {"capture_output": True, "text": True}
    if timeout is not None:
        kwargs["timeout"] = timeout
    try:
        result = subprocess.run(["sysctl", "-n", key], check=True, **kwargs)
        value = (result.stdout or "").strip()
        return value if value else default
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
        logger.debug("sysctl lookup failed for key: %s", key)
        return default
