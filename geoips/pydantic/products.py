"""Product plugin format."""

from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Any, Dict, List

from geoips import interfaces
from geoips.pydantic.bases import Plugin


def get_plugin_types():
    """Generates list of possible plugin types."""
    interface_types = []
    for ifs in interfaces.list_available_interfaces().values():
        interface_types.extend(ifs)
    return list(set(interface[:-1] for interface in interface_types))


class Step(BaseModel):
    """Lists sequence of steps along with the step data."""

    type: str = Field(description="interface type")
    name: str
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the step."
    )

    @field_validator("type")
    def validate_type(cls, v):
        if v not in get_plugin_types():
            raise ValueError(
                f"invalid plugin type {type} must be one of {get_plugin_types()}"
            )
        return v

    @model_validator(mode="before")
    def validate_arguments(cls, values):

        interface_type, plugin_data = next(iter(values.items()))

        print(f"interface type : {interface_type}")
        values["type"] = interface_type
        values["name"] = plugin_data.get("name", "")
        print("plugin name : ", values["name"])
        values["arguments"] = plugin_data.get("arguments", {})
        print("plugin arguments : ", values["arguments"])
        print("\n\n")
        # values.update(plugin_data)
        return values


class ProductSpec(BaseModel):
    """The specification for a product."""

    # list of steps
    steps: List[Step] = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")
