"""Unit test module for the CLI command 'geoips config create-registries'."""

import pytest

from geoips.commandline.commandline_interface import main
from geoips.errors import PluginRegistryError

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
    ],
]
valid_expected = [
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
        "save_type": "json",
    },
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
        "save_type": "yaml",
    },
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": ["geoips"],
        "save_type": "json",
    },
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": None,
        "save_type": "json",
    },
    {
        "log_level": "interactive",
        "command": "geoips config create-registries",
        "namespace": "geoips.plugin_packages",
        "packages": ["geoips"],
        "save_type": "json",
    },
]
invalid_args = [
    ["geoips", "config", "create-registries", "-p", "fake_package"],
    ["geoips", "config", "create-registries", "-n", "fake.plugin_packages"],
    ["geoips", "config", "create-registries", "-s", "invalid_save_type"],
]


def generate_id(args):
    """Generate an ID from the arguments provided.

    Parameters
    ----------
    args: list[str]
        - A list of strings representing the CLI command being ran.
    expected: dict
        - A dictionary of expected argument values that are returned from the command
          being ran from args.
    """
    if isinstance(args, dict):
        return ""
    return " ".join(args)


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
    monkeypatch.setattr("sys.argv", cli_args)
    args = main(suppress_args=False)
    arg_dict = vars(args)
    arg_dict.pop("command_parser")
    arg_dict.pop("exe_command")
    # Assert that the argument dictionary returned from the CLI matches what we expect
    assert arg_dict == expected
