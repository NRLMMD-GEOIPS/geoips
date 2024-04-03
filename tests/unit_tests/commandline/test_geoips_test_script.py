"""Unit test for GeoIPS CLI `test script` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest
from tests.unit_tests.commandline.test_geoips_run import TestGeoipsRun


class TestGeoipsTestScript(BaseCliTest):
    """Unit Testing Class for Test Script Sub-Command."""

    @property
    def all_possible_subcommand_combinations(self):
        """A stotastic list of commands used by the GeoipsTestScript command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._test_script_args
            for arg_list in TestGeoipsRun().all_possible_subcommand_combinations:
                # Replacing 'run' with 'test', as they currently are the same command
                # We'll need to strip TestGeoipsRun._cmd_list and place that here
                # once we've changed 'run' to implement 'run_procflow'
                arg_list[1] = "test"
                # Inserting 'script' as this command is called via 'geoips test script',
                # instead of what's currently called via 'geoips run <script_name>'
                arg_list.insert(2, "script")
                self._cmd_list.append(arg_list)
            # Add arg lists to run base integration tests
            self._cmd_list.append(base_args + ["--integration", "base_install.sh"])
            self._cmd_list.append(base_args + ["--integration", "base_test.sh"])
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
        elif "-i" in args:
            checklists = {
                "dependencies": ["git", "python"],
                "test_data_names": ["test_data_amsr2", "test_data_noaa_aws"],
                "test_names": [
                    "amsr2.config_based_no_compare.sh",
                    "amsr2_ocean.tc.windspeed.imagery_clean.sh",
                    "test_interfaces",
                ],
            }
            # check to make sure that the integration tests ran
            # (doesn't matter if they fail or pass)
            for checklist_key in list(checklists.keys()):
                checklist = checklists[checklist_key]
                for item in checklist:
                    if checklist_key == "test_names" and args[-1] == "base_test.sh":
                        assert item in output
                    if checklist_key != "test_names":
                        assert item in output
        else:
            # Checking that output from geoips test script command reports succeeds
            assert "Return value:" in output


test_sub_cmd = TestGeoipsTestScript()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.all_possible_subcommand_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_all_command_combinations(args):
    """Test all 'geoips test script ...' commands.

    This test covers every valid combination of commands for the 'geoips test script'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'test', 'script'])
    """
    test_sub_cmd.test_all_command_combinations(args)
