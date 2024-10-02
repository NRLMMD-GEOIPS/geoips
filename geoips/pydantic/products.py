"""Product plugin format."""

from typing import Literal
from pydantic import BaseModel, Field
from geoips.pydantic.bases import Plugin


class ReaderArguments(BaseModel):
    """Arguments to pass to the reader plugin."""

    variables: list[str] = Field(
        None, description="The variables to read from the input file."
    )


class ReaderStep(BaseModel):
    """A step to read data from a file."""

    # I'm not sure that I like this syntax. I also am not sure that I like the error
    # that it generates when someone attempts to set this to a different value.
    # When set to a different value, the error raised is:
    #
    #    ValidationError: 1 validation error for Mine
    #    interface
    #      Input should be 'readers' [type=literal_error, input_value='SomeoneElse', input_type=str]
    #        For further information visit
    #        https://errors.pydantic.dev/2.8/v/literal_error
    #
    # Another option would be to use typing.ClassVar but that would hide the attribute
    # from the model. It would still be accessible as a class attribute but it would not
    # be visible in the model's documentation, it's string representation, etc.
    #
    # Maybe this could be set on a base ProductStep class to validate against the name
    # of the class or against a ClassVar.
    #
    # I'm definitely open to solutions here.
    #
    # The behavior that I'd like to see is that the interface attribute defaults to
    # "readers" and is not required. If it is set, it must be set to "readers". If it is
    # set to a different value it should raise an error that is more informative than
    # the one that is currently raised.
    interface: Literal["readers"] = "readers"

    reader: str = Field(description="The name of the reader plugin to be used.")
    arguments: ReaderArguments = Field(
        description="The arguments to pass to the reader plugin."
    )


class ProductSpec(BaseModel):
    """The specification for a product."""

    steps: list[ReaderStep] = Field(description="The steps to produce the product.")


class ProductPlugin(Plugin):
    """A plugin that produces a product."""

    spec: ProductSpec = Field(description="The product specification")
