"""Product plugin format."""

from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Any, Dict, List

from geoips import interfaces
from geoips.pydantic.bases import Plugin


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


class OutputFormatterArguments(BaseModel):
    """output_formatters."""

    pass


class FilenameFormatterArguments(BaseModel):
    """Validate FilenameFormatter arguments."""

    pass


class AlgorithmArguments(BaseModel):
    """Validate Algorithm arguments."""

    pass


class InterpolatorArguments(BaseModel):
    """Validate Interpolator arguments."""

    pass


class ReaderArguments(BaseModel):
    """Validate Reader step arguments."""

    @model_validator(mode="before")
    def validate(values: dict) -> dict:
        """Validate Reader step arguments."""
        reader_arguments_list = ["variables"]
        for arg in reader_arguments_list:
            if arg not in values:
                raise ValueError(f"\n\n\tMissing argument:{arg} for reader plugin.\n\n")

        return values


class StepDefinition(BaseModel):
    """Validate step definition : name, arguments."""

    step_name: str
    type: str = Field(description="plugin type")
    name: str = Field(desciption="plugin name")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the step."
    )

    @field_validator("name")
    def validate_plugin_name(cls, value: str) -> str:
        """Validate plugin name."""
        # print("plugin name is ", value)
        if not value:
            raise ValueError("The plugin_name cannot be empty")
        # print("plugin_name validation to be implemented")
        return value

    @model_validator(mode="before")
    def validate_arguments(cls, values: Dict[str, Any]) -> Dict[str, Any]:
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
        plugin_arguments_model_name = f"{plugin_type_camel_case}Arguments"
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
    def step_name_validator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
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
        step_name, step_data = next(iter(values.items()))

        # raise error if the step name (plugin type) is not valid
        if step_name not in valid_types:
            raise ValueError(
                f"\n\ninvalid step name : {step_name}.\n\t"
                f"Must be one of {valid_types}\n\n"
            )

        # extract value for type field (if provided) otherwise
        # add the key value for step name
        plugin_type = step_data.get("type", "")
        if "type" not in step_data:
            step_data = {"type": step_name.lower(), **step_data}
            plugin_type = step_data.get("type", "")
            # print("plugin_type ", plugin_type)

        # ensure 'type' field matches step name 
        if plugin_type != step_name:
            raise ValueError(
                f"\n\nstep name : '{step_name}'"
                f"and type : '{plugin_type}' mismatch. "
                f"Check your product definition\n\n"
            )

        # add step name to the step data
        step_data["step_name"] = step_name

        return {"definition": step_data}


class ProductSpec(BaseModel):
    """The specification for a product."""

    # list of steps
    steps: List[Step] = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")
