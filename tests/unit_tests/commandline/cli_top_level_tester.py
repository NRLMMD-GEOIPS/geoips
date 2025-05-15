# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Semi-Abstract CLI Test Class implementing attributes shared by commands."""

import abc
import contextlib
from importlib import metadata
import io
from numpy import any
import pytest
import subprocess
import sys

from geoips.commandline.cmd_instructions import alias_mapping
from geoips.commandline.commandline_interface import GeoipsCLI
from geoips.commandline.commandline_interface import main as cli_main
from geoips.geoips_utils import is_editable


gcli = GeoipsCLI()


def generate_id(args):
    """Generate an ID from the arguments provided.

    Differs slightly from BaseCliTest:generate_id as this function might encounter
    arguments that are a dictionary. This happens due to how those tests are structured,
    where two sets of args are provided for one test (cli_args, expected), where
    expected is a dictionary and should not be part of the test ID.

    Parameters
    ----------
    args: list[str]
        - A list of strings representing the CLI command being ran.
    """
    if isinstance(args, dict):
        return ""
    return " ".join(args)


def check_valid_command_using_monkeypatch(monkeypatch, cli_args, expected):
    """Assert that the command provided works as expected.

    This method is used in multiple unit test calls that don't make use of BaseCliTest.
    Essentially, we mock a sys.argv call via monkeypatch and assert that the output
    of the command casted as vars(args) matches a dictionary of expected arguments that
    the test provides.

    Parameters
    ----------
    monkeypatch: Generator[Monkeypatch]
        - A pytest fixture used to create isolated and controlled test environments by
          modifying code at runtime.
    cli_args: list[str]
        - A list of strings representing the CLI command being ran.
    expected: dict
        - A dictionary of expected argument values that are returned from the command
          being ran from args.
    """
    monkeypatch.setattr("sys.argv", cli_args)
    args = cli_main(suppress_args=False)
    arg_dict = vars(args)
    arg_dict.pop("command_parser")
    arg_dict.pop("exe_command")
    # Assert that the argument dictionary returned from the CLI matches what we expect
    assert arg_dict == expected


