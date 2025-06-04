# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Code to implement GeoIPS Command Line Interface (CLI).

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips list' and 'geoips run'
"""

from os.path import basename, dirname, join
import sys

from colorama import Fore, Style

from geoips.commandline.cmd_instructions import get_instructions
from geoips.commandline.geoips_command import GeoipsCommand
from geoips.commandline.geoips_config import GeoipsConfig
from geoips.commandline.geoips_describe import GeoipsDescribe
from geoips.commandline.geoips_list import GeoipsList
from geoips.commandline.geoips_run import GeoipsRun
from geoips.commandline.geoips_test import GeoipsTest
from geoips.commandline.geoips_tree import GeoipsTree
from geoips.commandline.geoips_validate import GeoipsValidate
from geoips.commandline.log_setup import setup_logging


class GeoipsCLI(GeoipsCommand):
    """Top-Level Class for the GeoIPS Commandline Interface (CLI).

    This class includes a list of Command Classes, which will implement the core
    functionality of the CLI. This includes the following as of right now:
    - [GeoipsConfig, GeoipsGet, GeoipsList, GeoipsRun, GeoipsTest, GeoipsValidate]
    """

    name = "geoips"  # Needed since we inherit from GeoipsCommand
    command_classes = [
        GeoipsConfig,
        GeoipsDescribe,
        GeoipsList,
        GeoipsRun,
        GeoipsTest,
        GeoipsTree,
        GeoipsValidate,
    ]

    def __init__(self, instructions_dir=None, legacy=False):
        """Initialize the GeoipsCLI and each of it's command classes.

        The CLI contains a single top-level argparse.ArgumentParser() which contains
        subparsers related to each subcommand. This ensures that each command has a
        unique set of arguments inheirted from command -> subcommand -> subcommand,
        and so on. For example, the GeoipsList Command Class's arguments are inherited
        by all subcommand child classes, which recursively can have their own child
        subcommand classes.

        Parameters
        ----------
        instructions_dir: str or Posix.Path
            - The path to the directory which includes the commandline instructions.
              This is only used for testing purposes so we can ensure the correct
              functionality occurs for possibly missing / invalid instruction files.
        """
        if instructions_dir:
            # Instructions dir has been provided, use the instructions found in that
            # directory so we can test that the correct functionality occurs for any
            # given instruction file state.
            self.cmd_instructions = get_instructions(instructions_dir)
        else:
            # Otherwise use the default instructions which we know are correct
            # (and if they're not, the appropriate error will be raised.)
            self.cmd_instructions = None

        # parse_known_args expects arguments in a specific order. So, currrently,
        # 'geoips --log-level info <rest of command>' will work but
        # 'geoips <rest of command> --log-level info' will not. The functionality below
        # rearranges the log level arguments to match the working version. This way,
        # users can add --log-level <log_level_name> anywhere in the command and it will
        # work.
        if set(sys.argv).intersection(set(["--log-level", "-log"])):
            # One of the flags was found in the arguments provided
            log_idx = max(
                [
                    idx if arg in ["--log-level", "-log"] else -1
                    for idx, arg in enumerate(sys.argv)
                ]
            )
            # Make sure that the argument list is long enough for log level to be
            # provided. It doesn't have to be correct, that validation will be done
            # by argparse
            if len(sys.argv) > log_idx + 1:
                flag = sys.argv[log_idx]
                log_level = sys.argv[log_idx + 1]
                # Get the flag and log_level, remove them from the argument list, and
                # insert them in working locations.
                # I.e. geoips --log-level <log_level_name>
                sys.argv.pop(log_idx + 1)
                sys.argv.pop(log_idx)
                sys.argv.insert(1, log_level)
                sys.argv.insert(1, flag)

        super().__init__(legacy=legacy)

    def execute_command(self):
        """Execute the given command."""
        self.GEOIPS_ARGS = self.parser.parse_args()
        if hasattr(self.GEOIPS_ARGS, "exe_command"):
            # The command called is executable (child of GeoipsExecutableCommand)
            # so execute that command now.
            self.GEOIPS_ARGS.exe_command(self.GEOIPS_ARGS)
            return self.GEOIPS_ARGS
        else:
            print(
                # f'"{self.GEOIPS_ARGS.command}" command requires a subcommand.\n\n'
                f"{self.GEOIPS_ARGS.command_parser.format_usage()}"
            )
            sys.exit(2)


def deprecate_create_plugin_registries():
    """Deprecate the 'create_plugin_registries' command if it was supplied.

    If 'create_plugin_registries' was called, convert that command to
    'geoips config create-registries' and print a deprecation warning. These two
    commands are equivalent, however we are transitioning to the sole use of the CLI
    rather than unconnected console scripts.
    """
    if basename(sys.argv[0]) == "create_plugin_registries":
        LOG = setup_logging(logging_level="warning")
        LOG.warning(
            msg=(
                "'create_plugin_registries' is deprecated. Please use 'geoips config "
                "create-registries' from now on. This functionality will be removed in "
                "the future."
            ),
            stacklevel=2,
        )
        sys.argv[0] = join(dirname(sys.argv[0]), "geoips")
        sys.argv.append("config")
        sys.argv.append("create-registries")


def support_legacy_procflows():
    """Run a series of checks on sys.argv to support legacy calls to run_procflow.

    The new GeoIPS CLI has changed how we run our process workflows from now on. Instead
    of calling 'run_procflow' or 'data_fusion_procflow', we now call
    'geoips run single_source' or 'geoips run data_fusion'. This function parses through
    sys.argv and performs the necessary translations to match our current format so that
    the CLI's argparser can call the appropriate functionality.

    Returns
    -------
    legacy: bool
        - The truth value as to whether or not a legacy procflow call was used
    """
    defined_procflow = None
    # Including '-h' here as we need to be able to support help messages for this cmd
    supported_procflows = [
        "config_based",
        "data_fusion",
        "order_based",
        "ob",
        "obp",
        "single_source",
        "-h",
    ]
    if (
        basename(sys.argv[0]) == "geoips"
        and len(sys.argv) > 2
        and sys.argv[1] == "run"
        and (len(sys.argv) < 3 or sys.argv[2] not in supported_procflows)
    ):
        # Either a procflow was not specified or it was an invalid procflow. Notify the
        # user of that with a 'NotImplementedError'.
        if len(sys.argv) >= 3:
            procflow_name = sys.argv[2]
        else:
            procflow_name = "No procflow supplied."
        raise NotImplementedError(
            f"'geoips run' was called alongside procflow: '{procflow_name}'.\nIf you "
            "did not supply a procflow name, this is not supported currently.\n"
            "Eventually, 'geoips run' will call the 'order_based' procflow, however "
            "this is not at the current time of use.\nFor a list of supported "
            f"procflows, choose one of the following: {supported_procflows}."
        )
    elif basename(sys.argv[0]) == "run_procflow":
        entrypoint = "run_procflow"
        defined_procflow = "single_source"

    elif basename(sys.argv[0]) == "data_fusion_procflow":
        entrypoint = "data_fusion_procflow"
        defined_procflow = "data_fusion"

    if defined_procflow:
        # Either 'run_procflow' or 'data_fusion_procflow' was called, make the
        # appropriate translations in sys.argv so the CLI's parser can call the correct
        # functionality
        if "--procflow" in sys.argv:
            # If '--procflow' was found in the command line arguments, loop through the
            # arguments and grab the correct procflow.
            for idx, arg in enumerate(sys.argv):
                if arg == "--procflow" and len(sys.argv) > idx + 1:
                    defined_procflow = sys.argv[idx + 1]
        sys.argv[0] = sys.argv[0].replace(entrypoint, "geoips")
        sys.argv.insert(1, "run")
        sys.argv.insert(2, defined_procflow)
        return True
    return False


def print_beta_warning():
    """Notify the user that the CLI is still in Beta development stage."""
    print(
        Fore.RED
        + "\nWARNING: "
        + Fore.YELLOW
        + "The GeoIPS CLI is currently under development and is subject "
        "to change.\nUntil this warning is removed, do not rely on the CLI to be "
        "static.\nPlease feel free to test the CLI and report any bugs or comments as "
        "an issue here:\n"
        + Fore.BLUE
        + "https://github.com/NRLMMD-GEOIPS/geoips/issues/new/choose\n"
        + Style.RESET_ALL
    )


def main(suppress_args=True):
    """Entry point for GeoIPS command line interface (CLI).

    Parameters
    ----------
    suppress_args: bool, (default=True)
        - Whether or not we want to suppress the arguments returned from the CLI.
          If False, return the argument namespace. Used for unit testing.
    """
    # Support legacy 'run_procflow' calls if applicable
    legacy = support_legacy_procflows()
    # Deprecate 'create_plugin_registries' if called
    deprecate_create_plugin_registries()
    # Initialize the CLI and all of its commands
    geoips_cli = GeoipsCLI(legacy=legacy)
    # Execute the called command
    args = geoips_cli.execute_command()
    # Notify that the user is in Beta development status right now.
    print_beta_warning()
    if not suppress_args:
        return args


if __name__ == "__main__":
    main()
