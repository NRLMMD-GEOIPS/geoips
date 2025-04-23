# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `test script` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsTestScript(BaseCliTest):
    """Unit Testing Class for Test Script Command."""

    @property
    def command_combinations(self):
        """A subset list of all possible commands used by the GeoipsTestScript command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = ["geoips", "test", "script"]
            # Add argument list executing a dummy test script
            self._cmd_list.append(base_args + ["cli_dummy_script.sh"])
            # Do the same thing specifying which package it comes from
            self._cmd_list.append(base_args + ["-p", "geoips", "cli_dummy_script.sh"])
            # Add argumetn list executing a dummy integration test
            self._cmd_list.append(
                base_args
                + [
                    "--integration",
                    "cli_dummy_integration.sh",
                ],
            )
            # Do the same thing specifying which package it comes from
            self._cmd_list.append(
                base_args
                + [
                    "-p",
                    "geoips",
                    "--integration",
                    "cli_dummy_integration.sh",
                ],
            )
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non existent package
            self._cmd_list.append(
                base_args
                + [
                    "-p",
                    "non_existent_package",
                    "abi.static.Infrared.imagery_annotated.sh",
                ]
            )
            # Add argument list with non existent script name in default geoips pkg
            self._cmd_list.append(base_args + ["non_existent_script_name"])
            # Add arg list to run integration tests from another package (will fail)
            self._cmd_list.append(
                base_args + ["-p", "data_fusion", "--integration", "base_test.sh"]
            )
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips test script ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        editable = self.assert_non_editable_error_or_wrong_package(args, error)
        if editable:
            # An error occurred using args. Assert that args is not valid and check the
            # output of the error.
            assert (
                "geoips test script -p <package_name> <--integration> <script_name>`"
                in error
            )

    def check_output(self, args, output):
        """Ensure that the 'geoips test script ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert (
                "geoips test script -p <package_name> <--integration> <script_name>`"
                in output
            )
        elif "--integration" in args:
            assert "I ran a dummy integration test." in output
        else:
            # Checking that output from geoips test script command reports succeeds
            assert "I ran a dummy test script." in output


test_sub_cmd = TestGeoipsTestScript()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips test script ...' commands.

    This test covers every valid combination of commands for the 'geoips test script'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'test', 'script'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
