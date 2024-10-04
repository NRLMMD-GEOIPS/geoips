"""Product plugin format."""

from typing import Literal, Union
from pydantic import BaseModel, Field, root_validator

from geoips.pydantic.bases import Plugin


class ReaderArguments(BaseModel):
    """Arguments to pass to the reader plugin."""

    variables: list[str] = Field(
        None, description="The variables to read from the input file."
    )

class ReaderInterfaceStep(BaseModel):
    """A step to read interface name for the reader"""
    interface: Literal["readers"] = Field(
        default="readers", 
        description="Interface name, must be 'readers'",
        frozen=True
    )


class ReaderStep(BaseModel):
    """A step to read data from a file."""
    reader: str = Field(description="The name of the reader plugin to be used.")
    arguments: ReaderArguments = Field(
        description="The arguments to pass to the reader plugin."
    )

class ProductSpec(BaseModel):
    """The specification for a product."""

    steps: list[Union[ReaderInterfaceStep, ReaderStep]] = Field(description="The steps to produce the product.")

    @root_validator(pre=True)
    def ensure_interface_step(cls, values):
        """Ensure that 'interface: readers' step is present if not explicitly provided."""
        steps = values.get('steps', [])
        
        # Check if there is no 'interface: readers' step and insert it as the first step if missing
        if not any(isinstance(step, dict) and step.get('interface') == 'readers' for step in steps):
            # Insert 'interface: readers' step as the first step
            steps.insert(0, {"interface": "readers"})
        
        values['steps'] = steps
        return values

    def get_interface(self):
        for step in self.steps:
            if hasattr(step, 'interface'):
                return step.interface
    
    def get_reader(self):
        for step in self.steps:
            if hasattr(step, 'reader'):
                return step.reader
    
    def get_reader_variables(self):
        for step in self.steps:
            if hasattr(step, 'arguments'):
                return step.arguments.variables


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")

    def get_interface(self):
        return self.spec.get_interface()

    def get_reader(self):
        return self.spec.get_reader()

    def get_reader_variables(self):
        return self.spec.get_reader_variables()
        
    



