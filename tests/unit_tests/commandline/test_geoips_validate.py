# # # Distribution Statement A. Approved for public release. Distribution is unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Unit test for GeoIPS CLI `validate` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from glob import glob
from importlib import resources
from numpy.random import rand
import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsValidate(BaseCliTest):
    """Unit Testing Class for 'geoips validate' Command."""

    @property
    def command_combinations(self):
        """A list of stochastic call signatures for the GeoipsValidate command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._validate_args
            rand_threshold = 0.85
            # validate some subset plugins from all installed packages
            for pkg_name in self.plugin_package_names:
                pkg_path = str(resources.files(pkg_name) / "plugins")
            for plugin_type in ["modules", "yaml"]:
                if plugin_type == "modules":
                    plugin_path_str = f"{pkg_path}/{plugin_type}/**/*.py"
                else:
                    plugin_path_str = f"{pkg_path}/{plugin_type}/**/*.yaml"
                plugin_paths = sorted(glob(plugin_path_str, recursive=True))
                for plugin_path in plugin_paths:
                    if rand() > rand_threshold:
                        self._cmd_list.append(base_args + [plugin_path])
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips validate ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        assert "usage: To use, type `geoips validate <file_path>`" in error
        assert "is invalid." in error

    def check_output(self, args, output):
        """Ensure that the 'geoips validate ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert "usage: To use, type `geoips validate <file_path>`" in output
        else:
            # Checking that output from geoips validate command reports valid
            assert "is valid." in output


test_sub_cmd = TestGeoipsValidate()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips validate ...' commands.

    This test covers every valid combination of commands for the 'geoips validate'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'validate'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
