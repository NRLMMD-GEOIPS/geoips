# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for GeoIPS CLI `list plugins` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""

from importlib import resources
import json
import pytest

from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsListPlugins(BaseCliTest):
    """Unit Testing Class for List Plugins Command."""

    @property
    def command_combinations(self):
        """A list of every possible call signature for the GeoipsListPlugins command.

        This includes failing cases as well.
        """
        if not hasattr(self, "_cmd_list"):
            base_args = ["geoips", "list", "plugins"]
            alias_args = ["geoips", "ls", "plugins"]
            self._cmd_list = [base_args, alias_args]
            for argset in [base_args, alias_args]:
                for pkg_name in self.plugin_package_names:
                    self._cmd_list.append(argset + ["-p", pkg_name])
            # Add argument list invoking the --columns flag
            self._cmd_list.append(base_args + ["--columns", "package", "interface"])
            self._cmd_list.append(base_args + ["--columns", "plugin_type", "family"])
            self._cmd_list.append(base_args + ["--columns", "relpath", "source_names"])
            self._cmd_list.append(base_args + ["--columns", "plugin_name", "relpath"])
            self._cmd_list.append(alias_args + ["--columns", "package", "interface"])
            self._cmd_list.append(alias_args + ["--columns", "plugin_type", "family"])
            self._cmd_list.append(alias_args + ["--columns", "relpath", "source_names"])
            self._cmd_list.append(alias_args + ["--columns", "plugin_name", "relpath"])
            # Add argument list which invokes the help message for this command
            self._cmd_list.append(base_args + ["-h"])
            self._cmd_list.append(alias_args + ["-h"])
            # Add argument list with a non-existent package name
            self._cmd_list.append(base_args + ["-p", "non_existent_package"])
            self._cmd_list.append(alias_args + ["-p", "non_existent_package"])
        return self._cmd_list

    def check_error(self, args, error):
        """Ensure that the 'geoips list plugins ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        # bad command has been provided, check the contents of the error message
        assert args != ["geoips", "list", "plugins"] and args != [
            "geoips",
            "ls",
            "plugins",
        ]
        assert "usage: To use, type `geoips list plugins`" in error

    def check_output(self, args, output):
        """Ensure that the 'geoips list plugins ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        if "usage: To use, type" in output:
            # -h has been called, check help message contents for this command
            assert "-h" in args
            assert "To use, type `geoips list plugins`" in output
        else:
            # The args provided are valid, so test that the output is actually correct
            selected_cols = self.retrieve_selected_columns(args)
            headers = {
                "GeoIPS Package": "package",
                "Interface Name": "interface",
                "Interface Type": "plugin_type",
                "Family": "family",
                "Plugin Name": "plugin_name",
                "Relative Path": "relpath",
            }
            # Assert that the correct headers exist in the CLI output
            self.assert_correct_headers_in_output(output, headers, selected_cols)

            if "-p" in args:
                # certain package has been selected, ensure we found every pkg-plugin
                pkg_names = [args[-1]]
            else:
                # all packages selected, ensure that we found every plugin
                pkg_names = self.plugin_package_names
            for pkg_name in pkg_names:
                with open(
                    str(resources.files(pkg_name) / "registered_plugins.json"), "r"
                ) as fo:
                    plugin_registry = json.load(fo)
                for interface_type in ["module_based", "yaml_based"]:
                    # check each type of interface
                    if interface_type in plugin_registry:
                        # if that interface type is within the registry, loop over the
                        # found interfaces
                        for interface_name in plugin_registry[interface_type]:
                            # search the interface's portion of the registry and assert
                            # that each plugin found within it has been reported in the
                            # CLI"s output
                            interface_registry = plugin_registry[interface_type][
                                interface_name
                            ]
                            for plugin_name in interface_registry:
                                assert plugin_name in list(interface_registry.keys())


test_sub_cmd = TestGeoipsListPlugins()


@pytest.mark.parametrize(
    "args",
    test_sub_cmd.command_combinations,
    ids=test_sub_cmd.generate_id,
)
def test_command_combinations(monkeypatch, args):
    """Test all 'geoips list plugins ...' commands.

    This test covers every valid combination of commands for the
    'geoips list plugins' command. We also test invalid commands, to ensure that
    the proper help documentation  is provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'list', 'plugins'])
    """
    test_sub_cmd.test_command_combinations(monkeypatch, args)
