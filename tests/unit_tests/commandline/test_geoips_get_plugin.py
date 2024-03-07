"""Unit test for GeoIPS CLI `get plugin` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""
from numpy.random import rand
import pytest

from geoips import interfaces
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsGetPlugin(BaseCliTest):
    """Unit Testing Class for GeoipsGetPlugin Command."""

    rand_threshold = 0.10

    @property
    def all_possible_subcommand_combinations(self):
        """A list of every possible call signature for the GeoipsGetPlugin command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._get_plugin_args
            # validate all plugins from package geoips_clavrx
            for interface_name in interfaces.__all__:
                interface = getattr(interfaces, interface_name)
                interface_registry = interface.plugin_registry.registered_plugins[
                    interface.interface_type
                ][interface_name]
                for idx, plugin_name in enumerate(interface_registry):
                    # Randomly select some plugins to perform 'get plugin' on. Doing
                    # this because there are too many plugins to test in a timely manner
                    if interface.name == "products":
                        for subplg_name in interface_registry[plugin_name]:
                            do_get_plugin = rand() < self.rand_threshold
                            if do_get_plugin or idx == 0:
                                combined_name = f"{plugin_name}.{subplg_name}"
                                self._cmd_list.append(
                                    base_args + [interface.name, combined_name],
                                )
                    else:
                        do_get_plugin = rand() < self.rand_threshold
                        if do_get_plugin or idx == 0:
                            self._cmd_list.append(
                                base_args + [interface.name, plugin_name],
                            )
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non_existent_interface
            self._cmd_list.append(base_args + ["non_existent_interface", "Infrared"])
            # Add argument list with non_existent_plugin
            self._cmd_list.append(base_args + ["algorithms", "non_existent_plugin"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips get plugin ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        err_str = "usage: To use, type `geoips get plugin <interface_name> "
        err_str += "<plugin_name>`"
        assert err_str in error


    def check_output(self, args, output):
        """Ensure that the 'geoips get plugin ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            usg_str = "usage: To use, type `geoips get plugin <interface_name> "
            usg_str += "<plugin_name>`"
            assert usg_str in output
        else:
            # Checking that output from geoips get plugin command is valid
            interface_name = args[3]
            expected_outputs = [
                "docstring",
                "family",
                "interface",
                "package",
                "plugin_type",
                "relpath",
            ]
            if interface_name == "products":
                expected_outputs.append("source_names")
            elif interface_name in interfaces.module_based_interfaces:
                expected_outputs.append("signature")
            for output_item in expected_outputs:
                assert f"{output_item}:" in output

test_sub_cmd = TestGeoipsGetPlugin()

@pytest.mark.parametrize(
        "args",
        test_sub_cmd.all_possible_subcommand_combinations,
        ids=test_sub_cmd.generate_id,
)
def test_all_command_combinations(args):
    """Test all 'geoips get plugin ...' commands.

    This test covers every valid combination of commands for the 'geoips get plugin'
    command. We also test invalid commands, to ensure that the proper help documentation
    is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'get', 'plugin'])
    """
    test_sub_cmd.test_all_command_combinations(args)
