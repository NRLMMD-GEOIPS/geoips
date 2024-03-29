"""Unit test for GeoIPS CLI `list scripts` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from glob import glob
from importlib import resources
from os.path import basename
import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListScripts(BaseCliTest):
    """Unit Testing Class for List Scripts Sub-Command."""

    @property
    def all_possible_subcommand_combinations(self):
        """A list of every possible call signature for the GeoipsListScripts command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._list_scripts_args
            for pkg_name in self.plugin_packages + ["all"]:
                if pkg_name != "all":
                    args = base_args + ["-p", pkg_name]
                else:
                    args = base_args
                self._cmd_list.append(args)
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with a non-existent package
            self._cmd_list.append(base_args + ["-p", "non_existent_package"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips list scripts ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        assert args != ["geoips", "list", "scripts"]
        for pkg_name in self.plugin_packages:
            assert args != ["geoips", "list", "scripts", "-p", pkg_name]
        assert "usage: To use, type `geoips list scripts`" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips list scripts ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert "usage: To use, type `geoips list scripts`" in output
        else:
            # Checking tabular output from the list-scripts command
            if "-p" in args:
                # A certain package was requested, generate a list of all scripts from
                # that package.
                pkg_names = [args[-1]]
            else:
                # no `-p` flag, check all packages instead.
                pkg_names = self.plugin_packages
            script_names = []
            for pkg_name in pkg_names:
                script_names += sorted(
                    [
                        basename(fpath)
                        for fpath in glob(
                            str(resources.files(pkg_name) / "../tests/scripts" / "*.sh")
                        )
                    ]
                )
            for script_name in script_names:
                assert script_name in "".join(
                    output.strip().replace("\n", "").replace("│", "").split()
                )
            # Assert that the correct headers exist in the CLI output
            headers = ["GeoIPS Package", "Filename"]
            for header in headers:
                assert header in output


test_sub_cmd = TestGeoipsListScripts()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.all_possible_subcommand_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_all_command_combinations(args):
    """Test all 'geoips list scripts ...' commands.

    This test covers every valid combination of commands for the 'geoips list scripts'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'list', 'scripts'])
    """
    test_sub_cmd.test_all_command_combinations(args)
