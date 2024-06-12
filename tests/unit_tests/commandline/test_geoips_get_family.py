"""Unit test for GeoIPS CLI `get family` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from geoips import interfaces
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsGetFamily(BaseCliTest):
    """Unit Testing Class for Get Family Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsGetFamily command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._get_family_args
            # add each family argument from every interface to the command arg list
            for interface_name in interfaces.__all__:
                interface = getattr(interfaces, interface_name)
                for alias in self.alias_mapping[interface_name] + [interface_name]:
                    for family_name in interface.supported_families:
                        self._cmd_list.append(
                            base_args + [alias, "fam", family_name]
                        )
                        self._cmd_list.append(
                            base_args + [alias, "family", family_name]
                        )
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non_existent_interface
            self._cmd_list.append(
                base_args + ["non_existent_interface", "fam", "standard"]
            )
            self._cmd_list.append(
                base_args + ["non_existent_interface", "family", "standard"]
            )
            # Add argument list with non_existent_family
            self._cmd_list.append(
                base_args + ["algorithms", "fam", "non_existent_family"]
            )
            self._cmd_list.append(
                base_args + ["algorithms", "family", "non_existent_family"]
            )
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that `geoips get <interface_name> family ...` error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        err_str = "usage: To use, type `geoips get <interface_name> <sub-cmd> ...`"
        assert err_str in error

    def check_output(self, args, output):
        """Ensure that the 'geoips get family ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            usg_str = "usage: To use, type `geoips get <interface_name> <sub-cmd> ...`"
            assert usg_str in output
        else:
            # Checking that output from geoips get plugin command is valid
            expected_outputs = [
                "Docstring",
                "Family Name",
                "Family Path",
                "Interface Name",
                "Interface Type",
                "Required Args / Schema",
            ]
            for output_item in expected_outputs:
                assert f"{output_item}:" in output


test_sub_cmd = TestGeoipsGetFamily()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips get <interface_name> family <family_name> ...' commands.

    This test covers every valid combination of commands for the
    'geoips get <interface_name> family <family_name>' command. We also test invalid
    commands, to ensure that the proper help documentation is provided for those using
    the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with ie:
        - ['geoips', 'get', <interface_name>, 'family', <family_name>])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
