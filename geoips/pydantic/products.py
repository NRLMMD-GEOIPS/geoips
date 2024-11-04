"""Product plugin format."""

# Python Standard Libraries
from typing import Any, Dict, List

# Third-Party Libraries
from pydantic import BaseModel, Field, model_validator

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic.bases import Plugin


def get_plugin_names(plugin_type):
    """Retrieve a list of valid plugin names for a given plugin type."""
    plugin_names = []
    interface_name = plugin_type + "s"

    try:
        interface = getattr(interfaces, interface_name)
    except AttributeError:
        raise AttributeError(
            f"{plugin_type} is not valid plugin type"
        )
    plugin_names = [plugin.name for plugin in interface.get_plugins()]
    return plugin_names


def get_plugin_types():
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


class OutputFormatterArgumentsValidator(BaseModel):
    """output_formatters."""

    pass


class FilenameFormatterArgumentsValidator(BaseModel):
    """Validate FilenameFormatter arguments."""

    pass


class AlgorithmArgumentsValidator(BaseModel):
    """Validate Algorithm arguments."""

    pass


class InterpolatorArgumentsValidator(BaseModel):
    """Validate Interpolator arguments."""

    pass


class ReaderArgumentsValidator(BaseModel):
    """Validate Reader step arguments."""

    @model_validator(mode="before")
    def _validate_reader_arguments(values: dict) -> dict:
        """Validate Reader step arguments."""
        reader_arguments_list = ["variables", "area_def", "metadata_only", "chans", "self_register"]
        for arg in reader_arguments_list:
            if arg not in values:
                raise ValueError(f"\n\n\tMissing argument:{arg} for reader plugin.\n\n")

        return values


class StepDefinition(BaseModel):
    """Validate step definition : name, arguments."""

    type: str = Field(description="plugin type")
    name: str = Field(description="plugin name")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the step."
    )

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
        Validate & organize details for each step   .

        Parameters
        ----------
        values : dict
            A dictionary of plugin data. The key is plugin type, and
            the value consists of plugin name & arguments

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
        plugin_type_camel_case = "".join(
            [word.capitalize() for word in plugin_type.split("_")]
        )
        plugin_arguments_model_name = f"{plugin_type_camel_case}ArgumentsValidator"
        plugin_arguments_model = globals().get(plugin_arguments_model_name)
        if plugin_arguments_model is None:
            raise ValueError(f"\n\n\tThe plugin type argument class"
                             f"{plugin_arguments_model_name} is not defined\n\n")
        plugin_arguments_model(**values.get("arguments", {}))

        return values


class Step(BaseModel):
    """Validate and process a sequence of steps with their data."""

    definition: StepDefinition

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


class ProductSpec(BaseModel):
    """The specification for a product."""

    # list of steps
    steps: List[Step] = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin, BaseModel):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")
