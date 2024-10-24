"""Product plugin format."""

from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, List, Literal

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

    type: Literal[*get_plugin_types()] = Field(description="interface type")
    name: str
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the step."
    )

    @model_validator(mode='before')
    def validate_arguments(cls, values):

        interface_type, plugin_data = next(iter(values.items()))

        valid_interfaces = get_plugin_types()
        if interface_type not in get_plugin_types():
            raise ValueError(
                f"Invalid interface type: {interface_type}"
                f"\ninterface must be one of \n\t: {valid_interfaces} \n\n"
            )

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
