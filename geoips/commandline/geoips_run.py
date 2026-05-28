# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "run" command.

Runs the appropriate script based on the args provided.
"""

from ast import literal_eval
from collections.abc import Mapping
import json
from os import environ
from os.path import abspath
from pathlib import Path
from typing import List, Union

from colorama import Fore, Style

import geoips.utils.yaml_utils as yaml
from geoips.commandline.args import add_args
from geoips.commandline.run_procflow import main
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips.filenames.base_paths import PATHS
from geoips.interfaces import procflows, workflows
from geoips.pydantic_models.v1.workflows import WorkflowPluginModel
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
        environ["ORDER_BASED_CALLED"] = "False"
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
        environ["ORDER_BASED_CALLED"] = "False"
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

    def json_or_yaml_path(self, value: str, no_raise=False) -> Path:
        """Ensure the value provided is a valid pathlib.Path json or yaml file.

        Parameters
        ----------
        value: str
            - The input value for the filepath to typecheck against.
        no_raise: bool, optional
            - Whether or not to raise errors if the input value does not match the
              accepted format. Defaults to False. When True, return False or Path if
              the input value matches the expected format.

        Returns
        -------
        path: Path
            - A json or yaml pathlib.Path object.
        """
        path = Path(value)

        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            if no_raise:
                return False
            raise self.parser.error(
                f"File must have extension .json, .yaml, or .yml, not {path.suffix}"
            )

        if not path.exists():
            if no_raise:
                return False
            raise self.parser.error(f"Input filepath not found: {value}")

        return path

    def workflow_type(self, value: Union[str, List[Path], dict]):
        """Cast input value to a workflow type.

        If value cannot be cast to an accepted workflow type, argparse will raise an
        error denoting that your argument value could not be associated with an
        accepted type.

        Parameters
        ----------
        value: Union[str, List[Path], dict]
            - The input value of a potential workflow.

        Returns
        -------
        workflow: WorkflowPlugin-like
            - The same input value as long as it could be cast to any of the accepted
              workflow types. Workflow has been automatically expanded in the case that
              we need to apply overrides to it. Doesn't change the functionality of the
              OBP if overrides don't occur.
        """
        # unregistered generated workflow
        try:
            workflow = literal_eval(value)
        except (ValueError, SyntaxError):
            # Ignore these errors, could still be valid input
            workflow = None

        if isinstance(workflow, Mapping):
            # Validate the generated workflow with is_registered set to false as this
            # plugin has been dynamically generated
            workflow = WorkflowPluginModel(
                **workflow,
                is_registered=False,
                # Adding context in pydantic is akin to passing in values that are
                # usually None to an Objects __init__ function. It will construct
                # differently if those parameters are provided. In this case, we are
                # telling pydantic to expand the workflow, rather than validate just
                # what's in the data provided
                context={"expand": True},
            ).model_dump()
        # unregistered workflow @ filepath
        elif self.json_or_yaml_path(value, no_raise=True):
            # since the filepath was valid and exists, load the data and validate it
            filepath = self.json_or_yaml_path(value)
            if filepath.suffix.lower() == ".json":
                loader = json.load
            else:
                loader = yaml.safe_load

            with open(filepath, "r") as f:
                workflow = loader(f)
            # This assumes if you pass the filepath option that the plugin itself is not
            # registered. Validate that it's formatted correctly.
            workflow = WorkflowPluginModel(
                **workflow,
                is_registered=False,
                # Adding context in pydantic is akin to passing in values that are
                # usually None to an Objects __init__ function. It will construct
                # differently if those parameters are provided. In this case, we are
                # telling pydantic to expand the workflow, rather than validate just
                # what's in the data provided
                context={"expand": True},
            ).model_dump()
        # registered named workflow
        elif isinstance(value, str):
            workflow = workflows.get_plugin(value, _expand=True)
        else:
            self.parser.error(
                "Error: positional argument 'workflow' could not be associated with an"
                f" accepted type. Input = {value} ; accepted types = "
                "[str, List[Path], dict]"
            )

        return workflow

    def dict_type(self, value):
        """Ensure an dictionary-based override can be cast as a dictionary.

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
            lhs, rhs = value.split("=", 1)
        except ValueError:
            raise self.parser.error(
                f"Invalid format '{value}'. Expected '<global_variable_name>=<value>'"
            )

        return {
            "argument": lhs,
            # doing a yaml.safe_load attempts to cast the value into its correct type
            "value": yaml.safe_load(rhs),
        }

    def kind_override_type(self, value: str):
        """Ensure an override string fits the following format.

        Expected Format
        ---------------
        '<kind>:<argument_name>=<some_value>'

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
            lhs, rhs = value.split("=", 1)
        except ValueError:
            raise self.parser.error(
                f"Invalid format '{value}'. Expected '<kind>:<argument_name>=<value>'"
            )

        parts = lhs.split(":")

        if len(parts) != 2:
            raise self.parser.error(
                f"Invalid key '{lhs}'. Must be in the format of "
                "'<kind>:<argument_name>'"
            )

        kind = parts[0]
        argument = parts[1]

        return {
            "kind": kind,
            "argument": argument,
            # doing a yaml.safe_load attempts to cast the value into its correct type
            "value": yaml.safe_load(rhs),
        }

    def step_override_type(self, value: str):
        """Ensure an override string fits the following format.

        Expected Format
        ---------------
        '<step_id>:<string1>:<optional_string2>:<optional_string3>:...=<some_value>'

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
            lhs, rhs = value.split("=", 1)
        except ValueError:
            raise self.parser.error(
                f"Invalid format '{value}'. Expected '<step_id>:<...>=<value>'"
            )

        parts = lhs.split(":")

        if len(parts) < 2:
            raise self.parser.error(
                f"Invalid key '{lhs}'. Must have at least '<step_id>.<string>'"
            )

        step_id = parts[0]
        keys = parts[1:-1]
        argument = parts[-1]

        return {
            "step_id": step_id,
            "keys": keys,
            "argument": argument,
            # doing a yaml.safe_load attempts to cast the value into its correct type
            "value": yaml.safe_load(rhs),
        }

    def add_arguments(self):
        """Add arguments to the run-subparser for the 'run order-based' command."""
        # Required arguments
        self.parser.add_argument(
            "workflow",
            type=self.workflow_type,
            help=(
                "The name of the workflow plugin to execute. Cannot be supplied "
                "alongside the --generated or --filepath argument."
            ),
        )
        self.parser.add_argument(
            "filenames",
            nargs="*",
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
            nargs="+",
            help=(
                "One or more step override strings to apply to your workflow. An "
                "override string should take on the following format:\n "
                "'<step_id>:<string1>:<optional_string2>:...<argument>=<some_value>'"
            ),
        )
        self.parser.add_argument(
            "-k",
            "--kind-override-strings",
            default=[],
            type=self.kind_override_type,
            nargs="+",
            help=(
                "One or more kind override strings to apply to your workflow. An "
                "override string should take on the following format:\n "
                "'<kind>:<argument_name>=<some_value>'"
            ),
        )
        self.parser.add_argument(
            "-g",
            "--global-override-strings",
            default=[],
            type=self.global_override_type,
            nargs="+",
            help=(
                "One or more global override strings to apply to your workflow. An "
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
        environ["ORDER_BASED_CALLED"] = "True"
        workflow = args.workflow

        workflow = self._apply_overrides(workflow, args)

        obp = procflows.get_plugin("order_based")
        obp(workflow, args.filenames, args)

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
        environ["ORDER_BASED_CALLED"] = "False"
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
