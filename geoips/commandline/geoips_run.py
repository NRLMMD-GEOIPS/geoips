# # # Distribution Statement A. Approved for public release. Distribution is unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""GeoIPS CLI "run" command.

Runs the appropriate script based on the args provided.
"""

from geoips.commandline.args import add_args
from geoips.commandline.run_procflow import main
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips.utils.context_managers import import_optional_dependencies

data_fusion_installed = False

with import_optional_dependencies(loglevel="interactive"):
    """Attempt to import data_fusion_args from Data Fusion."""
    from data_fusion.commandline.args import add_args as data_fusion_add_args

    data_fusion_installed = True


class GeoipsRunConfigBased(GeoipsExecutableCommand):
    """Run Command for executing the config based process-workflow (procflow)."""

    name = "config_based"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run config_based' Command."""
        add_args(parser=self.parser, legacy=self.legacy)

    def __call__(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        if args.procflow is None and self.legacy:
            err_str = (
                "Deprecated, Legacy 'run_procflow' call was used and --procflow "
                "flag wasn't specified. Please either specify which procflow is "
                "being executed via '--procflow <procflow_name>' or use the "
                "supported procflow call 'geoips run <procflow_name>'"
            )
            self.parser.error(err_str)
        elif args.procflow is None:
            # If None, set to 'config_based'. We don't want users to have to specify
            # what procflow will be used as it is specified in
            # 'geoips run config_based'.
            args.procflow = "config_based"
        main(ARGS=args)


class GeoipsRunDataFusion(GeoipsExecutableCommand):
    """Run Command for executing the data fusion process-workflow (procflow)."""

    name = "data_fusion"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run data_fusion' Command."""
        if data_fusion_installed:
            data_fusion_add_args(parser=self.parser, legacy=self.legacy)

    def __call__(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        if data_fusion_installed:
            if args.procflow is None and self.legacy:
                err_str = (
                    "Deprecated, Legacy 'data_fusion_procflow' call was used and "
                    "--procflow flag wasn't specified. Please either specify which "
                    "procflow is being executed via '--procflow <procflow_name>' or "
                    "use the supported procflow call 'geoips run <procflow_name>'"
                )
                self.parser.error(err_str)
            elif args.procflow is None:
                # If None, set to 'data_fusion'. We don't want users to have to specify
                # what procflow will be used as it is specified in
                # 'geoips run data_fusion'.
                args.procflow = "data_fusion"
            main(ARGS=args)
        else:
            print(
                "Data fusion is not installed. If you want to run this type of "
                "functionality, please clone and install "
                "https://github.com/NRLMMD-GEOIPS/data_fusion.git"
            )


class GeoipsRunSingleSource(GeoipsExecutableCommand):
    """Run Command for executing the single source process-workflow (procflow)."""

    name = "single_source"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run single_source' Command."""
        add_args(parser=self.parser, legacy=self.legacy)

    def __call__(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        if args.procflow is None and self.legacy:
            err_str = (
                "Deprecated, Legacy 'run_procflow' call was used and --procflow "
                "flag wasn't specified. Please either specify which procflow is "
                "being executed via '--procflow <procflow_name>' or use the "
                "supported procflow call 'geoips run <procflow_name>'"
            )
            self.parser.error(err_str)
        elif args.procflow is None:
            # If None, set to 'single_source'. We don't want users to have to specify
            # what procflow will be used as it is specified in
            # 'geoips run single_source'.
            args.procflow = "single_source"
        main(ARGS=args)


class GeoipsRun(GeoipsCommand):
    """Run Command for running process-workflows (procflows)."""

    name = "run"
    command_classes = [
        GeoipsRunSingleSource,
        GeoipsRunDataFusion,
        GeoipsRunConfigBased,
    ]
