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


# class OutputFormatterArguments(BaseModel):
#     """output_formatters."""

#     pass


# class FilenameFormatterArguments(BaseModel):
#     """Validate FilenameFormatter arguments."""

#     pass


# class AlgorithmArguments(BaseModel):
#     """Validate Algorithm arguments."""

#     pass


# class InterpolatorArguments(BaseModel):
#     """Validate Interpolator arguments."""

#     pass


# class ReaderArguments(BaseModel):
#     """Validate Reader step arguments."""

#     @model_validator(mode="before")
#     def validate(values: dict) -> dict:
#         """Validate Reader step arguments."""
#         reader_arguments_list = ["variables"]
#         for arg in reader_arguments_list:
#             if arg not in values:
#                 raise ValueError(f"\n\n\tMissing argument:{arg} for reader plugin.\n\n")

#         return values


class StepDefinition(BaseModel):
    """Validate step definition : name, arguments."""

    pass


class Step(BaseModel):
    """Lists sequence of steps along with the step data."""

    definition: StepDefinition

    @model_validator(mode="before")
    def step_name_validator(cls, values):
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
        if not values:
            raise ValueError("Empty : Missing step data")

        valid_types = get_plugin_types()
        step_name, step_data = next(iter(values.items()))
        if step_name not in valid_types:
            raise ValueError(
                f"\n\ninvalid step name : {step_name}.\n\t"
                f"Must be one of {valid_types}\n\n"
            )

        step_name, step_data = next(iter(values.items()))

        plugin_type = step_data.get("type", "")
        if "type" not in step_data:
            step_data = {"type": step_name.lower(), **step_data}
            plugin_type = step_data.get("type", "")
            print("plugin_type ", plugin_type)

        if plugin_type != step_name:
            raise ValueError(
                f"\n\nstep name : '{step_name}' and type : '{plugin_type}' mismatch. "
                f"Check your product definition\n\n"
            )
        return values


class ProductSpec(BaseModel):
    """The specification for a product."""

    # list of steps
    steps: List[Step] = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")
