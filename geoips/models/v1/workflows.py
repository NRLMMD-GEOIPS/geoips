# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow plugin models.

Defines pydantic models related to Workflow plugins,
including top-level callable interfaces (eg. Readers, OutputFormatters, etc.).
"""

from __future__ import annotations

# Python Standard Libraries
import logging
from typing import Any, Dict, List

# Third-Party Libraries
from pydantic import ConfigDict, Field, field_validator, model_validator

# GeoIPS imports
from geoips import interfaces
from geoips.models.v1.bases import (
    PythonIdentifier,
    PluginModel,
    FrozenModel,
    PermissiveFrozenModel,
)
from geoips.utils.types.partial_lexeme import Lexeme

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
    interface_name = str(Lexeme(plugin_kind).plural)
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
        str(Lexeme(plugin_kinds).singular)
        for ifs in interfaces.list_available_interfaces().values()
        for plugin_kinds in ifs

    }


class OutputFormatterArgumentsModel(PermissiveFrozenModel):
    """Validate Output Formatter arguments."""

    pass


class CoverageCheckerArgumentsModel(PermissiveFrozenModel):
    """Validate Coverage Checker arguments."""

    pass


class FilenameFormatterArgumentsModel(PermissiveFrozenModel):
    """Validate FilenameFormatter arguments."""

    pass


class AlgorithmArgumentsModel(PermissiveFrozenModel):
    """Validate Algorithm arguments."""

    pass


class InterpolatorArgumentsModel(PermissiveFrozenModel):
    """Validate Interpolator arguments."""

    pass


class WorkflowArgumentsModel(PermissiveFrozenModel):
    """Validate Workflow arguments."""

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


class WorkflowStepDefinitionModel(FrozenModel):
    """Validate step definition : kind, name, and arguments."""

    kind: Lexeme = Field(..., description="plugin kind")
    name: str = Field(..., description="plugin name", init=False)
    arguments: Dict[str, Any] = Field(default_factory=dict, description="step args")

    @field_validator("kind", mode="before")
    def _validate_plugin_kind(cls, value: str) -> str:
        """
        Validate that 'kind' is a known plugin kind.

        Parameters
        ----------
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
        # We did not switch to kind: Annotated[str, Field(pattern=kind_pattern)] due to
        # lack of user-friendly error reporting options in case of validation failure.

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
        cls, model: WorkflowStepDefinitionModel
    ) -> WorkflowStepDefinitionModel:
        """
        Validate that a plugin with this name exists for the specified plugin kind.

        Parameters
        ----------
        model: WorkflowStepDefinitionModel
            The WorkflowStepDefinitionModel instance to validate.

        Returns
        -------
        WorkflowStepDefinitionModel
            The validated instance of WorkflowStepDefinitionModel

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
                f"Invalid plugin name '{plugin_name}'."
                f"Must be one of {sorted(valid_plugin_names)}"
            )

        return model

    @model_validator(mode="after")
    def _validate_plugin_arguments(
        cls, model: WorkflowStepDefinitionModel
    ) -> WorkflowStepDefinitionModel:
        """
        Validate and organize details for each step.

        This validator is called after the model is initialized. It ensures that the
        `kind`, `name`, and `arguments` attributes are properly validated and
        structured for each workflow step.

        Parameters
        ----------
        model: WorkflowStepDefinitionModel
            The WorkflowStepDefinitionModel instance to validate.

        Returns
        -------
        WorkflowStepDefinitionModel
            The validated instance of WorkflowStepDefinitionModel
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
            "CoverageCheckerArgumentsModel": CoverageCheckerArgumentsModel,
            "ReaderArgumentsModel": ReaderArgumentsModel,
            "WorkflowArgumentsModel": WorkflowArgumentsModel,
        }

        try:
            plugin_arguments_model = plugin_arguments_models[
                plugin_arguments_model_name
            ]
        except KeyError as e:
            valid_models = ", ".join(plugin_arguments_models)
            raise ValueError(
                f'The argument class/model "{plugin_arguments_model_name}" for'
                f'the plugin kind "{plugin_kind}" is not defined. Valid available'
                f"models are {valid_models}."
            ) from e
            LOG.interactive(
                "Plugin kind '%s' was already validated, yet PluginArgumentsModel "
                "lookup failed. Please report this to the GeoIPS development team",
                plugin_kind,
            )

        plugin_arguments_model(**model.arguments)

        return model


class WorkflowSpecModel(FrozenModel):
    """The specification for a workflow."""

    # list of steps
    steps: Dict[PythonIdentifier, WorkflowStepDefinitionModel] = Field(
        ..., description="Steps to produce the workflow."
    )


class WorkflowPluginModel(PluginModel):
    """A plugin that produces a workflow."""

    model_config = ConfigDict(extra="allow")
    spec: WorkflowSpecModel = Field(..., description="The workflow specification")
