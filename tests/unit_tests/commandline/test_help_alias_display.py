# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for displaying CLI command aliases in help output."""

import argparse
from copy import deepcopy

import pytest

from geoips.commandline.ancillary_info import cmd_instructions
from geoips.commandline.commandline_interface import GeoipsCLI


def _walk_parsers(parser):
    """Yield each unique parser in a command hierarchy."""
    seen = set()
    pending = [parser]
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        for action in current._actions:
            if isinstance(action, argparse._SubParsersAction):
                pending.extend(action.choices.values())


def _get_subparser(parser, name):
    """Return a named direct child of ``parser``."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices[name]
    raise AssertionError(f"No subparsers found on {parser.prog}.")


def test_subcommand_aliases_have_consistent_help_formatting():
    """Display aliases beside commands, but omit them from the usage selector."""
    cli = GeoipsCLI()

    for parser in _walk_parsers(cli.parser):
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                assert action.metavar == "COMMAND"

    help_output = cli.parser.format_help()
    assert "config (cfg)" in help_output
    assert "{config,cfg" not in help_output


@pytest.mark.parametrize(
    ("help_text", "description_text", "expected_help", "expected_description"),
    [
        (
            "Short list help.",
            "Long list description.",
            "Short list help.",
            "Long list description.",
        ),
        ("Help fallback text.", None, "Help fallback text.", "Help fallback text."),
        (
            None,
            "Description fallback text.",
            "Description fallback text.",
            "Description fallback text.",
        ),
    ],
)
def test_command_help_and_description_fallbacks(
    help_text, description_text, expected_help, expected_description
):
    """Use either instruction field as the fallback for the other."""
    instructions = deepcopy(cmd_instructions)
    list_instructions = instructions["instructions"]["geoips_list"]
    list_instructions.pop("help", None)
    list_instructions.pop("description", None)
    if help_text is not None:
        list_instructions["help"] = help_text
    if description_text is not None:
        list_instructions["description"] = description_text

    cli = GeoipsCLI(cmd_instructions=instructions)
    list_parser = _get_subparser(cli.parser, "list")

    assert expected_help in cli.parser.format_help()
    assert expected_description in list_parser.format_help()


def test_command_instructions_require_help_or_description():
    """Reject command instructions that omit both text fields."""
    instructions = deepcopy(cmd_instructions)
    list_instructions = instructions["instructions"]["geoips_list"]
    list_instructions.pop("help", None)
    list_instructions.pop("description", None)

    with pytest.raises(KeyError, match="must define 'help', 'description', or both"):
        GeoipsCLI(cmd_instructions=instructions)


def test_describe_interface_instructions_are_formatted_for_each_interface():
    """Substitute interface names and hide large positional choices."""
    cli = GeoipsCLI()
    describe_parser = _get_subparser(cli.parser, "describe")
    algorithms_parser = _get_subparser(describe_parser, "algorithms")
    output_formatters_parser = _get_subparser(describe_parser, "output-formatters")

    assert "algorithms" in algorithms_parser.description
    assert "output-formatters" in output_formatters_parser.description
    assert "{interface}" not in algorithms_parser.description
    assert "{interface}" not in output_formatters_parser.description

    algorithms_help = algorithms_parser.format_help()
    assert "FAMILY" in algorithms_help
    assert "PLUGIN" in algorithms_help
    assert "{scalar_to_scalar" not in algorithms_help


def test_lint_help_hides_package_choices():
    """Use a concise metavar instead of listing installed plugin packages."""
    cli = GeoipsCLI()
    lint_parser = _get_subparser(cli.parser, "lint")
    help_output = lint_parser.format_help()

    assert "--package-name PACKAGE" in help_output
    assert "{geoips" not in help_output
