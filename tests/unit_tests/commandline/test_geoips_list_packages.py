# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `list packages` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListPackages(BaseCliTest):
    """Unit Testing Class for List Packages Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsListPackages command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = ["geoips", "list", "packages"]
            alias_args = ["geoips", "ls", "packages"]
            self._cmd_list = [base_args, alias_args]
            # Add argument list invoking the --columns flag
            self._cmd_list.append(base_args + ["--columns", "package", "package_path"])
            self._cmd_list.append(alias_args + ["--columns", "package", "package_path"])
            self._cmd_list.append(base_args + ["--columns", "docstring", "package"])
            self._cmd_list.append(alias_args + ["--columns", "docstring", "package"])
            self._cmd_list.append(
                base_args + ["--columns", "docstring", "package_path"]
            )
            self._cmd_list.append(
                alias_args + ["--columns", "docstring", "package_path"]
            )
            self._cmd_list.append(
                base_args + ["--columns", "package", "docstring", "package_path"]
            )
            self._cmd_list.append(
                alias_args + ["--columns", "package", "docstring", "package_path"]
            )
            # Add argument list which invokes the help message for this command
            self._cmd_list.append(base_args + ["-h"])
            self._cmd_list.append(alias_args + ["-h"])
            # Add argument list with a non-existent command call ("-p")
            self._cmd_list.append(base_args + ["-p", "geoips"])
            self._cmd_list.append(alias_args + ["-p", "geoips"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips list packages ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # bad command has been provided, check the contents of the error message
        assert args != ["geoips", "list", "packages"] and args != [
            "geoips",
            "ls",
            "packages",
        ]
        assert "usage: To use, type `geoips list packages`" in error
        assert "Error: '-p' flag is not supported for this command" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips list packages ...' successful output is correct.

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
            assert "type `geoips list packages`" in output
        else:
            # The args provided are valid, so test that the output is actually correct
            for arg in ["geoips", "list", "packages"]:
                if arg == "list":
                    assert arg in args or "ls" in args
                else:
                    assert arg in args
            # Assert that the correct headers exist in the CLI output
            headers = {
                "GeoIPS Package": "package",
                "Docstring": "docstring",
                "Package Path": "package_path",
                "Version Number": "version",
            }
            selected_cols = self.retrieve_selected_columns(args)
            self.assert_correct_headers_in_output(output, headers, selected_cols)
            # Assert that we found every installed package
            for pkg_name in self.plugin_package_names:
                if "--columns" not in args or "package" in selected_cols:
                    assert pkg_name in output


test_sub_cmd = TestGeoipsListPackages()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips list packages ...' commands.

    This test covers every valid combination of commands for the 'geoips list packages'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'list', 'packages'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
