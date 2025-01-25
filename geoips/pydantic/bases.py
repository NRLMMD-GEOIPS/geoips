"""Pydantic base models for GeoIPS.

Intended for use by other base models.

``PluginModel`` should be used as the parent class of all other plugin models.

Other models defined here validate field types within child plugin models.
"""

# Python Standard Libraries
from functools import lru_cache
import keyword
import logging
from pathlib import Path

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated


# GeoIPS imports
from geoips.plugin_registry import plugin_registry

from geoips import interfaces

LOG = logging.getLogger(__name__)


class PrettyBaseModel(BaseModel):
    """Make Pydantic models pretty-print by default.

    This model overrides the default string representation of Pyantic models to generate
    a user-friendly, JSON-formatted output with two-space indentation.
    """

    def __str__(self) -> str:
        """Return a pretty-print string representation of a Pydantic model.

        The returned string will be formatted as JSON with two-space indentation.

        Returns
        -------
        str
            A JSON-formatted string representation of the Pydantic model.
        """
        return self.model_dump_json(indent=2)


class StaticBaseModel(PrettyBaseModel):
    """Pydantic model with a customized ``ConfigDict`` configurations for GeoIPS.

    This model extends ``PrettyBaseModel`` and uses Pydantic ConfigDict to provide
    customized configurations such as forbidding extra fields.

    # Attributes
    # ----------
    # model_config : ConfigDict
    #     Configuration for the Pydantic model:
    #     - `extra="forbid"`: Does not allow any additional fileds in the input data.
    #     - `populate_by_name=True`: Enables populaitng fields by their aliases.


    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


def python_identifier(val: str) -> str:
    """Validate if a string is a valid Python identifier.

    Validate if a string is a valid Python identifier and not a reserved Python keyword.
    `See <https://docs.python.org/3/reference/lexical_analysis.html#identifiers>`_ for
    more information on Python identifiers and reserved keywords.

    Validation is performed by calling `str.isidentifier` and `keyword.iskeyword`.

    Parameters
    ----------
    val : str
        The input string to validate.

    Returns
    -------
    str
        The input string if it is a valid Python identifier.

    Raises
    ------
    ValueError
        If the input string is invalid as a Python identifier or a reserved keyword.
    """
    error_messages = []
    if not val.isidentifier():
        error_messages.append(f"{val} is not a valid Python identifier.")
    if keyword.iskeyword(val):
        error_messages.append(f"{val} is a reserved Python keyword.")

    if error_messages:
        error_message = " ".join(error_messages) + " Please update it."
        LOG.error(error_message, exc_info=True)
        raise ValueError(error_message)

    return val


# Create the PythonIdentifier type
PythonIdentifier = Annotated[str, AfterValidator(python_identifier)]


@lru_cache(maxsize=None)
def get_interfaces() -> set[str]:
    """Return a set of distinct interfaces.

    This function returns all available plugin interfaces. The results are cached for
    runtime memory optimizaiton.

    Returns
    -------
    set of str
        set of interfaces
    """
    return {
        available_interfaces
        for ifs in interfaces.list_available_interfaces().values()
        for available_interfaces in ifs
    }


class PluginModel(StaticBaseModel):
    """Base Plugin model for all GeoIPS plugins.

    This should be used as the base class for all top-level
    PluginModels. It adds standard plugin attributes for inheritance.
    It validates YAML plugins for the order based procflow.

    See the YAML plugin documentation `here
    <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/docs/source/tutorials/plugin_development/product_default.rst>`_
    for more information about how this is used.
    """

    interface: PythonIdentifier = Field(
        ...,
        description="""Name of the plugin's interface. Run geoips list interfaces to see
        available options.""",
    )
    family: PythonIdentifier = Field(..., description="Family of the plugin.")
    name: PythonIdentifier = Field(..., description="Plugin name.")
    docstring: str = Field(..., description="Docstring for the plugin in numpy format.")
    description: str = Field(
        None,
        description=("A short description or defaults to first line from docstring."),
    )
    package: PythonIdentifier = Field(
        ...,
        description="Package that contains this plugin.",
        default_factory=plugin_registry.get_package_name,
    )
    relpath: str = Field(
        None, description="Path to the plugin file relative to its parent package."
    )
    abspath: str = Field(None, description="Absolute path to the plugin file.")

    @field_validator("interface", mode="before")
    def valid_interface(cls, value: PythonIdentifier) -> PythonIdentifier:
        """
        Validate the input for the 'interface' field.

        Ensures that the input value is one of the valid interfaces. Raises a ValueError
        if the input is not valid.

        Parameters
        ----------
        cls : Type
            PluginModel class.
        value :
            Value of the 'interface' field to validate.

        Returns
        -------
        PythonIdentifier
            Validated value if it is valid.

        Raises
        ------
        ValueError
            If the 'interface' field value is not in the list of valid interfaces.
        """
        valid_interfaces = get_interfaces()
        if value not in valid_interfaces:
            raise ValueError(
                f"Incorrect interface: {value}.Must be one of {valid_interfaces}"
            )
        return value

    # TODO: Update to have two validators, allowing for full numpy docstrings
    @model_validator(mode="before")
    def _set_description(
        cls: type["PluginModel"], values: dict[str, str | int | float | None]
    ):
        """
        Set ``description`` to first line of ``dosctring`` field if not provided.

        Parameters
        ----------
        values : dict
            Dictionary of field values before validation.

        Returns
        -------
        dict
            Updated dictionary of field values, setting ``description`` if it was not
            provided.

        """
        if "description" not in values or values.get("description") is None:
            first_line = values.get("docstring")
            if first_line:
                values["description"] = (
                    values.get("docstring").strip().split("\n", 1)[0].strip()
                )
        return values

    @field_validator("description", mode="after")
    def validate_one_line_description(cls: type["PluginModel"], value: str) -> str:
        """
        Validate that the description adheres to required single line standards.

        The description string must meet the following requirements:
        - Must be a single line.
        - First letter must be be alphanumeric.
        - Must end with a period.
        - Must not exceed 72 characters.

        Parameters
        ----------
        value : str
            ``description`` string to validate.

        Returns
        -------
        str
            Validated ``description`` string.

        Raises
        ------
        PydanticCustomError
            If the ``description`` field violates any of the validation rules.
        """
        if "\n" in value:
            raise PydanticCustomError(
                "single_line", "Description must be a single line.\n"
            )
        if not (value[0].isalnum() and value.endswith(".")):
            raise PydanticCustomError(
                "format_error",
                "Description must start with a letter or number and end with a period.",
            )
        if len("description") > 72:
            raise PydanticCustomError(
                "length_error", "Description cannot be more than 72 characters."
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
