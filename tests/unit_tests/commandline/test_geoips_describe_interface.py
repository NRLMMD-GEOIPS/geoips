# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `describe interface` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from geoips import interfaces
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsDescribeInterface(BaseCliTest):
    """Unit Testing Class for Describe Interface Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the this command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = ["geoips", "describe"]
            # add arguments for retrieving each GeoIPS Interface
            for interface_name in interfaces.__all__:
                interface_name = interface_name.replace("_", "-")
                for alias in self.alias_mapping[interface_name] + [interface_name]:
                    self._cmd_list.append(base_args + [alias])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non_existent_interface
            self._cmd_list.append(base_args + ["non_existent_interface"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips describe interface ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        err_str = "usage: To use, type `geoips describe <interface_name> <sub-cmd> ...`"
        assert err_str in error

    def check_output(self, args, output):
        """Ensure that the 'geoips describe interface ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            usg_str = (
                "usage: To use, type `geoips describe <interface_name> <sub-cmd> ...`"
            )
            assert usg_str in output
        else:
            # Checking that output from geoips describe package command is valid
            expected_outputs = [
                "Absolute Path",
                "Docstring",
                "Interface",
                "Interface Type",
                "Supported Families",
            ]
            for output_item in expected_outputs:
                assert f"{output_item}:" in output


test_sub_cmd = TestGeoipsDescribeInterface()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips describe interface ...' commands.

    This test covers every valid combination of commands for the 'geoips describe
    interface' command. We also test invalid commands, to ensure that the proper help
    documentation is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (I.e.
          ['geoips', 'describe', 'interface'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