class BaseCliTest(abc.ABC):
    """Top-Level CLI Test Class which implements shared attributes for commands."""

    alias_mapping = alias_mapping

    def generate_id(self, args):
        """Generate an ID for the test-arguments provided."""
        return " ".join(args)

    @property
    def plugin_package_names(self):
        """List of names of every installed GeoIPS package."""
        if not hasattr(self, "_plugin_package_names"):
            self._plugin_package_names = [
                ep.value for ep in metadata.entry_points(group="geoips.plugin_packages")
            ]
        return self._plugin_package_names

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

    def retrieve_selected_columns(self, args):
        """If --columns was used for a command, retrieve the list of columns.

        Only used for commands that invoke --columns as a valid optional argument.
        Currently, only a '--columns' option exists for list commands, and this function
        will retrieve the selected list of columns so we can assert that they, and
        nothing else, are listed correctly in the output of the list command.

        We expect to add the --columns argument to the 'get' command in the future.

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
                assert header in output or "has no" in output or "No plugins" in output

    def assert_non_editable_error_or_wrong_package(self, args, error):
        """If we found a package in non-editable mode, assert that an error exists.

        This is used for commands which require packages to be installed in editable
        mode to work (list scripts, test scripts, list unit-tests, test-linting). Since
        we'll check for the same errors in all of these tests, we've refactored it to
        be in one location.

        Parameters
        ----------
        args: list of str
            - The arguments provided to the CLI
        error: str
            - The error output of the CLI call

        Returns
        -------
        editable: bool
            - The truth value of whether or not all packages were editable.
        """
        # Test if a package was specified and is installed in non-editable mode
        pkg_idx = -1
        pkg_name = None
        # Default to last item of args. If no argument is provided after -p, an
        # error will be raised later anyways.
        for idx, arg in enumerate(args):
            if arg == "-p" and len(args) > idx + 1:
                # That means a package was provided. It might not be valid, but we
                # don't care. We'll test this in the if statements below.
                pkg_idx = idx + 1
                pkg_name = args[pkg_idx]
                break

        if pkg_name is not None and pkg_name not in self.plugin_package_names:
            # If the package provided is not a valid package, check for that error
            # instead
            assert f"{args[2]}: error: argument --package_name/-p: invalid" in error
            return False

        if pkg_name:
            # Just test if this package is in editable mode
            editable = is_editable(pkg_name)
        else:
            # Otherwise, assume we're working on all installed packages
            editable = any(
                [is_editable(pkg_name) for pkg_name in self.plugin_package_names]
            )

        if not editable:
            if "-p" in args and "--integration" in args and "geoips" not in args[1:]:
                # This is a specific case for the integration test scripts that
                # only work for geoips. Make sure an error is raised that says
                # we cannot run integration tests in packages other than 'geoips'
                integration_error = (
                    "script: error: Only package 'geoips' has integration tests"
                )
                package_name_error = (
                    "error: argument --package_name/-p: invalid choice:"
                )
                assert integration_error in error or package_name_error in error
            else:
                # If the package provided is a valid installed package, assert that
                # an non-editable error was raised
                assert "is installed in non-editable mode" in error
        return editable

    @property
    @abc.abstractmethod
    def command_combinations(self):
        """A 2d List of command combinations for a CLI command call.

        This can cover every possible combination to call a command or it can be a
        subset of commands if they take a while to run.

        For a shorter command such as 'geoips list interface', this property would be
        every possible combination of strings used to call 'geoips list interface'.
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

        For a longer command such as 'geoips test script', we grab a stochastic subset
        of the possible commands and use those to test instead.
        """
        pass

    @abc.abstractmethod
    def check_error(self, args, error):
        """Ensure that the 'geoips <cmd> ...' error output is correct.

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
        """Ensure that the 'geoips <cmd> ...' successful output is correct.

        Parameters
        ----------
        args: 2D list of str
            - The arguments used to call the CLI
        output: str
            - Multiline str representing the output of the CLI call
        """
        pass

    def capture_output(self, func, args):
        """Redirect stdout and stderr output from a python function to two variables.

        Where these two variables (stdout, stderr), will be used for testing the output
        of CLI commands to make sure they're working as expected.

        Parameters
        ----------
        func: python function
            - The function whose output we want to capture.
        args: array of str
            - List of arguments to call the CLI with (ie. ['geoips', '<cmd>'])

        Returns
        -------
        stdout: str
            - The ouput that would have been printed to sys.stdout.
        stderr: str
            - The output that would have been printed to sys.stderr.
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with (
            contextlib.redirect_stdout(stdout_capture),
            contextlib.redirect_stderr(stderr_capture),
        ):
            try:
                func()
            except SystemExit as se:
                print(se, file=sys.stderr)
            except Exception as e:
                print(e, file=sys.stderr)
            # except RuntimeError as re:
            #     print(re, file=sys.stderr)

        # Retrieve the output printed from 'func'
        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()

        # Close the StringIO Objects
        stdout_capture.close()
        stderr_capture.close()

        return stdout, stderr

    def viable_monkeypatch(self, args):
        """Determine whether or not the arguments are viable to run via monkeypatch.

        We are currently unable to catch certain commands outputs using
        contextlib.redirect_stdout / contextlib.redirect_stderr. The cause of this is
        still unknown, however we have a workaround using subprocess for the time being.

        If the arguments can be ran via monkeypatch, return True, otherwise return
        False.

        Parameters
        ----------
        args: array of str
            - List of arguments to call the CLI with (ie. ['geoips', '<cmd>'])

        Returns
        -------
        monkeypatch_viable: bool
            - Whether or not the arguments can be ran with monkeypatch. Monkeypatch is a
              much quicker option if available.
        """
        match args:
            case _ if "-h" in args:
                # Can't capture help messages using monkeypatch... yet
                return False
            case _ if "linting" in args:
                # Can't capture linting output using monkeypatch... yet
                return False
            case _ if "test" in args and "script" in args:
                # Can't capture bash script output using monkeypatch... yet
                return False
            case _ if (
                "run" in args
                or "run_procflow" in args
                or "data_fusion_procflow" in args
            ):
                # Can't capture procflow output using monkeypatch... yet
                return False
            case _ if any(["non_existent" in arg for arg in args]):
                # Can't capture argparse.ArgumentError output using monkeypatch... yet
                return False
            case _ if "--long" in args and "--columns" in args:
                # Can't capture argparse.ArgumentError output using monkeypatch... yet
                return False
            case _ if "--max-depth" in args and "-1" in args:
                # Can't capture argparse.ArgumentError output using monkeypatch... yet
                return False
            case _:
                # Monkeypatch works for the provided arguments!
                return True

    def test_command_combinations(self, monkeypatch, args=None):
        """Test all or a stochastic subset of 'geoips <cmd> ...' command combinations.

        This test covers a stochastic or complete list of command combinations for all
        'geoips' commands. We also test invalid commands, to ensure that the proper help
        documentation is provided for those using the command incorrectly.

        Parameters
        ----------
        args: array of str
            - List of arguments to call the CLI with (ie. ['geoips', '<cmd>'])
        """
        if args is None:
            return
        monkeypatch_viable = self.viable_monkeypatch(args)
        if monkeypatch_viable:
            # The arguments provided were valid for monkeypatch so we will be using it
            # to execute this test
            orig_argv = sys.argv
            monkeypatch.setattr(sys, "argv", [sys.argv[0]] + args[1:])
            # Capture the output of 'execute_command'
            output, error = self.capture_output(gcli.execute_command, args)
            # Reset sys.argv to what it was originally
            sys.argv = orig_argv
        else:
            # Arguments provided were not valid for monkeypatch and we will be capturing
            # output via subprocess piping
            # Call the CLI via the provided commands with subprocess.Popen
            prc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Capture the output using subprocess.PIPE, then decode it.
            output, error = prc.communicate()
            output, error = output.decode(), error.decode()
            prc.terminate()
        assert len(output) or len(error)  # assert that some output was created
        if len(error) and (not len(output) or output == "\n"):
            self.check_error(args, error)
        else:
            print(output)
            self.check_output(args, output)
