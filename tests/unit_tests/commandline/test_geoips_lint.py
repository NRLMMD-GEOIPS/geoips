# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `lint` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from geoips.geoips_utils import is_editable
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsLint(BaseCliTest):
    """Unit Testing Class for Lint Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the TestGeoipsLint command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = ["geoips", "lint"]
            self._cmd_list = [base_args]
            # select a small random amount of tests to call via geoips run
            for pkg_name in self.plugin_package_names:
                self._cmd_list.append(base_args + [pkg_name])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non existent package
            self._cmd_list.append(base_args + ["non_existent_package"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips lint ...' error output is correct.

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
            assert "To use, type `geoips lint <package-name>`" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips lint ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert "To use, type `geoips lint <package-name>`" in output
        elif not is_editable("geoips"):
            pytest.xfail("GeoIPS is not in editable mode and linting cannot proceed.")
        else:
            # Checking that output from geoips test linting command reports succeeds
            for linter in ["bandit", "black", "flake8"]:
                assert f"CALLING TEST:\n{linter}" in output
                assert f"TEST COMPLETE {linter}" in output


test_sub_cmd = TestGeoipsLint()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips lint ...' commands.

    This test covers every valid combination of commands for the 'geoips lint'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'lint'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
