"""Unit test for GeoIPS CLI `list` command.

See geoips/commandline/ancillary_info/cmd_instructions.yaml for more information.
"""
import json
from importlib import resources
import pytest
import subprocess

from geoips import interfaces
from tests.unit_tests.commandline.cli_top_level_tester import BaseCliTest


class TestGeoipsList(BaseCliTest):
    """Unit Testing Class for GeoipsList Command."""

    @property
    def all_possible_subcommand_combinations(self):
        """Check every possible call signature for the GeoipsList command.

        This includes failing cases as well.

        Parameters
        ----------
        base_args: list of str
            - ["geoips", "list"] occurs for this case
        """
        if not hasattr(self, "_cmd_list"):
            self._cmd_list = []
            base_args = self._list_args
            for pkg_name in self.plugin_packages + ["all"]:
                for interface_name in interfaces.__all__:
                    if pkg_name != "all":
                        args = base_args + [interface_name, "-p", pkg_name]
                    else:
                        args = base_args + [interface_name]
                    self._cmd_list.append(args)
            # Add argument list with a non-existent interface
            self._cmd_list.append(base_args + ["non_existent_interface"])
            # Add argument list with an existing interface but non-existent package
            self._cmd_list.append(
                base_args + ["algorithms", "-p", "non_existent_package"]
            )
        return self._cmd_list


test_sub_cmd = TestGeoipsList()
plugin_packages = test_sub_cmd.plugin_packages

@pytest.mark.parametrize(
        "args",
        test_sub_cmd.all_possible_subcommand_combinations,
        ids=test_sub_cmd.generate_id,
)
def test_all_command_combinations(args):
    """Test all 'geoips list ...' commands.

    This test covers every valid combination of commands for the 'geoips list' command.
    We also test invalid commands, to ensure that the proper help documentation is
    provided for those using the command incorrectly.

    Parameters
    ----------
    args: 2D array of str
        - List of arguments to call the CLI with (ie. ['geoips', 'list', 'algorithms'])
    """
    print(f"Calling args: {args}")
    # Call the CLI via the provided commands with subprocess.Popen
    prc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Capture the output using subprocess.PIPE, then decode it.
    output, error = prc.communicate()
    output, error = output.decode(), error.decode()
    print(output)
    assert len(output) or len(error) # assert that some output was created
    prc.terminate()
    if "usage: To use, type" in error:
        check_list_error(args, error)
    else:
        check_list_output(args, output)


def check_list_error(args, error):
    """Ensure that the 'geoips list ...' error output is correct.

    Parameters
    ----------
    args: 2D list of str
        - The arguments used to call the CLI (expected to fail)
    error: str
        - Multiline str representing the error output of the CLI call
    """
    if args[2] in interfaces.__all__:
        # interface exists, so check that the package name is incorrect
        assert args[-1] not in plugin_packages
        usg_str = "geoips list: error: argument --package/-p: invalid choice: "
        usg_str += f"'{args[-1]}' (choose from"
        assert usg_str in error
    else:
        usg_str = "geoips list: error: argument interface_name: invalid choice: "
        usg_str += f"'{args[2]}' (choose from"
        assert usg_str in error


def check_list_output(args, output):
    """Ensure that the 'geoips list ...' successful output is correct.

    Parameters
    ----------
    args: 2D list of str
        - The arguments used to call the CLI
    output: str
        - Multiline str representing the output of the CLI call
    """
    # The args provided are valid, so test that the output is actually correct
    interface = getattr(interfaces, args[2])
    interface_type = interface.interface_type
    if "No plugins found under" in output and "-p" in args:
        # No plugins were found under the selected interface, within a
        # certain package; ensure that is correct.
        plugin_registry = json.load(
            open(
                str(resources.files(args[-1]) / "registered_plugins.json"), "r"
            )
        )
        # assert that the provided interface doesn't exist within that package's
        # plugin registry
        assert interface.name not in list(plugin_registry[interface_type].keys())
    else:
        # Assert that the correct headers exist in the CLI output
        headers = [
            "GeoIPS Package", "Interface", "Interface_type", "Family",
            "Plugin Name", "Relative Path",
        ]
        for header in headers:
            assert header in output