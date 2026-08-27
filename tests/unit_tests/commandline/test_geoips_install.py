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

    assert data_parser.usage == (
        "geoips install data DATASET [DATASET ...] [OPTIONS]\n"
        "       geoips install data all [OPTIONS]\n"
    )
    assert "DATASET" in help_output
    assert "DIRECTORY" in help_output
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


def test_install_github_help_describes_test_data_repository_scope():
    """Describe the GitHub command's source, destination, and limited scope."""
    cli = GeoipsCLI()
    install_parser = _get_subparser(cli.parser, "install")
    github_parser = _get_subparser(install_parser, "github")
    help_output = github_parser.format_help()
    description = " ".join(github_parser.description.split())

    assert github_parser.usage == "geoips install github REPOSITORY"
    assert "REPOSITORY" in help_output
    assert "GEOIPS_REPO_URL" in description
    assert "GEOIPS_TESTDATA_DIR" in description
    assert "does not install GeoIPS plugin packages" in description
