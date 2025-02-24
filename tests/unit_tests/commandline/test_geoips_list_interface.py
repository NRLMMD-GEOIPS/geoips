# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `list interface` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import json
from importlib import resources
from pathlib import Path
import pytest

from geoips import interfaces
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListInterface(BaseCliTest):
    """Unit Testing Class for List Interface Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsListInterface command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = ["geoips", "list"]
            alias_args = ["geoips", "ls"]
            for argset in [base_args, alias_args]:
                for pkg_name in self.plugin_package_names + ["all"]:
                    for interface_name in interfaces.__all__:
                        interface_name = interface_name.replace("_", "-")
                        if pkg_name != "all":
                            args = argset + [interface_name, "-p", pkg_name]
                        else:
                            args = argset + [interface_name]
                        self._cmd_list.append(args)
            # Add argument list with a non-existent interface
            self._cmd_list.append(base_args + ["non_existent_interface"])
            self._cmd_list.append(alias_args + ["non_existent_interface"])
            # Add argument list that utilizes the --column optional arg
            self._cmd_list.append(
                base_args
                + [
                    "algorithms",
                    "--columns",
                    "package",
                    "interface",
                    "plugin_type",
                    "relpath",
                ]
            )
            self._cmd_list.append(
                alias_args
                + [
                    "algorithms",
                    "--columns",
                    "package",
                    "interface",
                    "plugin_type",
                    "relpath",
                ]
            )
            # Add argument list with an existing interface but non-existent package
            self._cmd_list.append(
                base_args + ["algorithms", "-p", "non_existent_package"]
            )
            self._cmd_list.append(
                alias_args + ["algorithms", "-p", "non_existent_package"]
            )
            # Add argument list with an existing interface but w/ conflicting opt args
            self._cmd_list.append(
                base_args + ["readers", "--long", "--columns", "package", "interface"]
            )
            self._cmd_list.append(
                alias_args + ["readers", "--long", "--columns", "package", "interface"]
            )
        return self._cmd_list

    def check_error(self, args, error):
        """Check that the 'geoips list <interface_name> ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        if "--columns" in args and "--long" in args:
            assert (
                "error: argument --columns/-c: not allowed with argument --long/-l"
                in error.replace("\n", "")
            )
        elif args[2] in interfaces.__all__:
            # interface exists, so check that the package name is incorrect
            assert args[-1] not in self.plugin_package_names
            usg_str = (
                f"error: argument --package-name/-p: invalid "
                f"choice: '{args[-1]}' (choose from"
            )
            assert usg_str in error.replace("\n", "")
        else:
            assert args[2] not in interfaces.__all__
        assert (
            "usage: To use, type `geoips list <interface_name>`" in error
            or "usage: To use, type `geoips list <cmd> <sub-cmd>`" in error
        )

    def check_output(self, args, output):
        """Check that the 'geoips list <interface_name> ...' success output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        interface = getattr(interfaces, args[2].replace("-", "_"))
        interface_type = interface.interface_type
        if "No plugins found under" in output and "-p" in args:
            # No plugins were found under the selected interface, within a
            # certain package; ensure that is correct.
            plugin_registry = json.load(
                open(
                    Path(resources.files(args[-1]).joinpath("registered_plugins.json")),
                    "r",
                ),
            )
            # assert that the provided interface doesn't exist within that package's
            # plugin registry
            assert interface.name not in plugin_registry[interface_type].keys()
        else:
            # Assert that the correct headers exist in the CLI output
            selected_cols = self.retrieve_selected_columns(args)
            headers = {
                "GeoIPS Package": "package",
                "Interface Name": "interface",
                "Interface Type": "plugin_type",
                "Family": "family",
                "Plugin Name": "plugin_name",
                "Source Names": "source_name",
                "Relative Path": "relpath",
            }
            self.assert_correct_headers_in_output(output, headers, selected_cols)


test_sub_cmd = TestGeoipsListInterface()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips list <interface_name> ...' commands.

    This test covers every valid combination of commands for the
    'geoips list <interface_name>' command. We also test invalid commands, to ensure
    that the proper help documentation is provided for those using the command
    incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with
          (ie. ['geoips', 'list', 'algorithms'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
