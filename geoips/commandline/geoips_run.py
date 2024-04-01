"""GeoIPS CLI "run" command.

Runs the appropriate script based on the args provided.
"""

from geoips.commandline.args import add_args
from geoips.commandline.run_procflow import main
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from data_fusion.commandline.args import add_args as data_fusion_add_args


class GeoipsRunDataFusion(GeoipsCommand):
    """Run Sub-Command for running the data fusion process-workflow (procflow)."""

    subcommand_name = "data_fusion"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run data_fusion' Command."""
        data_fusion_add_args(parser=self.subcommand_parser)

    def __call__(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        main(ARGS=args)


class GeoipsRunSingleSource(GeoipsExecutableCommand):
    """Run Sub-Command for running the single source process-workflow (procflow)."""

    subcommand_name = "single_source"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run single_source' Command."""
        add_args(parser=self.subcommand_parser)

    def __call__(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        main(ARGS=args)


class GeoipsRun(GeoipsCommand):
    """Run Sub-Command for running process-workflows (procflows)."""

    subcommand_name = "run"
    subcommand_classes = [GeoipsRunSingleSource, GeoipsRunDataFusion]

