# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `list interfaces` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListInterfaces(BaseCliTest):
    """Unit Testing Class for List Interfaces Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsListInterfaces command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = ["geoips", "list", "interfaces"]
            alias_args = ["geoips", "ls", "interfaces"]
            self._cmd_list = [base_args, alias_args]
            for argset in [base_args, alias_args]:
                for pkg_name in self.plugin_package_names:
                    self._cmd_list.append(argset + ["-wp", "-p", pkg_name])
            # Add argument list which selects certain columns for generic interfaces
            self._cmd_list.append(
                base_args
                + [
                    "--columns",
                    "package",
                    "interface",
                    "supported_famlies",
                    "abspath",
                ]
            )
            self._cmd_list.append(
                alias_args
                + [
                    "--columns",
                    "package",
                    "interface",
                    "supported_famlies",
                    "abspath",
                ]
            )
            # Add argument list which selects certain columns for implemented interfaces
            self._cmd_list.append(
                base_args
                + [
                    "-wp",
                    "-p",
                    "geoips",
                    "--columns",
                    "interface",
                    "plugin_type",
                ]
            )
            self._cmd_list.append(
                alias_args
                + [
                    "-wp",
                    "-p",
                    "geoips",
                    "--columns",
                    "interface",
                    "plugin_type",
                ]
            )
            self._cmd_list.append(base_args + ["-p", "geoips"])
            self._cmd_list.append(alias_args + ["-p", "geoips"])
            # Add argument list with an invalid command call ("--long" with "--columns")
            self._cmd_list.append(base_args + ["--long", "--columns", "relpath"])
            self._cmd_list.append(alias_args + ["--long", "--columns", "relpath"])
            # Add argument list which invokes the help message for this command
            self._cmd_list.append(base_args + ["-h"])
            self._cmd_list.append(alias_args + ["-h"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips list interfaces ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # bad command has been provided, check the contents of the error message
        assert args != ["geoips", "list", "interfaces"] and args != [
            "geoips",
            "ls",
            "interfaces",
        ]
        assert args != ["geoips", "list", "interfaces", "-wp"]
        assert "usage: To use, type `geoips list interfaces`" in error
        if "--long" in args and "--columns" in args:
            assert (
                "error: argument --columns/-c: not allowed with argument --long/-l"
                in error
            )
        elif "-p" in args and "-wp" not in args:
            assert "You cannot use the `-p` flag without the `-wp` flag." in error

    def check_output(self, args, output):
        """Ensure that the 'geoips list interfaces ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        if "usage: To use, type" in output:
            # -h has been called, check help message contents for this command
            assert "-h" in args
            assert "To use, type `geoips list interfaces`" in output
        else:
            # The args provided are valid, so test that the output is actually correct
            selected_cols = self.retrieve_selected_columns(args)
            if "-wp" in args or "-p" in args:
                headers = {
                    "GeoIPS Package": "package",
                    "Interface Type": "plugin_type",
                    "Interface Name": "interface",
                }
            else:
                # `geoips list-interfaces` was called, check for the correct headers
                headers = {
                    "GeoIPS Package": "package",
                    "Interface Type": "plugin_type",
                    "Interface Name": "interface",
                    "Supported Families": "supported_families",
                    "Docstring": "docstring",
                    "Absolute Path": "abspath",
                }
            # Assert that the correct headers exist in the CLI output
            self.assert_correct_headers_in_output(output, headers, selected_cols)


test_sub_cmd = TestGeoipsListInterfaces()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips list interfaces ...' commands.

    This test covers every valid combination of commands for the
    'geoips list interfaces' command. We also test invalid commands, to ensure that
    the proper help documentation  is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'list', 'interfaces'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
