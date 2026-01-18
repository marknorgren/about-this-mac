"""Tests for output utilities."""

import io
import json

import pytest

from about_this_mac.output import CliError, Output, handle_error


def test_output_text_and_raw_write_to_file() -> None:
    buffer = io.StringIO()
    output = Output(file=buffer)

    output.text("Hello")
    output.raw("Raw")

    assert buffer.getvalue() == "Hello\nRaw\n"


def test_output_json_mode_suppresses_text() -> None:
    buffer = io.StringIO()
    output = Output(json_mode=True, file=buffer)

    output.text("Hello")
    output.json({"status": "ok"})

    assert "Hello" not in buffer.getvalue()
    assert json.loads(buffer.getvalue()) == {"status": "ok"}


def test_output_error_uses_exit_code_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    output = Output(json_mode=True)

    with pytest.raises(SystemExit) as excinfo:
        output.error("Boom", hint="Try again", exit_code=2)

    assert excinfo.value.code == 2
    error_json = json.loads(capsys.readouterr().err.strip())
    assert error_json == {"error": "Boom", "hint": "Try again"}


def test_handle_error_uses_cli_error_exit_code(capsys: pytest.CaptureFixture[str]) -> None:
    output = Output()

    with pytest.raises(SystemExit) as excinfo:
        handle_error(CliError("Nope", exit_code=3), output)

    assert excinfo.value.code == 3
    assert "Error: Nope" in capsys.readouterr().err
