# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `list test-datasets` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListTestDatasets(BaseCliTest):
    """Unit Testing Class for List Test Datasets Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsListTestDatasets cmd.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = ["geoips", "list", "test-datasets"]
            alias_args = ["geoips", "ls", "test-datasets"]
            self._cmd_list = [base_args, alias_args]
            # Add argument list which invokes the help message for this command
            self._cmd_list.append(["geoips", "list", "test-datasets", "-h"])
            self._cmd_list.append(["geoips", "ls", "test-datasets", "-h"])
            # Add argument list with a non-existent command call ("-p")
            self._cmd_list.append(["geoips", "list", "test-datasets", "-p", "geoips"])
            self._cmd_list.append(["geoips", "ls", "test-datasets", "-p", "geoips"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips list test-datasets ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # bad command has been provided, check the contents of the error message
        assert args != ["geoips", "list", "test-datasets"] and args != [
            "geoips",
            "ls",
            "test-datasets",
        ]
        assert "usage: To use, type `geoips list test-datasets`" in error
        assert "Error: '-p' flag is not supported for this command" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips list test-datasets ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        if "usage: To use, type" in output:
            # -h has been called, check help message contents for this command
            assert "-h" in args
            assert "usage: To use, type `geoips list test-datasets`" in output
        else:
            # The args provided are valid, so test that the output is actually correct
            assert args == ["geoips", "list", "test-datasets"] or args == [
                "geoips",
                "ls",
                "test-datasets",
            ]
            # Assert that the correct headers exist in the CLI output
            headers = ["Data Host", "Dataset Name"]
            for header in headers:
                assert header in output
            # Assert that we found every installed package
            for test_dataset_name in self.test_datasets:
                assert test_dataset_name in output


test_sub_cmd = TestGeoipsListTestDatasets()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips list test-datasets ...' commands.

    This test covers every valid combination of commands for the
    'geoips list test-datasets' command. We also test invalid commands, to ensure that
    the proper help documentation is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with
          (ie. ['geoips', 'list', 'test-datasets'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
