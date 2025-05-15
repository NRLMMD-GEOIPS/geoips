# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `list source-names` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import json
from importlib import resources
from pathlib import Path
import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListSourceNames(BaseCliTest):
    """Unit Testing Class for List Source Names Command."""

    @property
    def command_combinations(self):
        """A list of call signatures for the GeoipsListSourceNames command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = ["geoips", "list", "source-names"]
            alias_args = ["geoips", "ls", "src-names"]
            for argset in [base_args, alias_args]:
                for pkg_name in self.plugin_package_names + ["all"]:
                    if pkg_name != "all":
                        args = argset + ["-p", pkg_name]
                    else:
                        args = argset
                    self._cmd_list.append(args)
            # Add argument list that utilizes the --column optional arg
            self._cmd_list.append(
                base_args + ["--columns", "source_name", "reader_names"]
            )
            self._cmd_list.append(
                alias_args + ["--columns", "source_name", "reader_names"]
            )
            # Add argument list with an existing interface but non-existent package
            self._cmd_list.append(base_args + ["-p", "non_existent_package"])
            self._cmd_list.append(alias_args + ["-p", "non_existent_package"])
            # Add argument list with an existing interface but w/ conflicting opt args
            self._cmd_list.append(
                base_args + ["--long", "--columns", "source_name", "reader_names"]
            )
            self._cmd_list.append(
                alias_args + ["--long", "--columns", "source_name", "reader_names"]
            )
        return self._cmd_list

    def check_error(self, args, error):
        """Check that the 'geoips list source-names ...' error output is correct.

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
        elif "-p" in args and args[-1] not in self.plugin_package_names:
            # check the package name is incorrect
            usg_str = (
                f"error: argument --package-name/-p: invalid "
                f"choice: '{args[-1]}' (choose from"
            )
            assert usg_str in error.replace("\n", "")
        assert (
            "usage: To use, type `geoips list source-names`" in error
            or "usage: To use, type `geoips list <cmd> <sub-cmd>`" in error
        )

    def check_output(self, args, output):
        """Check that the 'geoips list source-names...' success output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "no reader plugins" in output and "-p" in args:
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
            assert "readers" not in plugin_registry["module_based"].keys()
        else:
            # Assert that the correct headers exist in the CLI output
            selected_cols = self.retrieve_selected_columns(args)
            headers = {
                "Source Name": "source_name",
                "Reader Names": "reader_names",
            }
            self.assert_correct_headers_in_output(output, headers, selected_cols)


test_sub_cmd = TestGeoipsListSourceNames()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips list source-names ...' commands.

    This test covers valid combination of commands for the
    'geoips list source-names' command. We also test invalid commands, to ensure
    that the proper help documentation is provided for those using the command
    incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with
          (ie. ['geoips', 'list', 'source-names'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
