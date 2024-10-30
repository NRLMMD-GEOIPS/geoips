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

    type: str = Field(description="plugin type")
    name: str = Field(desciption="plugin name")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the step."
    )

    @model_validator(mode="before")
    def validate_arguments(cls, values):
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

        plugin_type, plugin_data = next(iter(values.items()))
        values["type"] = plugin_type
        values["name"] = plugin_data.get("name", "")
        values["arguments"] = plugin_data.get("arguments", {})

        # Delegate arguments validation to each plugin type argument class
        plugin_type_camel_case = "".join(
            [word.capitalize() for word in plugin_type.split("_")]
        )
        plugin_arguments_model_name = f"{plugin_type_camel_case}Arguments"
        plugin_arguments_model = globals().get(plugin_arguments_model_name)
        plugin_arguments_model(**values.get("arguments", {}))

        return values


class Step(BaseModel):
    """Lists sequence of steps along with the step data."""

    # type: str = Field(description="plugin type")
    # name: str
    # arguments: Dict[str, Any] = Field(
    #     default_factory=dict, description="Arguments for the step."
    # )

    @field_validator("type")
    def validate_type(cls, v):
        """
        Validate user input for the plugin type.

        Parameters
        ----------
        v : str
            The user provided step name, also known as plugin type

        Returns
        -------
        str
            The validated plugin type

        Raises
        ------
        ValueError
            if the user input plugin type is not in the valid_types list
        """
        if not v:
            raise ValueError("Empty : Missing step name / plugin type")

        valid_types = get_plugin_types()
        if v not in valid_types:
            raise ValueError(
                f"\n\ninvalid plugin type: {v}.\n\t Must be one of {valid_types}\n\n"
            )
        return v


class ProductSpec(BaseModel):
    """The specification for a product."""

    # list of steps
    steps: List[Step] = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")
