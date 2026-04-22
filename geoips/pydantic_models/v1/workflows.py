# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow plugin models.

Defines pydantic models related to Workflow plugins,
including top-level callable interfaces (eg. Readers, OutputFormatters, etc.).
"""

# Previously, the model names used as type hints were quoted marking them as strings;
# leading to forward references, which allow referring to a class before Python has
# fully parsed it.

# By adding from __future__ import annotations, Python defers evaluation of all type
# annotations until runtime, automatically treating them as strings. This eliminates
# the need to manually quote forward-referenced types (simplified type hinting).
from __future__ import annotations

# Python Standard Libraries
import logging
from typing import Any, Dict, List
from datetime import datetime

# Third-Party Libraries
from pydantic import ConfigDict, Field, field_validator, model_validator

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic_models.v1.bases import (
    PythonIdentifier,
    PluginModel,
    FrozenModel,
    PermissiveFrozenModel,
)
from geoips.pydantic_models.v1.coverage_checkers import CoverageCheckerArgumentsModel
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
    interface_name = Lexeme(plugin_kind).plural
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
        Lexeme(plugin_kinds).singular
        for ifs in interfaces.list_available_interfaces().values()
        for plugin_kinds in ifs
    }


class OutputFormatterArgumentsModel(PermissiveFrozenModel):
    """Validate Output Formatter arguments."""

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


class GlobalVariablesModel(PermissiveFrozenModel):
    """Workflow-level global variables shared across all steps.

    Carries fields that apply uniformly to every step of an
    Order-Based Procflow workflow rather than belonging to a
    single step's arguments. (e.g. temporal windowing, product
    identification, product DB output configuration, and the
    presectoring toggle)
    """

    window_start_time: datetime | None = Field(
        None,
        description="If specified, sector temporally between window_start_time "
        "and window_end_time.",
    )

    window_end_time: datetime | None = Field(
        None,
        description="If specified, sector temporally between window_start_time "
        "and window_end_time.",
    )

    product_name: str | None = Field(None)

    reader_defined_area_def: bool = Field(False)

    no_presectoring: bool = Field(
        True,
        description="Specify whether to resector the data prior to applying "
        "the algorithm",
    )

    product_db: bool = Field(False)

    product_db_writer: str | None = Field(None)

    product_db_writer_kwargs: Dict[str, Any] | None = Field(None)

    @model_validator(mode="after")
    def _validate_product_db_requires_writer(
        cls, model: GlobalVariablesModel
    ) -> GlobalVariablesModel:
        """Validate that product_db is fully defined.

        If product_db is defined, then a corresponding product must be specified
        as a string in product_db_writer. Also check the opposite case, where
        product_db_writer is defined, but product_db is false.
        """
        if model.product_db and model.product_db_writer is None:
            raise ValueError(
                "product_db is set while product_db_writer is not defined. "
                "Please specify a valid product_db_writer."
            )
        if model.product_db_writer is not None and not model.product_db:
            raise ValueError(
                f"product_db_writer is defined as: `{model.product_db_writer}` "
                "but product_db is False or unspecified.\nPlease explicitly "
                "invoke 'product_db = True' or drop product_db_writer."
            )

        return model

    @model_validator(mode="after")
    def _validate_window_start_requires_end(
        cls, model: GlobalVariablesModel
    ) -> GlobalVariablesModel:
        """Validate the specified time range.

        If window_start_time is defined, then window_end_time must also be
        defined. The reverse situation is also checked.
        """
        if model.window_start_time is not None and model.window_end_time is None:
            raise ValueError(
                f"window_start_time is defined as `{model.window_start_time}` "
                "but there is no defined window_end_time. Please specify a "
                "window_end_time."
            )
        if model.window_end_time is not None and model.window_start_time is None:
            raise ValueError(
                f"window_end_time is defined as `{model.window_end_time}` "
                "but there is no defined window_start_time. Please specify a "
                "window_start_time."
            )

        return model


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

    global_arguments: GlobalVariablesModel = Field(
        ..., description="Arguments shared across workflow steps"
    )
    steps: Dict[PythonIdentifier, WorkflowStepDefinitionModel] = Field(
        ..., description="Steps to produce the workflow."
    )


class WorkflowPluginModel(PluginModel):
    """A plugin that produces a workflow."""

    model_config = ConfigDict(extra="allow")
    spec: WorkflowSpecModel = Field(..., description="The workflow specification")
