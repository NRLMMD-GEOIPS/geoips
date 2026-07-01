# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "run" command.

Runs the appropriate script based on the args provided.
"""

from os.path import abspath

from colorama import Fore, Style

from geoips.commandline.args import add_args
from geoips.commandline.run_procflow import main
from geoips.commandline.geoips_command import (
    GeoipsCommand,
    GeoipsExecutableCommand,
    GeoipsWorkflowCommand,
)
from geoips.filenames.base_paths import PATHS
from geoips.interfaces import procflows, workflows
from geoips.pydantic_models.v1.workflows import WorkflowPluginModel
from geoips.utils.context_managers import import_optional_dependencies
import geoips.utils.yaml_utils as yaml

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


class GeoipsRunOrderBased(GeoipsWorkflowCommand):
    """Run command for executing an order based process-workflow (procflow).

    Makes use of workflow plugins and additional commandline arguments that single
    source would use.
    """

    name = "order_based"
    command_classes = []
    warning_with_color = (
        Fore.RED
        + "\nWARNING: "
        + Fore.YELLOW
        + "`geoips run order_based` is experimental and is subject to "
        + "change. This warning will be removed once this command is "
        + "stable.\n"
        + Style.RESET_ALL
    )
    warning_no_color = (
        "\nWARNING: `geoips run order_based` is experimental and is subject to change. "
        "This warning will be removed once this command is stable.\n"
    )

    def dict_type(self, value):
        """Ensure an dictionary-based override can be cast as a dictionary.

        This is used to validate the input of -S, -K, and -G flags.

        Parameters
        ----------
        value: str
            The full global override string for a geoips run order_based command.
        """
        try:
            return yaml.safe_load(value)
        except Exception as e:
            raise self.parser.error(f"Invalid dictionary input: {value}") from e

    def global_override_type(self, value: str):
        """Ensure an override string fits the following format.

        Expected Format
        ---------------
        '<global_variable_name>=<some_value>'

        Parameters
        ----------
        value: str
            The full global override string for a geoips run order_based command.

        Returns
        -------
        override_dict: dict
            The validated contents of an override string in a dictionary.
        """
        try:
            override = workflows.global_override_type(value)
        except Exception:
            raise self.parser.error(
                f"Invalid format '{value}'. Expected '<global_variable_name>=<value>'"
            )
        return override

    def kind_override_type(self, value: str):
        """Ensure an override string fits the following format.

        Expected Format
        ---------------
        '<kind>.<argument_name>=<some_value>'

        Parameters
        ----------
        value: str
            The full kind override string for a geoips run order_based command.

        Returns
        -------
        override_dict: dict
            The validated contents of an override string in a dictionary.
        """
        try:
            override = workflows.kind_override_type(value)
        except Exception:
            raise self.parser.error(
                f"Invalid format '{value}'. Expected '<kind>.<argument_name>=<value>'"
            )
        return override

    def step_override_type(self, value: str):
        """Ensure an override string fits the following format.

        Expected Format
        ---------------
        '<step_id>.<string1>.<optional_string2>.<optional_string3>...=<some_value>'

        Parameters
        ----------
        value: str
            The full step override string for a geoips run order_based command.

        Returns
        -------
        override_dict: dict
            The validated contents of an override string in a dictionary.
        """
        try:
            override = workflows.step_override_type(value)
        except Exception:
            raise self.parser.error(
                f"Invalid format '{value}'. Expected '<step_id>.<...>=<value>'"
            )
        return override

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run order-based' command."""
        # Required arguments
        self.parser.add_argument(
            "workflow",
            type=self.workflow_type,
            help=(
                "Workflow instance. Can be the name of a registered workflow plugin, "
                "a .json or .yaml path to an unregistered workflow plugin, or a "
                "dictionary that will be literally evaluated as a workflow."
            ),
        )
        self.parser.add_argument(
            "filenames",
            nargs="+",
            type=abspath,
            help="""Fully qualified paths to data files to be processed.""",
        )
        # dict-based override arguments
        self.parser.add_argument(
            "-S",
            "--step-override-dict",
            default={},
            type=self.dict_type,
            help=(
                "One or more step overrides to apply to your workflow. In a dictionary "
                "format. See geoips.pydantic_models.v1.workflows for more info on the "
                "correct format."
            ),
        )
        self.parser.add_argument(
            "-K",
            "--kind-override-dict",
            default={},
            type=self.dict_type,
            help=(
                "One or more kind overrides to apply to your workflow. In a dictionary "
                "format. See geoips.pydantic_models.v1.workflows for more info on the "
                "correct format."
            ),
        )
        self.parser.add_argument(
            "-G",
            "--global-override-dict",
            default={},
            type=self.dict_type,
            help=(
                "One or more global overrides to apply to your workflow. In a "
                "dictionary format. See geoips.pydantic_models.v1.workflows for more "
                "info on the correct format."
            ),
        )
        # string-based override arguments
        self.parser.add_argument(
            "-s",
            "--step-override-strings",
            default=[],
            type=self.step_override_type,
            action="append",
            help=(
                "Step override string to apply to your workflow. An "
                "override string should take on the following format:\n "
                "'<step_id>.<string1>.<optional_string2>...<argument>=<some_value>'"
            ),
        )
        self.parser.add_argument(
            "-k",
            "--kind-override-strings",
            default=[],
            type=self.kind_override_type,
            action="append",
            help=(
                "Kind override string to apply to your workflow. An "
                "override string should take on the following format:\n "
                "'<kind>.<argument_name>=<some_value>'"
            ),
        )
        self.parser.add_argument(
            "-g",
            "--global-override-strings",
            default=[],
            type=self.global_override_type,
            action="append",
            help=(
                "Global override string to apply to your workflow. An "
                "override string should take on the following format:\n "
                "'<global_variable_name>=<some_value>'"
            ),
        )

        # Turning off all additional procflow args for this command. We want this
        # command to have a limited set of arguments to start.
        # add_args(parser=self.parser, legacy=self.legacy)

    def _apply_overrides(self, workflow, args):
        """Override a workflow via dictionary and string overrides.

        Parameters
        ----------
        workflow: WorkflowPlugin-like
            - The workflow to override.
        args: Namespace()
            - The input argument namespace.

        Returns
        -------
        workflow: WorkflowPlugin-like
            - The overridden workflow.
        """
        s_override_dict = args.step_override_dict
        k_override_dict = args.kind_override_dict
        g_override_dict = args.global_override_dict

        s_override_strings = args.step_override_strings
        k_override_strings = args.kind_override_strings
        g_override_strings = args.global_override_strings

        # apply dict-based overrides
        if any(
            [
                s_override_dict,
                k_override_dict,
                g_override_dict,
            ]
        ):
            workflow = workflows._override_workflow_dict_format(
                workflow,
                goverrides=g_override_dict,
                koverrides=k_override_dict,
                soverrides=s_override_dict,
            )
            WorkflowPluginModel(**workflow, is_registered=False)

        # apply string-based overrides
        if any(
            [
                s_override_strings,
                k_override_strings,
                g_override_strings,
            ]
        ):
            workflow = workflows._override_workflow_string_format(
                workflow,
                goverrides=g_override_strings,
                koverrides=k_override_strings,
                soverrides=s_override_strings,
            )
            WorkflowPluginModel(**workflow, is_registered=False)

        return workflow

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
        write_tokens = args.write_tokens

        workflow = self._apply_overrides(workflow, args)

        obp = procflows.get_plugin("order_based")
        obp(workflow_spec=workflow, fnames=args.filenames, command_line_args=args)

        if PATHS["NO_COLOR"]:
            print(self.warning_no_color)
        else:
            print(self.warning_with_color)


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
