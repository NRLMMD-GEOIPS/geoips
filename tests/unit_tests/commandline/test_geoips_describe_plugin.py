# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `describe plugin` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

import pytest

from geoips import interfaces
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest
from geoips.geoips_utils import get_numpy_seeded_random_generator


class TestGeoipsDescribePlugin(BaseCliTest):
    """Unit Testing Class for Describe Plugin Command."""

    rand_threshold = 0.10
    random_generator = get_numpy_seeded_random_generator()

    @property
    def command_combinations(self):
        """A stochastic list of commands used for the GeoipsDescribePlugin command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = ["geoips", "describe"]
            # validate all plugins from package all packages
            for interface_name in interfaces.__all__:
                interface = getattr(interfaces, interface_name)
                # If there happen to be no plugins for a given interface, just skip, do
                # not fail catastrophically. This allows defining interfaces in the
                # geoips repo, even if there are no plugins of that interface directly
                # in the main geoips repo.
                if (
                    interface_name
                    not in interface.plugin_registry.registered_plugins[
                        interface.interface_type
                    ]
                ):
                    continue
                interface_registry = interface.plugin_registry.registered_plugins[
                    interface.interface_type
                ][interface_name]
                for idx, plugin_name in enumerate(interface_registry):
                    interface_name = interface_name.replace("_", "-")
                    for alias in self.alias_mapping[interface_name] + [interface_name]:
                        # Randomly select some plugins to perform 'describe plugin' on.
                        # Doing this because there are too many plugins to test in a
                        # timely manner
                        if interface.name == "products":
                            for subplg_name in interface_registry[plugin_name]:
                                do_describe_plugin = (
                                    self.random_generator.random() < self.rand_threshold
                                )
                                if do_describe_plugin or idx == 0:
                                    combined_name = f"{plugin_name}.{subplg_name}"
                                    self._cmd_list.append(
                                        base_args + [alias, combined_name],
                                    )
                        else:
                            do_describe_plugin = (
                                self.random_generator.random() < self.rand_threshold
                            )
                            if do_describe_plugin or idx == 0:
                                self._cmd_list.append(
                                    base_args + [alias, plugin_name],
                                )
            # Add argument list to retrieve help message
            self._cmd_list.append(base_args + ["-h"])
            # Add argument list with non_existent_interface
            self._cmd_list.append(base_args + ["non_existent_interface", "Infrared"])
            # Add argument list with non_existent_plugin
            self._cmd_list.append(base_args + ["algorithms", "non_existent_plugin"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips describe plugin ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # An error occurred using args. Assert that args is not valid and check the
        # output of the error.
        err_str = "usage: To use, type `geoips describe <interface_name> <sub-cmd> ...`"
        assert err_str in error

    def check_output(self, args, output):
        """Ensure that the 'geoips describe plugin ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        # The args provided are valid, so test that the output is actually correct
        if "-h" in args:
            usg_str = (
                "usage: To use, type `geoips describe <interface_name> <sub-cmd> ...`"
            )
            assert usg_str in output
        else:
            # Checking that output from geoips describe plugin command is valid
            interface_name = args[3]
            expected_outputs = [
                "Docstring",
                "Family",
                "Interface",
                "Package",
                "Plugin Type",
                "Relative Path",
            ]
            if interface_name == "products":
                expected_outputs.append("source_names")
            elif interface_name in interfaces.module_based_interfaces:
                expected_outputs.append("signature")
            for output_item in expected_outputs:
                assert f"{output_item}:" in output


test_sub_cmd = TestGeoipsDescribePlugin()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips describe plugin ...' commands.

    This test covers every valid combination of commands for the 'geoips describe
    plugin' command. We also test invalid commands, to ensure that the proper help
    documentation is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'describe', 'plugin'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args=args)
