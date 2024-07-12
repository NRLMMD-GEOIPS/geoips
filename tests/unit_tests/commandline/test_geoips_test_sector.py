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

"""Unit test for GeoIPS CLI `test sector` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from os import environ

import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsTestSector(BaseCliTest):
    """Unit Testing Class for Test Sector Command."""

    @property
    def command_combinations(self):
        """A list of call signatures for the GeoipsTestSector command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = self._test_sector_args
            self._cmd_list = []
            # Only creating two sectors here as they'll hit the same code locations.
            # Just want to make sure we get 100% coverage and don't create a ton of new
            # files.
            self._cmd_list.append(base_args + ["goes_east"])
            self._cmd_list.append(
                base_args + ["japan", "--outdir", f"{environ['GEOIPS_OUTDIRS']}"]
            )
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non existent sector
            self._cmd_list.append(base_args + ["non_existent_sector"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips test sector ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        assert "To use, type `geoips test sector <sector_name>" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips test sector ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            assert "To use, type `geoips test sector <sector_name>" in output
        else:
            assert f"{args[3]}.png" in output


test_sub_cmd = TestGeoipsTestSector()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips test sector ...' commands.

    This test covers valid combinations of commands for the 'geoips test sector'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'test', 'sector'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
