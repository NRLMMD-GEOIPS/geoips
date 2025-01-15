"""Pydantic base models for GeoIPS.

Intended for use by other base models.

``PluginModel`` should be used as the parent class of all other plugin models.

Other models defined here validate field types within child plugin models.
"""

# Python Standard Libraries
import keyword
from pathlib import Path
from typing import Tuple


# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated


class PrettyBaseModel(BaseModel):
    """Make Pydantic models pretty-print by default."""

    def __str__(self) -> str:
        """Return a pretty-print string representation of a Pydantic model.

        The returned string will be formatted as JSON with two-space indentation.

        Returns
        -------
            str: A string representation of the Pydantic model.
        """
        return self.model_dump_json(indent=2)


class StaticBaseModel(PrettyBaseModel):
    """A pydantic model with a custom Pydantic ConfigDict."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


def python_identifier(val: str) -> str:
    """Validate if a string is a valid Python identifier.

    Validate if a string is a valid Python identifier and not a reserved Python keyword.
    See https://docs.python.org/3/reference/lexical_analysis.html#identifiers for more
    information on Python identifiers and reserved keywords.

    Validation is performed by calling `str.isidentifier` and `keyword.iskeyword`.

    Parameters
    ----------
        val: str
            The input string to validate.

    Returns
    -------
        str: The input string if it is a valid Python identifier.

    Raises
    ------
        ValueError: If the input string is not a valid Python identifier or if it's a
        reserved Python keyword.
    """
    if not val.isidentifier():
        raise ValueError(f"{val} is not a valid Python identifier")
    if keyword.iskeyword(val):
        raise ValueError(f"{val} is a reserved Python keyword")
    return val


# Create the PythonIdentifier type
PythonIdentifier = Annotated[str, AfterValidator(python_identifier)]


class PluginModel(StaticBaseModel):
    """Base Plugin model for all GeoIPS plugins.

    This should be used as the base class for all top-level
    PluginModels. It adds standard plugin attributes for inheritance.
    It validates YAML plugins for the order based procflow.

    See the YAML plugin documentation here for more information about
    how this is used. [TODO: add link]
    """

    # TODO: constrain this list to the interfaces of GeoIPS
    interface: PythonIdentifier = Field(
        ...,
        description="""Name of the plugin's interface. Run geoips list interfaces to see
        available options.""",
    )
    family: PythonIdentifier = Field(
        ..., description="Family of the plugin."
    )  # TODO: constrain this list to the interfaces of GeoIPS
    name: PythonIdentifier = Field(..., description="Plugin name.")
    docstring: str = Field(..., description="Docstring for the plugin in numpy format.")
    package: PythonIdentifier = Field(
        None, description="Package that contains this plugin."
    )
    relpath: str = Field(
        None, description="Path to the plugin file relative to its parent package."
    )
    abspath: str = Field(None, description="Absolute path to the plugin file.")

    # TODO: Update to have two validators, allowing for full numpy docstrings
    @field_validator("docstring")
    def validate_one_line_numpy_docstring(cls: type["PluginModel"], value: str) -> str:
        """Validate string is one line, starts uppercase, and ends with a period."""
        if "\n" in value:
            raise PydanticCustomError(
                "single_line", "Docstring must be a single line.\n"
            )
        if not (value[0].isupper() and value.endswith(".")):
            raise PydanticCustomError(
                "format_error",
                "Docstring must start with a capital letter and end with a period.",
            )
        return value

    @field_validator("relpath")
    def validate_relative_path(cls: type["PluginModel"], value: str) -> str:
        """Validate string can be cast as Path and is a relative path."""
        custom_exception = PydanticCustomError(
            "relative_path_error",
            f"'relpath' must be relative path. Got '{value}'.",
        )
        try:
            path = Path(value)
        except (ValueError, TypeError) as e:
            raise custom_exception from e

        if path.is_absolute():
            raise custom_exception
        return value

    @field_validator("abspath")
    def validate_absolute_path(cls: type["PluginModel"], value: str) -> str:
        """Validate string can be cast as Path and is an absolute path."""
        custom_exception = PydanticCustomError(
            "absolute_path_error",
            f"'abspath' must be absolute path. Got '{value}'.",
        )
        try:
            path = Path(value)
        except (ValueError, TypeError) as e:
            raise custom_exception from e

        if not path.is_absolute():
            raise custom_exception
        return value


