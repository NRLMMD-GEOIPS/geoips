# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `test workflow` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from geoips.interfaces import workflows
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsTestWorkflow(BaseCliTest):
    """Unit Testing Class for Expand Command."""

    @property
    def command_combinations(self):
        """A list of call signatures for the TestGeoipsTestWorkflow command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = ["geoips", "test", "workflow"]
            self._cmd_list = []
            self._cmd_list.append(base_args + ["test_product"])
            self._cmd_list.append(base_args + ["test_workflow"])
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non existent workflow
            self._cmd_list.append(base_args + ["non_existent_workflow"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips test workflow ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # This can occur for the 'test_product' unit test if the data is missing on your
        # device
        if "could not be associated with one or more existing file paths." in error:
            assert "1 validation error for" in error
            return

        assert "To use, type `geoips test workflow <workflow_type>" in error

        if "non_existent" in args[-1]:
            assert "Error: could not load workflow plugin under name" in error
            return

        wf = workflows.get_plugin(args[-1])

        if wf.get("test") is None:
            assert "cannot test" in error and "missing a ``test`` section." in error
        else:
            assert (
                "Error: ``test`` parameters differ from the set of allowable parameters"
                " that the Order Based Procflow can operate on."
            ) in error

    def check_output(self, args, output):
        """Ensure that the 'geoips test workflow ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert "To use, type `geoips test workflow <workflow_type>" in output
        else:
            assert "has finished processing." in output


test_sub_cmd = TestGeoipsTestWorkflow()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, caplog, args):
    """Test all 'geoips test workflow ...' commands.

    This test covers valid combinations of commands for the 'geoips test workflow'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'test', 'workflow'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args=args, caplog=caplog)
