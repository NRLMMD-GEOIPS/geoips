"""GeoIPS CLI "run" command.

Runs the appropriate script based on the args provided.
"""

from geoips.commandline.args import add_args
from geoips.commandline.run_procflow import main
from geoips.commandline.geoips_command import GeoipsExecutableCommand


class GeoipsRun(GeoipsExecutableCommand):
    """Run Sub-Command for running process-workflows (procflows)."""

    subcommand_name = "run"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the run-subparser for the Run Command."""
        add_args(parser=self.subcommand_parser)

    def __call__(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        main(ARGS=args)
