"""Unit test for GeoIPS CLI `list-plugins` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""
from importlib import resources
import json
import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListPlugins(BaseCliTest):
    """Unit Testing Class for GeoipsListPlugins Command."""

    @property
    def all_possible_subcommand_combinations(self):
        """A list of every possible call signature for the GeoipsListPlugins command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = [self._list_plugins_args]
            for pkg_name in self.plugin_packages:
                self._cmd_list.append(
                    self._list_plugins_args + ["-p", pkg_name]
                )
            # Add argument list which invokes the help message for this command
            self._cmd_list.append(["geoips", "list-plugins", "-h"])
            # Add argument list with a non-existent package name
            self._cmd_list.append(
                ["geoips", "list-plugins", "-p", "non_existent_package"]
            )
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips list-plugins ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # bad command has been provided, check the contents of the error message
        assert args != ["geoips", "list-plugins"]
        assert "usage: To use, type `geoips list-plugins`" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips list-plugins ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        if "usage: To use, type" in output:
            # -h has been called, check help message contents for this command
            assert args == ["geoips", "list-plugins", "-h"]
            assert "To use, type `geoips list-plugins`" in output
        else:
            # The args provided are valid, so test that the output is actually correct
            headers = [
                "GeoIPS Package", "Interface", "Interface_type",
                "Family", "Plugin Name", "Relative Path",
            ]
            # Assert that the correct headers exist in the CLI output
            for header in headers:
                assert header in output

            if "-p" in args:
                # certain package has been selected, ensure we found every pkg-plugin
                pkg_names = [args[-1]]
            else:
                # all packages selected, ensure that we found every plugin
                pkg_names = self.plugin_packages
            for pkg_name in pkg_names:
                plugin_registry = json.load(
                    open(
                        str(resources.files(pkg_name) / "registered_plugins.json"), "r"
                    )
                )
                for interface_type in ["module_based", "yaml_based"]:
                    # check each type of interface
                    if interface_type in plugin_registry:
                        # if that interface type is within the registry, loop over the
                        # found interfaces
                        for interface_name in plugin_registry[interface_type]:
                            # search the interface's portion of the registry and assert
                            # that each plugin found within it has been reported in the
                            # CLI"s output
                            interface_registry = plugin_registry[
                                interface_type
                            ][interface_name]
                            for plugin_name in interface_registry:
                                assert plugin_name in list(interface_registry.keys())

test_sub_cmd = TestGeoipsListPlugins()

@pytest.mark.parametrize(
        "args",
        test_sub_cmd.all_possible_subcommand_combinations,
        ids=test_sub_cmd.generate_id,
)
def test_all_command_combinations(args):
    """Test all 'geoips list-plugins ...' commands.

    This test covers every valid combination of commands for the
    'geoips list-plugins' command. We also test invalid commands, to ensure that
    the proper help documentation  is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'list-plugins'])
    """
    test_sub_cmd.test_all_command_combinations(args)
