# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `describe package` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsDescribePackage(BaseCliTest):
    """Unit Testing Class for Describe Package Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the this command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = ["geoips", "describe"]
            # add arguments for retrieving each package
            for pkg_name in self.plugin_package_names:
                for alias in self.alias_mapping["package"] + ["package"]:
                    self._cmd_list.append(base_args + [alias, pkg_name])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["pkg", "-h"])
            self._cmd_list.append(base_args + ["package", "-h"])
            # Add argument list with non_existent_package
            self._cmd_list.append(base_args + ["pkg", "non_existent_package"])
            self._cmd_list.append(base_args + ["package", "non_existent_package"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips describe package ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        err_str = "usage: To use, type `geoips describe package <package_name>`"
        assert err_str in error

    def check_output(self, args, output):
        """Ensure that the 'geoips describe package ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            usg_str = "usage: To use, type `geoips describe package <package_name>`"
            assert usg_str in output
        else:
            # Checking that output from geoips describe package command is valid
            expected_outputs = [
                "Docstring",
                "GeoIPS Package",
                "Package Path",
                "Source Code",
                "Version Number",
            ]
            for output_item in expected_outputs:
                assert f"{output_item}:" in output


test_sub_cmd = TestGeoipsDescribePackage()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips describe package ...' commands.

    This test covers every valid combination of commands for the 'geoips describe
    package' command. We also test invalid commands, to ensure that the proper help
    documentation is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'describe', 'package'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
