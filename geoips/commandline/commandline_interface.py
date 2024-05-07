"""Code to implement GeoIPS Command Line Interface (CLI).

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips list' and 'geoips run'
"""

import logging
import sys

from geoips.commandline.ancillary_info import get_cmd_instructions
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

    def __init__(self, instructions_dir=None):
        """Initialize the GeoipsCLI and each of it's sub-command classes.

        The CLI contains a single top-level argparse.ArgumentParser() which contains
        subparsers related to each subcommand. This ensures that each command has a
        unique set of arguments inheirted from command -> subcommand -> sub-subcommand,
        and so on. For example, the GeoipsList Command Class's arguments are inherited
        by all subcommand child classes, which recursively can have their own child
        subcommand classes.
        """
        self._subcommand_name = "cli"  # Needed since we inherit from GeoipsCommand
        if instructions_dir:
            self.cmd_instructions = get_cmd_instructions(instructions_dir)
        else:
            self.cmd_instructions = None
        super().__init__()

        self.GEOIPS_ARGS = self.subcommand_parser.parse_args()

    @property
    def subcommand_name(self):
        """The Name of the Subcommand."""
        return self._subcommand_name

    def execute_command(self):
        """Execute the given command."""
        if hasattr(self.GEOIPS_ARGS, "exe_command"):
            # The command called is executable (child of GeoipsExecutableCommand)
            # so execute that command now.
            self.GEOIPS_ARGS.exe_command(self.GEOIPS_ARGS)
        else:
            try:
                cmd_name = sys.argv[1]
                self.subcommand_parser.error(
                    f"Cannot call 'geoips {cmd_name}' by itself. It's not an executable"
                    f" function. To see how to use it, run 'geoips {cmd_name} -h'."
                )
            except IndexError:
                self.subcommand_parser.error(
                    "Cannot run the aforementioned command as it is not executable. Try"
                    " running it with the '-h' option appended to it to get a usage "
                    "statement."
                )


def main():
    """Entry point for GeoIPS command line interface (CLI)."""
    geoips_cli = GeoipsCLI()
    geoips_cli.execute_command()


if __name__ == "__main__":
    main()
