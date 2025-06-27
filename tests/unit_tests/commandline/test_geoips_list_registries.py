# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test module for the CLI command 'geoips list registries'."""

import pytest

from geoips.commandline.commandline_interface import main
from tests.unit_tests.commandline.cli_top_level_tester import (
    generate_id,
    check_valid_command_using_monkeypatch,
)

valid_args = [
    ["geoips", "list", "registries"],
    ["geoips", "list", "registries", "-c", "package", "json"],
    ["geoips", "list", "registries", "-p", "geoips"],
    ["geoips", "list", "registries", "-n", "geoips.plugin_packages"],
    ["geoips", "list", "registries", "-r"],
    ["geoips", "list", "registries", "-n", "geoips.plugin_packages", "-r"],
]
valid_expected = [
    {
        "log_level": "interactive",
        "command": "geoips list registries",
        "package_name": "all",
        "long": True,
        "columns": None,
        "namespace": "geoips.plugin_packages",
        "relpath": False,
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips list registries",
        "package_name": "all",
        "long": True,
        "columns": ["package", "json"],
        "namespace": "geoips.plugin_packages",
        "relpath": False,
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips list registries",
        "package_name": "geoips",
        "long": True,
        "columns": None,
        "namespace": "geoips.plugin_packages",
        "relpath": False,
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips list registries",
        "package_name": "all",
        "long": True,
        "columns": None,
        "namespace": "geoips.plugin_packages",
        "relpath": False,
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips list registries",
        "package_name": "all",
        "long": True,
        "columns": None,
        "namespace": "geoips.plugin_packages",
        "relpath": True,
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips list registries",
        "package_name": "all",
        "long": True,
        "columns": None,
        "namespace": "geoips.plugin_packages",
        "relpath": True,
        "warnings": "print",
    },
]
invalid_args = [
    ["geoips", "list", "registries", "-n", "fake.plugin_packages"],
    ["geoips", "list", "registries", "-c", "not_a_column"],
    ["geoips", "list", "registries", "-p", "fake_package"],
]


@pytest.mark.parametrize("cli_args", [args for args in invalid_args], ids=generate_id)
def test_list_registries_invalid(monkeypatch, cli_args):
    """Test the CLI command 'geoips list registries' using invalid args.

    Parameters
    ----------
    cli_args: list[str]
        - A list of strings representing the CLI command being ran.
    """
    monkeypatch.setattr("sys.argv", cli_args)
    with pytest.raises(SystemExit):
        main()


@pytest.mark.parametrize(
    "cli_args,expected",
    [(args, expected) for args, expected in zip(valid_args, valid_expected)],
    ids=generate_id,
)
def test_list_registries_valid(monkeypatch, capsys, cli_args, expected):
    """Test the CLI command 'geoips list registries' using valid args.

    Parameters
    ----------
    cli_args: list[str]
        - A list of strings representing the CLI command being ran.
    expected: dict
        - A dictionary of expected argument values that are returned from the command
          being ran from args.
    """
    check_valid_command_using_monkeypatch(monkeypatch, cli_args, expected)
    captured = capsys.readouterr()
    headers = {
        "package": "GeoIPS Package",
        "json": "JSON Path",
        "yaml": "YAML Path",
    }
    if "-c" in cli_args:
        selected = cli_args[cli_args.index("-c") + 1 :]
    else:
        selected = list(headers.keys())
    for col in selected:
        assert headers[col] in captured.out
