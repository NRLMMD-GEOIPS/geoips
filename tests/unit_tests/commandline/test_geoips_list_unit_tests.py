"""Unit test for GeoIPS CLI `list unit-tests` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from glob import glob
from importlib.resources import files
from os import listdir
from os.path import basename
import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListUnitTests(BaseCliTest):
    """Unit Testing Class for List Unit Tests Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsListUnitTests command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = self._list_unit_tests_args
            self._cmd_list = [base_args]
            for pkg_name in self.plugin_package_names:
                self._cmd_list.append(base_args + ["-p", pkg_name])
            # Add argument list which invokes the help message for this command
            self._cmd_list.append(["geoips", "list", "unit-tests", "-h"])
            # Add argument list with a non-existent package
            self._cmd_list.append(
                ["geoips", "list", "unit-tests", "-p", "non_existent_package"]
            )
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips list unit-tests ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        editable = self.assert_non_editable_error_or_wrong_package(args, error)
        if editable:
            # bad command has been provided, check the contents of the error message
            assert args != ["geoips", "list", "unit-tests"]
            assert "usage: To use, type `geoips list unit-tests" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips list unit-tests ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        if "usage: To use, type" in output:
            # -h has been called, check help message contents for this command
            assert args == ["geoips", "list", "unit-tests", "-h"]
            assert "usage: To use, type `geoips list unit-tests" in output
        else:
            # The args provided are valid, so test that the output is actually correct
            # Assert that the correct headers exist in the CLI output
            headers = ["GeoIPS Package", "Unit Test Directory", "Unit Test Name"]
            for header in headers:
                assert header in output
            if "-p" in args:
                pkg_name = args[-1]
            else:
                pkg_name = "geoips"
            unit_test_dir = str(files(pkg_name) / "../tests/unit_tests")
            # Assert that we found every unit test
            for subdir_name in listdir(unit_test_dir):
                for unit_test in sorted(
                    glob(f"{unit_test_dir}/{subdir_name}/test_*.py")
                ):
                    assert basename(unit_test) in output


test_sub_cmd = TestGeoipsListUnitTests()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips list unit-tests ...' commands.

    This test covers every valid combination of commands for the
    'geoips list unit-tests' command. We also test invalid commands, to ensure that
    the proper help documentation is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'list', 'unit-tests'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
