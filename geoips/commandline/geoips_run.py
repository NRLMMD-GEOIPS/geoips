# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "run" command.

Runs the appropriate script based on the args provided.
"""

from colorama import Fore, Style

from geoips.commandline.args import add_args
from geoips.commandline.run_procflow import main
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips.interfaces import procflows
from geoips.utils.context_managers import import_optional_dependencies

data_fusion_installed = False

with import_optional_dependencies(loglevel="info"):
    """Attempt to import data_fusion_args from Data Fusion."""
    # NOTE: loglevel is set to 'info' here so we don't get the constant output of
    # 'Failed to import data_fusion.commandline at /path/to/geoips/geoips/commandline/geoips_run.py:19. If you need it, install it.' # NOQA
    # every time we use the CLI. If a user needs the CLI, I'm assuming they'll know to
    # install it.
    try:
        from data_fusion.commandline.args import add_args as data_fusion_add_args
    except ModuleNotFoundError as e:
        try:
            # 'data_fusion' is not an allowed name for the data_fusion package on pypi. 
            # We have temporarily pushed it to pypi as geoips_data_fusion.
            # This change allows geoips run to use the pypi packaged 
            # version of the data_fusion file, which is named
            # 'geoips_data_fusion'
            from geoips_data_fusion.commandline.args import (
                add_args as data_fusion_add_args,
            )
        except ModuleNotFoundError:
            raise e
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


class GeoipsRunOrderBased(GeoipsExecutableCommand):
    """Run command for executing an order based process-workflow (procflow).

    Makes use of workflow plugins and additional commandline arguments that single
    source would use.
    """

    name = "order_based"
    command_classes = []
    warning = (
        Fore.RED
        + "\nWARNING: "
        + Fore.YELLOW
        + "`geoips run order_based` is experimental and is subject to "
        + "change. This warning will be removed once this command is "
        + "stable.\n"
        + Style.RESET_ALL
    )

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run order-based' command."""
        self.parser.add_argument(
            "-w",
            "--workflow",
            type=str,
            required=True,
            help="The name of the workflow plugin to execute. REQUIRED.",
        )
        add_args(parser=self.parser, legacy=self.legacy)

    def __call__(self, args):
        """Run the provided GeoIPS command.

        In specific, run a GeoIPS order based process-workflow (procflow) to produce
        some output.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through.
        """
        workflow = args.workflow
        obp = procflows.get_plugin("order_based")
        obp(workflow, args.filenames, args)
        print(self.warning)


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
        GeoipsRunDataFusion,
        GeoipsRunConfigBased,
        GeoipsRunOrderBased,
        GeoipsRunSingleSource,
    ]
