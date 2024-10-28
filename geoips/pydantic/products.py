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


class ReaderArguments:
    """Validate Reader step arguments."""

    @staticmethod
    def validate(values: dict) -> dict:
        """Validate Reader step arguments."""
        # reader_arguments_list = ["fnames"]
        # for arg in reader_arguments_list:
        #     if arg not in values.get("arguments", {}):
        #         raise ValueError("Missing 'reader_specific_arg' for reader plugin.")
        return values


class Step(BaseModel):
    """Lists sequence of steps along with the step data."""

    type: str = Field(description="interface type")
    name: str
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the step."
    )

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
        # The following if else ladder would go away eventually once
        # we have classes for all the steps / plugin types

        if plugin_type == 'reader':
            values = ReaderArguments.validate(values)
        # else:
        #     raise ValueError(f"\nUnknown plugin type:{plugin_type} arguments provided"
        #                      f"can't validate, try a valid plugin type\n")

        return values


class ProductSpec(BaseModel):
    """The specification for a product."""

    # list of steps
    steps: List[Step] = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")
