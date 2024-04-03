"""Semi-Abstract CLI Test Class implementing attributes shared by sub-commands."""

import abc
import pytest
import subprocess

from geoips.geoips_utils import get_entry_point_group


class BaseCliTest(abc.ABC):
    """Top-Level CLI Test Class which implements shared attributes for sub-commands."""

    _config_install_args = ["geoips", "config", "install"]
    _get_family_args = ["geoips", "get", "family"]
    _get_interface_args = ["geoips", "get", "interface"]
    _get_package_args = ["geoips", "get", "package"]
    _get_plugin_args = ["geoips", "get", "plugin"]
    _list_interface_args = ["geoips", "list", "interface"]
    _list_interfaces_args = ["geoips", "list", "interfaces"]
    _list_plugins_args = ["geoips", "list", "plugins"]
    _list_packages_args = ["geoips", "list", "packages"]
    _list_scripts_args = ["geoips", "list", "scripts"]
    _list_test_datasets_args = ["geoips", "list", "test-datasets"]
    _list_unit_tests_args = ["geoips", "list", "unit-tests"]
    _run_args = ["geoips", "run"]
    _test_linting_args = ["geoips", "test", "linting"]
    _test_script_args = ["geoips", "test", "script"]
    _test_unit_test_args = ["geoips", "test", "unit-test"]
    _validate_args = ["geoips", "validate"]
    arg_list = [
        _config_install_args,
        _get_family_args,
        _get_interface_args,
        _get_package_args,
        _get_plugin_args,
        _list_interface_args,
        _list_interfaces_args,
        _list_plugins_args,
        _list_packages_args,
        _list_scripts_args,
        _list_test_datasets_args,
        _list_unit_tests_args,
        _run_args,
        _test_linting_args,
        _test_script_args,
        _test_unit_test_args,
        _validate_args,
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
    def test_datasets(self):
        """List of every available GeoIPS test dataset name."""
        if not hasattr(self, "_test_datasets"):
            self._test_datasets = [
                "test_data_amsr2",
                "test_data_clavrx",
                "test_data_fusion",
                "test_data_gpm",
                "test_data_noaa_aws",
                "test_data_sar",
                "test_data_scat",
                "test_data_smap",
                "test_data_viirs",
            ]
        return self._test_datasets

    def retrieve_selected_columns_from_list_command(self, args):
        """If --columns was used for a 'list' command, retrieve the list of columns.

        Only used for commands that invoke 'list'. We've added a '--columns' option
        for list commands, and this function will retrieve the selected list of
        columns so we can assert that they, and nothing else, are listed correctly
        in the output of the list command.

        Parameters
        ----------
        args: list of strings
            - Essentially <command_sent_to_cli>.split(" ")
            - ie. "geoips list interface algorithms --columns package interface relpath"
              would become:
              ["geoips", "list", "interface", "algorithms",
              "--columns", "package", "interface", "relpath"]
        """
        selected_cols = None
        if "--columns" in args:
            start_idx = None
            for idx, arg in enumerate(args):
                if arg == "--columns":
                    start_idx = idx + 1
                    break
            if start_idx is None or start_idx >= len(args):
                usage_str = f"{' '.join(args[:3])} -h for more information."
                pytest.fail(
                    f"Unexpected usage of --columns arg. Please run {usage_str}"
                )
            selected_cols = args[start_idx:]
        return selected_cols

    def assert_correct_headers_in_output(self, output, headers, selected_cols):
        """Ensure that all selected columns are in the corresponding 'list' output.

        This is only applied to list commands, as they produce tabular output with
        headers. Given output, a list of headers, and selected columns, check that
        each corresponding header to each selected column is in the provided output.

        Parameters
        ----------
        output: multiline str
            - The caputured output of the terminal
        headers: dict of strings
            - The Corresponding Header, column_val dict to parse through
        selected_columns: list of strings or None
            - If None, asser that every Header key is in the output. Otherwise check
              that the corresponding Header key, column_val is in the output
        """
        for header in headers:
            if selected_cols is None or headers[header] in selected_cols:
                assert header in output

    @property
    @abc.abstractmethod
    def all_possible_subcommand_combinations(self):
        """Every possible sub-command combination for a CLI command call.

        Ie. if we were testing 'geoips list interface', this property would be every
        possible combination of strings used to call 'geoips list interface'.
        This would take the form of:

        - [
            - ["geoips", "list", "interface", "algorithms", "-p", "data_fusion"],
            - ["geoips", "list", "interface", "algorithms", "-p", "geoips"],
            - ["geoips", "list", "interface", "algorithms", "-p", "geoips_clavrx"],
            - ...
            - ["geoips", "list", "interface", <interface_name>, "-p", <pkg_name>],
            - ["geoips", "list", "interface", <interface_name>],
            - ["geoips", "list", "interface", <invalid_interface_name>],
            - ["geoips", "list", "interface", <interface_name>, "-p", <bad_pkg_name>],
            - ...
        - ]
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
        assert len(output) or len(error)  # assert that some output was created
        prc.terminate()
        if len(error) and not len(output):
            print(error)
            self.check_error(args, error)
        else:
            print(output)
            self.check_output(args, output)
