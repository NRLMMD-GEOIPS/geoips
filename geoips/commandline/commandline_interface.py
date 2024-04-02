"""Code to implement GeoIPS Command Line Interface (CLI).

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips list' and 'geoips run'
"""

import logging
from os.path import basename
import sys

from geoips.commandline.log_setup import setup_logging
from geoips.commandline.geoips_command import GeoipsCommand
from geoips.commandline.geoips_config import GeoipsConfig
from geoips.commandline.geoips_get import GeoipsGet
from geoips.commandline.geoips_list import GeoipsList
from geoips.commandline.geoips_run import GeoipsRun
from geoips.commandline.geoips_test import GeoipsTest
from geoips.commandline.geoips_validate import GeoipsValidate

setup_logging()
LOG = logging.getLogger(__name__)


class GeoipsCLI(GeoipsCommand):
    """Top-Level Class for the GeoIPS Commandline Interface (CLI).

    This class includes a list of Sub-Command Classes, which will implement the core
    functionality of the CLI. This includes the following as of right now:
    - [GeoipsConfig, GeoipsGet, GeoipsList, GeoipsRun, GeoipsTest, GeoipsValidate]
    """

    subcommand_classes = [
        GeoipsConfig,
        GeoipsGet,
        GeoipsList,
        GeoipsRun,
        GeoipsTest,
        GeoipsValidate,
    ]

    def __init__(self):
        """Initialize the GeoipsCLI and each of it's sub-command classes.

        The CLI contains a single top-level argparse.ArgumentParser() which contains
        subparsers related to each subcommand. This ensures that each command has a
        unique set of arguments inheirted from command -> subcommand -> sub-subcommand,
        and so on. For example, the GeoipsList Command Class's arguments are inherited
        by all subcommand child classes, which recursively can have their own child
        subcommand classes.
        """
        self._subcommand_name = "cli"  # Needed since we inherit from GeoipsCommand
        super().__init__()

        self.GEOIPS_ARGS = self.subcommand_parser.parse_args()

    @property
    def subcommand_name(self):
        """The Name of the Subcommand."""
        return self._subcommand_name

    def execute_command(self):
        """Execute the given command."""
        self.GEOIPS_ARGS.exe_command(self.GEOIPS_ARGS)


def support_legacy_procflows():
    """Run a series of checks on sys.argv to support legacy calls to run_procflow.

    The new GeoIPS CLI has changed how we run our process workflows from now on. Instead
    of calling 'run_procflow' or 'data_fusion_procflow', we now call
    'geoips run single_source' or 'geoips run data_fusion'. This function parses through
    sys.argv and performs the necessary translations to match our current format so that
    the CLI's argparser can call the appropriate functionality.
    """
    defined_procflow = None
    if "run_procflow" == basename(sys.argv[0]):
        entrypoint = "run_procflow"
        defined_procflow = "single_source"

        if "--procflow" in sys.argv:
            # If '--procflow' was found in the command line arguments, loop through the
            # arguments and grab the correct procflow.

            # NOTE: If --procflow is not defined in the arguments and you are trying to
            # run a 'config_based' procflow, this will not work correctly. Since we have
            # no method of determining what procflow was specfied to run via
            # 'run_procflow' without the '--procflow' flag.

            # Please either specify '--procflow config_based' if using 'run_procflow' or
            # just use the newly created 'geoips run config_based' to ensure your
            # procflow works correctly.
            for idx, arg in enumerate(sys.argv):
                if arg == "--procflow" and len(sys.argv) > idx + 1:
                    defined_procflow = sys.argv[idx + 1]
    elif "data_fusion_procflow" == basename(sys.argv[0]):
        entrypoint = "data_fusion_procflow"
        defined_procflow = "data_fusion"

    if defined_procflow:
        # Either 'run_procflow' or 'data_fusion_procflow' was called, make the
        # appropriate translations in sys.argv so the CLI's parser can call the correct
        # functionality
        sys.argv[0] = sys.argv[0].replace(entrypoint, "geoips")
        sys.argv.insert(1, "run")
        sys.argv.insert(2, defined_procflow)


def main():
    """Entry point for GeoIPS command line interface (CLI)."""
    support_legacy_procflows()
    geoips_cli = GeoipsCLI()
    geoips_cli.execute_command()


if __name__ == "__main__":
    main()
