"""Product plugin format."""

from typing import Literal, Union
from pydantic import BaseModel, Field, root_validator
from geoips import interfaces

from geoips.pydantic.bases import Plugin


class ReaderArguments(BaseModel):
    """Arguments to pass to the reader plugin."""

    variables: list[str] = Field(
        None, description="The variables to read from the input file."
    )


class AlgorithmArguments(BaseModel):
    pass


class OutputFormatterArguments(BaseModel):
    """output_formatters"""
    pass

def get_interface_names():
    interface_names = []
    for ifs in interfaces.list_available_interfaces().values():
        interface_names.extend(ifs)
    return interface_names
    
class Step(BaseModel):
    interface: Literal[*get_interface_names()]
    name: str
    arguments: Union[ReaderArguments, AlgorithmArguments]

    @root_validator(pre=True)
    def validate_arguments(cls, values):
        interface_name = values.get("interface")
        interface_camel_case = "".join(
            [word.caplitalize() for word in interface_name[:-1].split("_")]
        )
        interface_arguments_model_name = f"{interface_camel_case}Arguments"
        interface_arguments_model = globals().get(interface_arguments_model_name)
        interface_arguments_model(**values.get("arguments", {}))


class ProductSpec(BaseModel):
    """The specification for a product."""

    steps: Step = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")