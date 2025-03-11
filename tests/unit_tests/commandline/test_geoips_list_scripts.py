# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `list scripts` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from glob import glob
from importlib import resources
from os.path import basename
import pytest

from geoips.geoips_utils import is_editable

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListScripts(BaseCliTest):
    """Unit Testing Class for List Scripts Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsListScripts command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = ["geoips", "list", "scripts"]
            alias_args = ["geoips", "ls", "scripts"]
            self._cmd_list = []
            for argset in [base_args, alias_args]:
                for pkg_name in self.plugin_package_names + ["all"]:
                    if pkg_name != "all":
                        args = argset + ["-p", pkg_name]
                    else:
                        args = argset
                    self._cmd_list.append(args)
            # Add argument list which invokes the --columns flag
            self._cmd_list.append(base_args + ["--columns", "package", "filename"])
            self._cmd_list.append(base_args + ["--columns", "filename"])
            self._cmd_list.append(base_args + ["--columns", "package"])
            self._cmd_list.append(alias_args + ["--columns", "package", "filename"])
            self._cmd_list.append(alias_args + ["--columns", "filename"])
            self._cmd_list.append(alias_args + ["--columns", "package"])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            self._cmd_list.append(alias_args + ["-h"])
            # Add argument list with a non-existent package
            self._cmd_list.append(base_args + ["-p", "non_existent_package"])
            self._cmd_list.append(alias_args + ["-p", "non_existent_package"])
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
        editable = self.assert_non_editable_error_or_wrong_package(args, error)
        if editable:
            # An error occurred using args. Assert that args is not valid and check the
            # output of the error.
            assert args != ["geoips", "list", "scripts"] and args != [
                "geoips",
                "ls",
                "scripts",
            ]
            for pkg_name in self.plugin_package_names:
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
        elif "-p" not in args and any(
            [is_editable(pkg_name) for pkg_name in self.plugin_package_names]
        ):
            self.assert_non_editable_error_or_wrong_package(args, output)
        else:
            # Checking tabular output from the list-scripts command
            if "-p" in args:
                # A certain package was requested, generate a list of all scripts from
                # that package.
                pkg_names = [args[-1]]
            else:
                # no `-p` flag, check all packages instead.
                pkg_names = self.plugin_package_names
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
            if "--columns" not in args or "filenames" in args:
                # ensure that filenames have been outputted if we are going to test this
                for script_name in script_names:
                    assert script_name in "".join(
                        output.strip().replace("\n", "").replace("│", "").split()
                    )
            selected_cols = self.retrieve_selected_columns(args)
            # Assert that the correct headers exist in the CLI output
            headers = {"GeoIPS Package": "package", "Filename": "filename"}
            self.assert_correct_headers_in_output(output, headers, selected_cols)


test_sub_cmd = TestGeoipsListScripts()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips list scripts ...' commands.

    This test covers every valid combination of commands for the 'geoips list scripts'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'list', 'scripts'])
    """
    # if "-p" not in args and
    test_sub_cmd.test_command_combinations(monkeypatch, args)
