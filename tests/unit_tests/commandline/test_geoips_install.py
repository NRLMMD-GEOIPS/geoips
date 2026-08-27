# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Focused tests for the GeoIPS CLI ``install`` command."""

import argparse
import sys

import pytest

from geoips.commandline.commandline_interface import GeoipsCLI


def _get_subparser(parser, name):
    """Return a named direct child of ``parser``."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices[name]
    raise AssertionError(f"No subparsers found on {parser.prog}.")


def test_install_data_help_uses_concise_dataset_metavar():
    """Hide the full dataset catalog from command help."""
    cli = GeoipsCLI()
    install_parser = _get_subparser(cli.parser, "install")
    data_parser = _get_subparser(install_parser, "data")
    help_output = data_parser.format_help()

    assert "DATASET [DATASET ...]" in help_output
    assert "{test_data_abi" not in help_output


def test_install_data_rejects_all_with_dataset_name(monkeypatch, capsys):
    """Require ``all`` to be used without individual dataset names."""
    cli = GeoipsCLI()
    monkeypatch.setattr(
        sys,
        "argv",
        ["geoips", "install", "data", "all", "test_data_abi"],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.execute_command()

    assert exc_info.value.code == 2
    assert (
        "'all' cannot be combined with individual dataset names"
        in capsys.readouterr().err
    )


def test_install_github_help_uses_repository_metavar():
    """Hide the repository choices behind a concise metavar."""
    cli = GeoipsCLI()
    install_parser = _get_subparser(cli.parser, "install")
    github_parser = _get_subparser(install_parser, "github")
    help_output = github_parser.format_help()

    assert "geoips install github REPOSITORY" in help_output
    assert "{test_data_abi" not in help_output


def test_install_github_reports_user_facing_progress(monkeypatch, capsys):
    """Describe the requested installation instead of exposing its shell command."""
    cli = GeoipsCLI()
    monkeypatch.setattr(
        sys,
        "argv",
        ["geoips", "install", "github", "test_data_abi"],
    )
    monkeypatch.setattr(
        "geoips.commandline.geoips_install.subprocess.call",
        lambda _: 0,
    )

    cli.execute_command()

    output = capsys.readouterr().out
    assert "test_data_abi" in output
    assert "git clone" not in output


def test_install_data_reports_missing_output_directory(monkeypatch, capsys, tmp_path):
    """Report a concise error when the selected destination does not exist."""
    missing_dir = tmp_path / "missing"
    cli = GeoipsCLI()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "geoips",
            "install",
            "data",
            "test_data_abi",
            "--outdir",
            str(missing_dir),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.execute_command()

    assert exc_info.value.code == 2
    assert f"Output directory '{missing_dir}' does not exist" in capsys.readouterr().err
