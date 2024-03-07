"""Code to implement GeoIPS Command Line Interface (CLI).

Will implement a plethora of commands, but for the meantime, we'll work on
'geoips list' and 'geoips run'
"""
import logging

from geoips.commandline.log_setup import setup_logging
from geoips.commandline.geoips_command import GeoipsCommand
from geoips.commandline.geoips_get import GeoipsGet
from geoips.commandline.geoips_list import GeoipsList
from geoips.commandline.geoips_run import GeoipsRun
from geoips.commandline.geoips_validate import GeoipsValidate

setup_logging()
LOG = logging.getLogger(__name__)


class GeoipsCLI(GeoipsCommand):
    """Top-Level Class for the GeoIPS Commandline Interface (CLI).

    This class includes a list of Sub-Command Classes, which will implement the core
    functionality of the CLI. This includes [GeoipsGet, GeoipsList, GeoipsRun] as of
    right now.
    """
    subcommand_classes = [GeoipsGet, GeoipsList, GeoipsRun, GeoipsValidate]

    def __init__(self):
        """Initialize the GeoipsCLI and each of it's sub-command classes.

        The CLI contains a single top-level argparse.ArgumentParser() which contains
        subparsers related to each subcommand. This ensures that each command has a
        unique set of arguments stemming from command -> subcommand -> sub-subcommand,
        and so on. For example, the GeoipsList Command Class' arguments are inherited
        by all subcommand class of itself, which carry that trend so on until no more
        subcommand classes remain.
        """
        self._subcommand_name = "cli"
        super().__init__()

        self.GEOIPS_ARGS = self.subcommand_parser.parse_args()

    @property
    def subcommand_name(self):
        return self._subcommand_name

    def execute_command(self):
        """Execute the given command."""
        self.GEOIPS_ARGS.exe_command(self.GEOIPS_ARGS)


def main():
    """Entry point for GeoIPS command line interface (CLI)."""
    geoips_cli = GeoipsCLI()
    geoips_cli.execute_command()


if __name__ == "__main__":
    main()