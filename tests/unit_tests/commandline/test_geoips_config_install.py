# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `config install` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsConfigInstall(BaseCliTest):
    """Unit Testing Class for Config Install Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsConfigInstall command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._config_install_args
            # add argument lists to install available test datasets
            for test_dataset_name in self.test_datasets:
                self._cmd_list.append(base_args + [test_dataset_name])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non existent test dataset
            self._cmd_list.append(base_args + ["non_existent_test_dataset"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips config install ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        assert "To use, type `geoips config install <test_dataset_name>`" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips config install ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert "To use, type `geoips config install <test_dataset_name>`" in output
        else:
            # Checking that output from geoips config install command succeeds
            dataset_exists = f"Test dataset '{args[-1]}' already exists"
            dataset_installed = f"Test dataset '{args[-1]}' has been installed under"
            # Assert that the data already exists or was installed successfully
            assert dataset_exists in output or dataset_installed in output


test_sub_cmd = TestGeoipsConfigInstall()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips config install ...' commands.

    This test covers every valid combination of commands for the 'geoips config install'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'config', 'install'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
