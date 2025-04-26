# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow plugin models.

Defines pydantic models related to Workflow plugins,
including top-level callable interfaces (eg. Readers, OutputFormatters, etc.).
"""

# Python Standard Libraries
import logging
from typing import Any, Dict, List

# Third-Party Libraries
from pydantic import ConfigDict, Field, field_validator, model_validator

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic.bases import PluginModel, FrozenModel, PermissiveFrozenModel

LOG = logging.getLogger(__name__)


def get_plugin_names(plugin_kind: str) -> List[str]:
    """Return valid plugin names for passed plugin kind.

    Parameters
    ----------
    plugin_kind : str
        valid plugin interface name

    Returns
    -------
    list
        A list of plugin names for a valid plugin kind

    Raises
    ------
    AttributeError
        If the plugin kind is invalid

    """
    interface_name = plugin_kind

    if not interface_name[:-1] == "s":
        interface_name = plugin_kind + "s"

    try:
        interface = getattr(interfaces, interface_name)
    except AttributeError as e:
        error_message = f"{plugin_kind} is not a recognized plugin kind."
        LOG.critical(error_message, exc_info=True)
        raise AttributeError(error_message) from e
    return [plugin.name for plugin in interface.get_plugins() or []]


def get_plugin_kinds() -> set[str]:
    """Return plugin kinds from available interfaces.

    Returns
    -------
    set of str
        singular names of distinct plugin kinds
    """
    return {
        # set comprehension
        # the [:-1] slice converts the plugin kind from plural to singular
        # eg. 'Readers' => 'Reader'
        plugin_kinds[:-1]
        for ifs in interfaces.list_available_interfaces().values()
        for plugin_kinds in ifs
    }


class OutputFormatterArgumentsModel(PermissiveFrozenModel):
    """Validate Output Formatter arguments."""

    model_config = ConfigDict(extra="allow")
    pass


class CoverageCheckerArgumentsModel(PermissiveFrozenModel):
    """Validate Coverage Checker arguments."""

    model_config = ConfigDict(extra="allow")
    pass


class FilenameFormatterArgumentsModel(PermissiveFrozenModel):
    """Validate FilenameFormatter arguments."""

    model_config = ConfigDict(extra="allow")
    pass


class AlgorithmArgumentsModel(PermissiveFrozenModel):
    """Validate Algorithm arguments."""

    model_config = ConfigDict(extra="allow")
    pass


class InterpolatorArgumentsModel(PermissiveFrozenModel):
    """Validate Interpolator arguments."""

    model_config = ConfigDict(extra="allow")
    pass


class ReaderArgumentsModel(PermissiveFrozenModel):
    """Reader step argument definition.

    Pydantic model defining and validating Reader step arguments.
    """

    area_def: str = Field(None, description="Area definition identifier.")
    variables: List[str] = Field(
        None,
        description="List of channels to process",
        alias="chans",
    )
    metadata_only: bool = Field(False, description="Read metadata only.")
    self_register: List[str] = Field(None, description="Enable self-registration.")
    fnames: List[str] = Field(
        None, description="full path to the file(s) for static dataset inputs."
    )

    @model_validator(mode="before")
    def _handle_deprecated_chans(cls, values):
        """
        Check for the deprecated 'chans' field and issue a warning.

        This method detects if `chans` is present in the input values and issues a
        deprecation warning, recommending the use of 'variable' instead.

        Parameters
        ----------
        values : dict
            Input values to the model.

        Returns
        -------
        dict
            The original input values.
        """
        if "chans" in values:
            LOG.warning(
                "'chans' is deprecated and will be removed in GeoIPS 2.0. Use"
                "'variables' instead."
            )
        return values


class WorkflowArgumentsModel(PermissiveFrozenModel):
    """Validate workflow arguments."""

    pass


class WorkflowStepDefinitionModel(FrozenModel):
    """Validate step definition : name, arguments."""

    kind: str = Field(..., description="plugin kind")
    name: str = Field(..., description="plugin name", init=False)
    arguments: Dict[str, Any] = Field(default_factory=dict, description="step args")

    @field_validator("kind", mode="before")
    def _validate_kind(cls, value: str) -> str:
        """
        Validate user input for the 'kind' field.

        Parameters
        ----------
        cls : Type
            WorkflowStepDefinitionModel class.
        value : str
            Value of the 'kind' attribute to validate.

        Returns
        -------
        str
            Validated value of 'kind' if it is valid.

        Raises
        ------
        ValueError
            If the user-provided value for 'kind' is not in the valid_kind list.
        """
        if not value:
            raise ValueError("Invalid input: 'kind' cannot be empty.")

        valid_kinds = get_plugin_kinds()

        # raise error if the plugin kind is not valid
        if value not in valid_kinds:
            raise ValueError(
                f"[!] Invalid plugin kind: '{value}'. Must be one of {valid_kinds}\n\n"
            )

        return value

    @model_validator(mode="after")
    def _validate_plugin_name(
        cls, model: "WorkflowStepDefinitionModel"
    ) -> "WorkflowStepDefinitionModel":
        """
        Validate that the plugin name is valid for the specified plugin kind.

        Parameters
        ----------
        cls : Type
            WorkflowStepDefinitionModel class.
        values : dict
            Dictionary of input values.

        Returns
        -------
        dict
            Input values post plugin name validation.

        Raises
        ------
        ValueError
            If the plugin name is not valid for the specified plugin kind.

        """
        plugin_name = model.name
        plugin_kind = model.kind

        valid_plugin_names = get_plugin_names(plugin_kind)
        if plugin_name not in valid_plugin_names:
            raise ValueError(
                f"[!] Invalid plugin name '{plugin_name}'. \n\t"
                f"Must be one of {sorted(valid_plugin_names)}"
            )

        return model

    @model_validator(mode="after")
    def _validate_plugin_arguments(
        cls, model: "WorkflowStepDefinitionModel"
    ) -> "WorkflowStepDefinitionModel":
        """
        Validate and organize details for each step.

        Parameters
        ----------
        values : dict
            A dictionary of plugin data. The key is plugin kind, and
            the value consists of plugin name and arguments

        Returns
        -------
        values : dict
            A validated and structured dictionary with the following fields:

            - `kind` : str
                The kind of the plugin.
            - `name` : str
                The name of the plugin.
            - `arguments` : dict
                The arguments associated with the plugin.

        """
        # Delegate arguments validation to each plugin kind argument class
        plugin_kind = model.kind
        plugin_kind_pascal_case = "".join(
            [word.capitalize() for word in plugin_kind.split("_")]
        )
        plugin_arguments_model_name = f"{plugin_kind_pascal_case}ArgumentsModel"
        # Dictionary listing all plugin arguments models
        plugin_arguments_models = {
            "AlgorithmArgumentsModel": AlgorithmArgumentsModel,
            "CoverageCheckerArgumentsModel": CoverageCheckerArgumentsModel,
            "FilenameFormatterArgumentsModel": FilenameFormatterArgumentsModel,
            "InterpolatorArgumentsModel": InterpolatorArgumentsModel,
            "OutputFormatterArgumentsModel": OutputFormatterArgumentsModel,
            "ReaderArgumentsModel": ReaderArgumentsModel,
            "WorkflowArgumentsModel": WorkflowArgumentsModel,
        }
        plugin_arguments_model = plugin_arguments_models.get(
            plugin_arguments_model_name
        )
        if plugin_arguments_model is None:
            raise ValueError(
                f'The argument class/model "{plugin_arguments_model_name}" for'
                f'the plugin kind "{plugin_kind}" is not defined.'
            )

        plugin_arguments_model(**model.arguments)

        return model


class WorkflowSpecModel(FrozenModel):
    """The specification for a workflow."""

    # list of steps
    steps: Dict[str, WorkflowStepDefinitionModel] = Field(
        ..., description="Steps to produce the workflow."
    )


class WorkflowPluginModel(PluginModel):
    """A plugin that produces a workflow."""

    model_config = ConfigDict(extra="allow")
    spec: WorkflowSpecModel = Field(..., description="The workflow specification")
