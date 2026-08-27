# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for the ``geoips lint`` command."""

import pytest

from geoips.commandline.commandline_interface import GeoipsCLI
from geoips.commandline import geoips_lint


def _get_lint_command():
    """Return the lint command and parsed default arguments."""
    cli = GeoipsCLI()
    args = cli.parser.parse_args(["lint"])
    return args.exe_command, args


def _provide_source_tree(monkeypatch, tmp_path):
    """Provide an editable-style package tree containing the lint runner."""
    package_path = tmp_path / "plugin_repository" / "geoips"
    package_path.mkdir(parents=True)
    lint_path = tmp_path / "plugin_repository" / "tests" / "utils"
    lint_path.mkdir(parents=True)
    (lint_path / "check_code.sh").touch()
    monkeypatch.setattr(geoips_lint.resources, "files", lambda unused: package_path)
    return package_path.parent


def test_non_editable_package_exits_cleanly(monkeypatch, capsys):
    """Report a concise operational error without raising a runtime traceback."""
    command, args = _get_lint_command()
    monkeypatch.setattr(geoips_lint, "is_editable", lambda unused: False)

    with pytest.raises(SystemExit) as exc_info:
        command(args)

    error = capsys.readouterr().err
    assert exc_info.value.code == 1
    assert "plugin package 'geoips' is not installed in editable mode" in error
    assert "python -m pip install -e PATH" in error
    assert "unit tests" not in error
    assert "Traceback" not in error


def test_missing_geoips_lint_runner_exits_cleanly(monkeypatch, tmp_path, capsys):
    """Fail when the installed GeoIPS package does not provide its lint runner."""
    command, args = _get_lint_command()
    package_path = tmp_path / "geoips"
    package_path.mkdir()
    monkeypatch.setattr(geoips_lint, "is_editable", lambda unused: True)
    monkeypatch.setattr(geoips_lint.resources, "files", lambda unused: package_path)

    with pytest.raises(SystemExit) as exc_info:
        command(args)

    error = capsys.readouterr().err
    assert exc_info.value.code == 1
    assert "GeoIPS lint runner was not found" in error
    assert "Install GeoIPS in editable mode" in error


def test_linter_failures_produce_a_failure_exit_status(monkeypatch, tmp_path, capsys):
    """Run every checker and report each nonzero return code."""
    command, args = _get_lint_command()
    package_root = _provide_source_tree(monkeypatch, tmp_path)
    calls = []
    return_codes = iter([0, 2, 3])

    monkeypatch.setattr(geoips_lint, "is_editable", lambda unused: True)

    def fake_call(command_args, shell):
        calls.append((command_args, shell))
        return next(return_codes)

    monkeypatch.setattr(geoips_lint, "call", fake_call)

    with pytest.raises(SystemExit) as exc_info:
        command(args)

    error = capsys.readouterr().err
    assert exc_info.value.code == 1
    assert "code-quality checks failed: black (2), flake8 (3)" in error
    assert [call_args[0][2] for call_args in calls] == ["bandit", "black", "flake8"]
    assert all(call_args[0][3] == str(package_root) for call_args in calls)
    assert all(call_args[1] is False for call_args in calls)


def test_successful_linters_complete_without_exiting(monkeypatch, tmp_path):
    """Return normally after all three checkers succeed."""
    command, args = _get_lint_command()
    _provide_source_tree(monkeypatch, tmp_path)
    calls = []

    monkeypatch.setattr(geoips_lint, "is_editable", lambda unused: True)
    monkeypatch.setattr(
        geoips_lint,
        "call",
        lambda command_args, shell: calls.append((command_args, shell)) or 0,
    )

    assert command(args) is None
    assert [call_args[0][2] for call_args in calls] == ["bandit", "black", "flake8"]


def test_subprocess_start_failure_exits_cleanly(monkeypatch, tmp_path, capsys):
    """Convert an operating-system subprocess error into a CLI failure."""
    command, args = _get_lint_command()
    _provide_source_tree(monkeypatch, tmp_path)
    monkeypatch.setattr(geoips_lint, "is_editable", lambda unused: True)

    def fail_to_start(unused_args, shell):
        raise OSError("bash is unavailable")

    monkeypatch.setattr(geoips_lint, "call", fail_to_start)

    with pytest.raises(SystemExit) as exc_info:
        command(args)

    error = capsys.readouterr().err
    assert exc_info.value.code == 1
    assert "unable to run bandit: bash is unavailable" in error
