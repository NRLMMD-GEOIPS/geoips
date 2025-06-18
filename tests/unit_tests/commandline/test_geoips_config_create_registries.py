"""Unit test module for the CLI command 'geoips config create-registries'."""

import pytest

from geoips.commandline.commandline_interface import main
from geoips.errors import PluginRegistryError
from tests.unit_tests.commandline.cli_top_level_tester import (
    generate_id,
    check_valid_command_using_monkeypatch,
)

valid_args = [
    ["geoips", "config", "create-registries"],
    ["geoips", "config", "create-registries", "-s", "yaml"],
    ["geoips", "config", "create-registries", "-p", "geoips"],
    ["geoips", "config", "create-registries", "-n", "geoips.plugin_packages"],
    [
        "geoips",
        "config",
        "create-registries",
        "-n",
        "geoips.plugin_packages",
        "-p",
        "geoips",
        "--warnings",
        "hide",
    ],
]
valid_expected = [
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
        "save_type": "json",
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
        "save_type": "yaml",
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": ["geoips"],
        "save_type": "json",
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
        "save_type": "json",
        "warnings": "print",
    },
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": ["geoips"],
        "save_type": "json",
        "warnings": "print",
    },
]
invalid_args = [
    ["geoips", "config", "create-registries", "-p", "fake_package"],
    ["geoips", "config", "create-registries", "-n", "fake.plugin_packages"],
    ["geoips", "config", "create-registries", "-s", "invalid_save_type"],
]


@pytest.mark.parametrize("cli_args", [args for args in invalid_args], ids=generate_id)
def test_create_registries_invalid(monkeypatch, cli_args):
    """Test the CLI command 'geoips config create-registries' using invalid args.

    Parameters
    ----------
    cli_args: list[str]
        - A list of strings representing the CLI command being ran.
    """
    monkeypatch.setattr("sys.argv", cli_args)
    if "-n" in cli_args or "-p" in cli_args:
        error = PluginRegistryError
    else:
        # This occurs when 'save_type' is not one of 'json' or 'yaml'. Argparse
        # eventually calls sys.exit(2, msg), which is caught here.
        error = SystemExit
    with pytest.raises(error):
        main()


@pytest.mark.parametrize(
    "cli_args,expected",
    [(args, expected) for args, expected in zip(valid_args, valid_expected)],
    ids=generate_id,
)
def test_create_registries_valid(monkeypatch, cli_args, expected):
    """Test the CLI command 'geoips config create-registries' using valid args.

    Parameters
    ----------
    cli_args: list[str]
        - A list of strings representing the CLI command being ran.
    expected: dict
        - A dictionary of expected argument values that are returned from the command
          being ran from args.
    """
    check_valid_command_using_monkeypatch(monkeypatch, cli_args, expected)
