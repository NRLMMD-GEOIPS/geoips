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
from pydantic import ConfigDict, Field, model_validator

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic.bases import PluginModel, FrozenModel, PermissiveFrozenModel

LOG = logging.getLogger(__name__)


def get_plugin_names(plugin_type: str) -> List[str]:
    """Return valid plugin names for passed plugin type.

    Parameters
    ----------
    plugin_type : str
        valid plugin interface name

    Returns
    -------
    list
        A list of plugin names for a valid plugin type

    Raises
    ------
    AttributeError
        If the plugin type is invalid

    """
    interface_name = plugin_type
    try:
        if not interface_name[:-1] == "s":
            interface_name = plugin_type + "s"
    except IndexError as e:
        raise ValueError("'plugin_type' must be at least one character.") from e

    try:
        interface = getattr(interfaces, interface_name)
    except AttributeError as e:
        error_message = f"{plugin_type} is not a valid plugin type"
        LOG.critical(error_message, exc_info=True)
        raise AttributeError(error_message) from e
    return [plugin.name for plugin in interface.get_plugins() or []]


def get_plugin_types() -> set[str]:
    """Return plugin types from available interfaces.

    Returns
    -------
    set of str
        singular names of distinct plugin types
    """
    return {
        # set comprehension
        # the [:-1] slice converts the plugin type from plural to singular
        # eg. 'Readers' => 'Reader'
        plugin_types[:-1]
        for ifs in interfaces.list_available_interfaces().values()
        for plugin_types in ifs
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

    model_config = ConfigDict(extra="allow")
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
    """Validate step definition : name, arguments."""

    type: str = Field(
        ..., description="for internal use only, plugin type", exclude=True
    )
    name: str = Field(..., description="plugin name", init=False)
    arguments: Dict[str, Any] = Field(default_factory=dict, description="step args")

    @model_validator(mode="after")
    def _validate_plugin_name(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plugin name."""
        plugin_name = values.name
        plugin_type = values.type

        valid_plugin_names = get_plugin_names(plugin_type)
        if plugin_name not in valid_plugin_names:
            raise ValueError(
                f"{plugin_name} is invalid. \n\t"
                f"Must be one of {sorted(valid_plugin_names)}"
            )

        return values

    @model_validator(mode="before")
    def _validate_plugin_arguments(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and organize details for each step.

        Parameters
        ----------
        values : dict
            A dictionary of plugin data. The key is plugin type, and
            the value consists of plugin name and arguments

        Returns
        -------
        values : dict
            A validated and structured dictionary with the following fields:

            - `type` : str
                The type of the plugin.
            - `name` : str
                The name of the plugin.
            - `arguments` : dict
                The arguments associated with the plugin.

        """
        if not values:
            raise ValueError("Empty : Missing step details")

        # Delegate arguments validation to each plugin type argument class
        plugin_type = values.get("type")
        if not plugin_type:
            raise ValueError("Plugin name cannot be empty")
        plugin_type_pascal_case = "".join(
            [word.capitalize() for word in plugin_type.split("_")]
        )
        plugin_arguments_model_name = f"{plugin_type_pascal_case}ArgumentsModel"
        # Dictionary listing all plugin arguments models
        plugin_arguments_models = {
            "ReaderArgumentsModel": ReaderArgumentsModel,
            "AlgorithmArgumentsModel": AlgorithmArgumentsModel,
            "InterpolatorArgumentsModel": InterpolatorArgumentsModel,
            "FilenameFormatterArgumentsModel": FilenameFormatterArgumentsModel,
            "OutputFormatterArgumentsModel": OutputFormatterArgumentsModel,
            "CoverageCheckerArgumentsModel": CoverageCheckerArgumentsModel,
        }
        plugin_arguments_model = plugin_arguments_models.get(
            plugin_arguments_model_name
        )
        if plugin_arguments_model is None:
            raise ValueError(
                f'The argument class/model "{plugin_arguments_model_name}" for'
                f'the plugin type "{plugin_type}" is not defined.'
            )
        plugin_arguments_model(**values.get("arguments", {}))

        return values


class WorkflowStepModel(FrozenModel):
    """Validate and process a sequence of steps with their data."""

    definition: WorkflowStepDefinitionModel = Field(
        ..., description="Sequence of workflow steps"
    )

    @model_validator(mode="before")
    def _plugin_name_validator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate user input for the plugin type.

        Parameters
        ----------
        values : dict
            The step data containing step name (plugin type) and its content.

        Returns
        -------
        dict
            processed step data after step name validation.


        Raises
        ------
        ValueError
            if the user input step name is not in the valid_types list
            if the user input step name and type (if provided) are not same
        """
        if not values:
            raise ValueError("Empty : Step data cannot be empty.")

        valid_types = get_plugin_types()

        # extract step name and step data
        plugin_type, step_data = next(iter(values.items()))

        # raise error if the step name (plugin type) is not valid
        if plugin_type not in valid_types:
            raise ValueError(
                f"invalid step name : {plugin_type}.\n\t"
                f"Must be one of {valid_types}\n\n"
            )

        # extract value for type field (if provided) otherwise
        # add the key value for step name
        if "type" not in step_data:
            step_data["type"] = plugin_type

        # ensure 'type' field matches step name
        if step_data["type"] != plugin_type:
            raise ValueError(
                f"step name : '{plugin_type}'"
                f"and type : '{step_data['type']}' mismatch. "
                f"Check your workflow definition\n\n"
            )

        return {"definition": step_data}


class WorkflowSpecModel(FrozenModel):
    """The specification for a workflow."""

    # list of steps
    steps: List[WorkflowStepModel] = Field(
        ..., description="Steps to produce the workflow."
    )


class WorkflowPluginModel(PluginModel):
    """A plugin that produces a workflow."""

    model_config = ConfigDict(extra="allow")
    spec: WorkflowSpecModel = Field(..., description="The workflow specification")
