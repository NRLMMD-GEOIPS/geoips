"""GeoIPS CLI "run" command.

Runs the appropriate script based on the args provided.
"""

from geoips.commandline.args import add_args
from geoips.commandline.run_procflow import main
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from data_fusion.commandline.args import add_args as data_fusion_add_args


class GeoipsRunConfigBased(GeoipsExecutableCommand):
    """Run Sub-Command for executing the config based process-workflow (procflow)."""

    subcommand_name = "config_based"
    subcommand_classes = []

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run config_based' Command."""
        add_args(parser=self.subcommand_parser)

    def __call__(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        if args.procflow is None:
            # If None, set to config_based. We don't want users to have to specify
            # what procflow will be used as it is specified in 'geoips run config_based'
            # However, if a user has implemented legacy 'run_procflow', we want to
            # allow them to manually specify it so their procflow works correctly
            args.procflow = "config_based"
        main(ARGS=args)


class GeoipsRunDataFusion(GeoipsCommand):
    """Run Sub-Command for executing the data fusion process-workflow (procflow)."""

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
        if args.procflow is None:
            # If None, set to data_fusion. We don't want users to have to specify
            # what procflow will be used as it is specified in 'geoips run data_fusion'
            # However, if a user has implemented legacy 'run_procflow', we want to
            # allow them to manually specify it so their procflow works correctly
            args.procflow = "data_fusion"
        main(ARGS=args)


class GeoipsRunSingleSource(GeoipsExecutableCommand):
    """Run Sub-Command for executing the single source process-workflow (procflow)."""

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
        if args.procflow is None:
            # If None, set to single_source. We don't want users to have to specify
            # what procflow will be used as it is specified in
            # 'geoips run single_source'.
            # However, if a user has implemented legacy 'run_procflow', we want to
            # allow them to manually specify it so their procflow works correctly
            args.procflow = "single_source"
        main(ARGS=args)


class GeoipsRun(GeoipsCommand):
    """Run Sub-Command for running process-workflows (procflows)."""

    subcommand_name = "run"
    subcommand_classes = [
        GeoipsRunSingleSource,
        GeoipsRunDataFusion,
        GeoipsRunConfigBased,
    ]
