"""Unit test module for the CLI command 'geoips config delete-registries'."""

import pytest

from geoips.commandline.commandline_interface import main
from geoips.errors import PluginRegistryError
from geoips.plugin_registry import plugin_registry
from tests.unit_tests.commandline.cli_top_level_tester import (
    generate_id,
    check_valid_command_using_monkeypatch,
)

valid_args = [
    ["geoips", "config", "delete-registries"],
    ["geoips", "config", "delete-registries", "-p", "geoips"],
    ["geoips", "config", "delete-registries", "-n", "geoips.plugin_packages"],
    [
        "geoips",
        "config",
        "delete-registries",
        "-n",
        "geoips.plugin_packages",
        "-p",
        "geoips",
    ],
    # Used to rebuild the registry at the end of testing.
    ["creating-registries"],
]
valid_expected = [
    {
        "log_level": "interactive",
        "command": "geoips config delete-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
        "warnings": "hide",
    },
    {
        "log_level": "interactive",
        "command": "geoips config delete-registries",
        "namespace": "geoips.plugin_packages",
        "packages": ["geoips"],
        "warnings": "hide",
    },
    {
        "log_level": "interactive",
        "command": "geoips config delete-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
        "warnings": "hide",
    },
    {
        "log_level": "interactive",
        "command": "geoips config delete-registries",
        "namespace": "geoips.plugin_packages",
        "packages": ["geoips"],
        "warnings": "hide",
    },
    # Dummy dict needed for registry rebuild
    {"empty": "dict"},
]
invalid_args = [
    ["geoips", "config", "delete-registries", "-p", "fake_package"],
    ["geoips", "config", "delete-registries", "-n", "fake.plugin_packages"],
]


@pytest.mark.parametrize("cli_args", [args for args in invalid_args], ids=generate_id)
def test_delete_registries_invalid(monkeypatch, cli_args):
    """Test the CLI command 'geoips config delete-registries' using invalid args.

    Parameters
    ----------
    cli_args: list[str]
        - A list of strings representing the CLI command being ran.
    """
    monkeypatch.setattr("sys.argv", cli_args)
    with pytest.raises(PluginRegistryError):
        main()


@pytest.mark.parametrize(
    "cli_args,expected",
    [(args, expected) for args, expected in zip(valid_args, valid_expected)],
    ids=generate_id,
)
def test_delete_registries_valid(monkeypatch, cli_args, expected):
    """Test the CLI command 'geoips config delete-registries' using valid args.

    Parameters
    ----------
    cli_args: list[str]
        - A list of strings representing the CLI command being ran.
    expected: dict
        - A dictionary of expected argument values that are returned from the command
          being ran from args.
    """
    # Reset the registry at the end of testing. This could break other unit tests if the
    # registries are not rebuilt.
    if cli_args == ["creating-registries"]:
        plugin_registry.create_registries()
        return
    check_valid_command_using_monkeypatch(monkeypatch, cli_args, expected)
