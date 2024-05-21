"""Unit test for GeoIPS CLI `test script` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from glob import glob
from importlib import resources
from numpy.random import rand
from os import listdir
from os.path import basename, exists
import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsTestScript(BaseCliTest):
    """Unit Testing Class for Test Script Sub-Command."""

    @property
    def command_combinations(self):
        """A stotastic list of commands used by the GeoipsTestScript command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._test_script_args
            test_data_dir = str(resources.files("geoips") / "../../test_data")
            # select a small random amount of tests to call via geoips run
            for pkg_name in self.plugin_package_names:
                script_paths = sorted(
                    [
                        script_path
                        for script_path in glob(
                            str(resources.files(pkg_name) / "../tests/scripts/*.sh")
                        )
                    ]
                )
                for script_path in script_paths:
                    do_geoips_run = rand() < 0.15
                    test_data_found = False
                    if do_geoips_run:
                        # This script has been randomly selected. Check it's contents
                        # to make sure that the test data for the script actually exists
                        with open(script_path, "r") as f:
                            for line in f.readlines():
                                if "geoips run" in line:
                                    for dir_name in listdir(test_data_dir):
                                        if dir_name in line:
                                            for string in line.split():
                                                if dir_name in string:
                                                    data_path = string.replace(
                                                        "$GEOIPS_TESTDATA_DIR",
                                                        test_data_dir,
                                                    )
                                                    if exists(data_path):
                                                        test_data_found = True
                                                        break
                                    break
                    if do_geoips_run and test_data_found and len(self._cmd_list) < 4:
                        self._cmd_list.append(
                            base_args + ["-p", pkg_name, basename(script_path)]
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
        elif "--integration" in args:
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
    test_sub_cmd.command_combinations,
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
