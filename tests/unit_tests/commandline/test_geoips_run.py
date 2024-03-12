"""Unit test for GeoIPS CLI `run` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from glob import glob
from importlib import resources
from numpy.random import rand
from os import listdir, environ
from os.path import basename
import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsRun(BaseCliTest):
    """Unit Testing Class for GeoipsRun Command."""

    @property
    def all_possible_subcommand_combinations(self):
        """A list of every possible call signature for the GeoipsRun command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._run_args
            # select a small random amount of tests to call via geoips run
            for pkg_name in self.plugin_packages:
                script_names = sorted(
                    [
                        basename(script_path)
                        for script_path in glob(
                            str(resources.files(pkg_name) / "../tests/scripts/*.sh")
                        )
                    ]
                )
                for script_name in script_names:
                    do_geoips_run = rand() < 0.15
                    test_data_found = (
                        f"test_data_{script_name.split('.', 1)[0]}"
                        in listdir(str(environ["GEOIPS_TESTDATA_DIR"]))
                    )
                    if do_geoips_run and test_data_found and len(self._cmd_list) < 4:
                        self._cmd_list.append(base_args + ["-p", pkg_name, script_name])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non existent package
            self._cmd_list.append(
                base_args
                + [
                    "-p",
                   "non_existent_package",
                   "abi.static.Infrared.imagery_annotated.sh"
                ]
            )
            # Add argument list with non existent script name in default geoips pkg
            self._cmd_list.append(
                base_args + ["non_existent_script_name"]
            )
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips run ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        assert "To use, type `geoips run -p <package_name> <script_name>`" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips run ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert "To use, type `geoips run -p <package_name> <script_name>`" in output
        else:
            # Checking that output from geoips run command reports succeeds
            assert "Return value: 0" in output


test_sub_cmd = TestGeoipsRun()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.all_possible_subcommand_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_all_command_combinations(args):
    """Test all 'geoips run ...' commands.

    This test covers every valid combination of commands for the 'geoips run'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'run'])
    """
    test_sub_cmd.test_all_command_combinations(args)
