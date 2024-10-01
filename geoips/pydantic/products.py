"""Product plugin format."""

from pydantic import BaseModel, Field
from geoips.pydantic.bases import Plugin


class ReaderArguments(BaseModel):
    """Arguments to pass to the reader plugin."""

    variables: list[str] = Field(
        None, description="The variables to read from the input file."
    )


class ReaderStep(BaseModel):
    """A step to read data from a file."""

    name: str = Field(description="The name of the reader plugin to be used.")
    arguments: ReaderArguments = Field(
        description="The arguments to pass to the reader plugin."
    )


class ProductSpec(BaseModel):
    """The specification for a product."""

    steps: list[ReaderStep] = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")
