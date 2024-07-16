# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `get family` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from geoips import interfaces
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsGetFamily(BaseCliTest):
    """Unit Testing Class for Get Family Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsGetFamily command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._get_family_args
            # add each family argument from every interface to the command arg list
            for interface_name in interfaces.__all__:
                interface = getattr(interfaces, interface_name)
                for family_name in interface.supported_families:
                    self._cmd_list.append(base_args + [interface_name, family_name])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non_existent_interface
            self._cmd_list.append(base_args + ["non_existent_interface", "standard"])
            # Add argument list with non_existent_plugin
            self._cmd_list.append(base_args + ["algorithms", "non_existent_family"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips get family ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        err_str = "usage: To use, type `geoips get family <interface_name> "
        err_str += "<family_name>`"
        assert err_str in error

    def check_output(self, args, output):
        """Ensure that the 'geoips get family ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            usg_str = "usage: To use, type `geoips get family <interface_name> "
            usg_str += "<family_name>`"
            assert usg_str in output
        else:
            # Checking that output from geoips get plugin command is valid
            expected_outputs = [
                "Docstring",
                "Family Name",
                "Family Path",
                "Interface Name",
                "Interface Type",
                "Required Args / Schema",
            ]
            for output_item in expected_outputs:
                assert f"{output_item}:" in output


test_sub_cmd = TestGeoipsGetFamily()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips get family ...' commands.

    This test covers every valid combination of commands for the 'geoips get family'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'get', 'family'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
