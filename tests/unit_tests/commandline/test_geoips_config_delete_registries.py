"""Unit test module for the CLI command 'geoips config delete-registries'."""

import pytest

from geoips.commandline.commandline_interface import main
from geoips.errors import PluginRegistryError
from geoips.plugin_registry import plugin_registry
from tests.unit_tests.commandline.test_geoips_config_create_registries import (
    generate_id,
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
    },
    {
        "log_level": "interactive",
        "command": "geoips config delete-registries",
        "namespace": "geoips.plugin_packages",
        "packages": ["geoips"],
    },
    {
        "log_level": "interactive",
        "command": "geoips config delete-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
    },
    {
        "log_level": "interactive",
        "command": "geoips config delete-registries",
        "namespace": "geoips.plugin_packages",
        "packages": ["geoips"],
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
    if cli_args == ["creating-registries"]:
        plugin_registry.create_registries()
        return
    monkeypatch.setattr("sys.argv", cli_args)
    args = main(suppress_args=False)
    arg_dict = vars(args)
    arg_dict.pop("command_parser")
    arg_dict.pop("exe_command")
    # Assert that the argument dictionary returned from the CLI matches what we expect
    assert arg_dict == expected
