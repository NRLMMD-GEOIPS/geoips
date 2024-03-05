"""Semi-Abstract CLI Test Class implementing attributes shared by sub-commands."""
import abc
import subprocess

from geoips.geoips_utils import get_entry_point_group

class BaseCliTest(abc.ABC):
    """Top-Level CLI Test Class which implements shared attributes for sub-commands."""

    _list_args = ["geoips", "list"]
    _list_interfaces_args = ["geoips", "list-interfaces"]
    _list_plugins_args = ["geoips", "list-plugins"]
    _list_packages_args = ["geoips", "list-packages"]
    _list_scripts_args = ["geoips", "list-scripts"]
    arg_list = [
        _list_args,
        _list_interfaces_args,
        _list_plugins_args,
        _list_packages_args,
        _list_scripts_args,
    ]

    def generate_id(self, args):
        """Generate an ID for the test-arguments provided."""
        return " ".join(args)

    @property
    def plugin_packages(self):
        """List of names of every installed GeoIPS package."""
        if not hasattr(self, "_plugin_packages"):
            self._plugin_packages = [
                ep.value for ep in get_entry_point_group("geoips.plugin_packages")
            ]
        return self._plugin_packages

    @property
    @abc.abstractmethod
    def all_possible_subcommand_combinations(self):
        """Every possible sub-command combination for a CLI command call.

        Ie. if we were testing 'geoips list', this property would be every possible
        combination of strings used to call 'geoips list'. This would take the form of:
            - [
                ["geoips", "list", "algorithms", "-p", "data_fusion"],
                ["geoips", "list", "algorithms", "-p", "geoips"],
                ["geoips", "list", "algorithms", "-p", "geoips_clavrx"],
                ...
                ["geoips", "list", <interface_name>, "-p", <pkg_name>],
                ["geoips", "list", <interface_name>],
                ["geoips", "list", <invalid_interface_name>],
                ["geoips", "list", <interface_name>, "-p", <invalid_pkg_name>],
                ...
            ]
        """
        pass

    @abc.abstractmethod
    def check_error(self, args, error):
        """Ensure that the 'geoips list <sub-cmd> ...' error output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI (expected to fail)
        error: str
            - Multiline str representing the error output of the CLI call
        """
        pass

    @abc.abstractmethod
    def check_output(self, args, output):
        """Ensure that the 'geoips list <sub-cmd> ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        pass

    def test_all_command_combinations(self, args=None):
        """Test all 'geoips list <sub-cmd> ...' commands.

        This test covers every valid combination of commands for the
        'geoips list <sub-cmd> ...' command. We also test invalid commands, to ensure
        that the proper help documentation is provided for those using the command
        incorrectly.

        Parameters
        ----------
        args: 2D array of str
            - List of arguments to call the CLI with (ie. ['geoips', 'list <sub-cmd>'])
        """
        if args is None:
            return
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
        assert len(output) or len(error) # assert that some output was created
        prc.terminate()
        if len(error):
            print(error)
            self.check_error(args, error)
        else:
            print(output)
            self.check_output(args, output)