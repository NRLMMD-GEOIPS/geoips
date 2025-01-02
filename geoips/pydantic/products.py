# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Order-based procflow Product building Models."""

# Python Standard Libraries
from typing import Any, Dict, List

# Third-Party Libraries
from pydantic import BaseModel, Field, model_validator, ConfigDict

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic.bases import PluginModel


def get_plugin_names(plugin_type: str) -> List[str]:
    """Retrieve a list of valid plugin names for a given plugin type.

    Parameters
    ----------
    plugin_type : str
        The type of plugin

    Returns
    -------
    list
        A list of plugin names for a valid plugin type

    Raises
    ------
    AttributeError
        If the plugin type is invalid

    """
    interface_name = plugin_type + "s"

    try:
        interface = getattr(interfaces, interface_name)
    except AttributeError:
        raise AttributeError(f"{plugin_type} is not valid plugin type")
    return [plugin.name for plugin in interface.get_plugins() or []]


def get_plugin_types() -> List[str]:
    """Retrieve a list of plugin types from available interfaces.

    Returns
    -------
    list of str
        list of possible unique plugin types
    """
    interface = []
    for ifs in interfaces.list_available_interfaces().values():
        interface.extend(ifs)
    return list(set(plugin_types[:-1] for plugin_types in interface))


class OutputFormatterArgumentsModel(BaseModel):
    """output_formatters."""

    pass


class FilenameFormatterArgumentsModel(BaseModel):
    """Validate FilenameFormatter arguments."""

    pass


class AlgorithmArgumentsModel(BaseModel):
    """Validate Algorithm arguments."""

    pass


class InterpolatorArgumentsModel(BaseModel):
    """Validate Interpolator arguments."""

    pass


class ReaderArgumentsModel(BaseModel):
    """Validate Reader step arguments."""

    model_config = ConfigDict(extra="forbid")
    area_def: str = Field(None, description="Area definition identifier.")
    chans: List[str] = Field(None, description="List of channels to process.")
    metadata_only: bool = Field(False, description="Flag for metadata-only processing.")
    self_register: bool = Field(False, description="Flag for self-registration.")


class ProductStepDefinitionModel(BaseModel):
    """Validate step definition : name, arguments."""

    model_config = ConfigDict(extra="forbid")
    type: str = Field(..., description="plugin type")
    name: str = Field(..., description="plugin name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="step args")

    @model_validator(mode="before")
    def _validate_plugin_name(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plugin name."""
        if not values:
            raise ValueError("The plugin_name cannot be empty")
        plugin_name = values.get("name", "").lower()
        plugin_type = values.get("type", " ").lower()

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
        Validate & organize details for each step.

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

        # arguments = values.get("arguments", {})
        # Delegate arguments validation to each plugin type argument class
        plugin_type = values.get("type", " ").lower()
        plugin_type_snake_case = "".join(
            [word.capitalize() for word in plugin_type.split("_")]
        )
        plugin_arguments_model_name = f"{plugin_type_snake_case}ArgumentsModel"
        print("plugin arugments model name \t", plugin_arguments_model_name)
        plugin_arguments_model = globals().get(plugin_arguments_model_name)
        if plugin_arguments_model is None:
            raise ValueError(
                f"""\n\n\tThe argument class/model "{plugin_arguments_model_name}" for
                the plugin type "{plugin_type}" is not defined.\n\n"""
            )
        plugin_arguments_model(**values.get("arguments", {}))

        return values


class ProductStepModel(BaseModel):
    """Validate and process a sequence of steps with their data."""

    definition: ProductStepDefinitionModel = Field(..., description="Sequence of steps")

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
            The processed step data after step name validation

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
                f"\n\ninvalid step name : {plugin_type}.\n\t"
                f"Must be one of {valid_types}\n\n"
            )

        # extract value for type field (if provided) otherwise
        # add the key value for step name
        if "type" not in step_data:
            step_data = {"type": plugin_type.lower(), **step_data}
            # print("plugin_type ", plugin_type)

        # ensure 'type' field matches step name
        if step_data["type"] != plugin_type:
            raise ValueError(
                f"\n\nstep name : '{plugin_type}'"
                f"and type : '{step_data['type']}' mismatch. "
                f"Check your product definition\n\n"
            )

        return {"definition": step_data}


class ProductSpecModel(BaseModel):
    """The specification for a product."""

    # list of steps
    steps: List[ProductStepModel] = Field(
        ..., description="Steps to produce the product."
    )


class ProductPluginModel(PluginModel):
    """A plugin that produces a product."""

    spec: ProductSpecModel = Field(..., description="The product specification")
