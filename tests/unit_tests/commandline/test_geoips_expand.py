# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `expand` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest
import yaml

from geoips.pydantic_models.v1.workflows import WorkflowPluginModel
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsExpand(BaseCliTest):
    """Unit Testing Class for Expand Command."""

    @property
    def command_combinations(self):
        """A list of call signatures for the TestGeoipsExpand command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = ["geoips", "expand"]
            self._cmd_list = []
            self._cmd_list.append(base_args + ["test_product"])
            self._cmd_list.append(base_args + ["test_workflow"])
            # Can't test --color output as the raw string output cannot be read by
            # yaml.safe_load. We'll just have to visually test that one. (It works).
            # self._cmd_list.append(base_args + ["test_workflow", "--color"])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non existent workflow
            self._cmd_list.append(base_args + ["non_existent_workflow"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips expand ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        assert (
            "To use, type `geoips expand <workflow_name>" in error
            or "Error: could not load workflow plugin under name" in error
        )

    def check_output(self, args, output):
        """Ensure that the 'geoips expand ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert "To use, type `geoips expand <workflow_name>" in output
        else:
            wf = yaml.safe_load(output.strip())
            assert WorkflowPluginModel(**wf)


test_sub_cmd = TestGeoipsExpand()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips expand ...' commands.

    This test covers valid combinations of commands for the 'geoips expand'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'expand'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
