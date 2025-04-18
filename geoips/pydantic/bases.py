"""Pydantic base models for GeoIPS.

Intended for use by other base models.

``PluginModel`` should be used as the parent class of all other plugin models.

Other models defined here validate field types within child plugin models.
"""

# Python Standard Libraries
import keyword
import logging
from typing import Union, Tuple
import warnings

# Third-Party Libraries
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated


# GeoIPS imports
from geoips import interfaces

LOG = logging.getLogger(__name__)

ColorTuple = Union[
    Tuple[float, float, float], Tuple[int, int, int], Tuple[int, int, int, float]
]
ColorType = Union[ColorTuple, str]


class PrettyBaseModel(BaseModel):
    """Make Pydantic models pretty-print by default.

    This model overrides the default string representation of Pydantic models to
    generate a user-friendly, JSON-formatted output with two-space indentation.
    """

    def __str__(self) -> str:
        """Return a pretty-print string representation of a Pydantic model.

        The returned string will be formatted as JSON with two-space indentation.

        Returns
        -------
        str
            A JSON-formatted string representation of the Pydantic model.
        """
        # exclude_none removes all optional fields that were unset and default to None
        return self.model_dump_json(indent=2, exclude_none=True)


class FrozenModel(PrettyBaseModel):
    """Pydantic model with a customized ``ConfigDict`` configurations for GeoIPS.

    This model extends ``PrettyBaseModel`` and uses Pydantic's ConfigDict to provide
    customized configurations. It is intended for use in cases where additional fields
    are not allowed, and the object data cannot be modified after initialization.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)


class PermissiveFrozenModel(PrettyBaseModel):
    """Pydantic model with a customized ``ConfigDict`` configurations for GeoIPS.

    This model extends ``PrettyBaseModel`` and uses Pydantic's ConfigDict to provide
    customized configurations. It is intended for use in cases where additional fields
    are allowed, but the object data cannot be modified after initialization.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, frozen=True)


class DynamicModel(PrettyBaseModel):
    """Pydantic model with a customized ``ConfigDict`` configurations for GeoIPS.

    This model extends ``PrettyBaseModel`` and uses Pydantic's ConfigDict to provide
    customized configurations. It is intended for use in cases where additional fields
    are not allowed, but the object data can be modified after initialization.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=False)


class PermissiveDynamicModel(PrettyBaseModel):
    """Pydantic model with a customized ``ConfigDict`` configurations for GeoIPS.

    This model extends ``PrettyBaseModel`` and uses Pydantic's ConfigDict to provide
    customized configurations. It is intended for use in cases where additional fields
    are allowed, and the object data can be modified after initialization.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, frozen=False)


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
        error_messages.append(f"'{val}' is not a valid Python identifier.")
    if keyword.iskeyword(val):
        error_messages.append(f"'{val}' is a reserved Python keyword.")

    if error_messages:
        error_message = " ".join(error_messages) + " Please update it."
        LOG.interactive(error_message, exc_info=True)
        raise ValueError(error_message)

    return val


# Create the PythonIdentifier type
PythonIdentifier = Annotated[str, AfterValidator(python_identifier)]


def get_interfaces() -> set[str]:
    """Return a set of distinct interfaces.

    This function returns all available plugin interfaces. The results are cached for
    runtime memory optimization.

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


class PluginModel(FrozenModel):
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
    package: PythonIdentifier = (
        Field(
            None,
            description=(
                "Automatically derived package name for this plugin. Users "
                "must not set this field manually."
            ),
        ),
    )
    relpath: str = Field(
        None, description="Path to the plugin file relative to its parent package."
    )
    abspath: str = Field(None, description="Absolute path to the plugin file.")

    @model_validator(mode="before")
    def _derive_package_name(
        cls: type["PluginModel"], values: dict[str, str | int | float | None]
    ):
        """
        'package' value is derived by calling ``get_plugin_metadata()``.

        Parameters
        ----------
        values : dict
            Dictionary of field values before validation.

        Returns
        -------
        dict
            Updated dictionary with the `package` field set based on the
            metadata retrieved from ``get_plugin_metadata()``.
        """
        # name is guaranteed to exist due to Pydantic validation.
        # No need to raise an error for 'name'.
        interface_name = values.get("interface")
        try:
            interface = getattr(interfaces, interface_name)
        except AttributeError:
            raise ValueError(
                f"Invalid interface: '{interface_name}'."
                f"Must be one of {get_interfaces()}"
            )

        try:
            metadata = interface.get_plugin_metadata(values.get("name"))
        except KeyError:
            raise ValueError(f"Plugin not found: '{values.get('name')}'")
        # the above exception handling would be further improved by checking the
        # existence of plugin registry in the future issue #906

        if "package" not in metadata:
            err_msg = (
                "Metadata for '%s' workflow plugin must contain 'package' key."
                % values.get("name")
            )
            LOG.critical(err_msg)
            raise ValueError(err_msg)
        values["package"] = metadata.get("package")
        return values

    @field_validator("interface", mode="before")
    def _validate_interface(cls, value: PythonIdentifier) -> PythonIdentifier:
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
            err_msg = f"Incorrect interface:'{value}'.Must be one of {valid_interfaces}"
            LOG.critical(err_msg, exc_info=True)
            raise ValueError(err_msg)
        return value

    @model_validator(mode="before")
    def _set_description(
        cls: type["PluginModel"], values: dict[str, str | int | float | None]
    ):
        """
        Set ``description`` to first line of ``docstring`` field if not provided.

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
            temp_string = values.get("docstring")
            if temp_string:
                values["description"] = temp_string.strip().split("\n", 1)[0].strip()
        return values

    @field_validator("description", mode="after")
    def _validate_one_line_description(cls: type["PluginModel"], value: str) -> str:
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
        error_messages = {
            "single_line": "Description must be a single line.",
            "format_error": (
                "Description must start with a letter / number and end" "with a period."
            ),
            "length_error": "Description cannot be more than 72 characters, reduce by:",
        }
        try:
            if "\n" in value:
                LOG.critical(
                    "'error': %s 'input_provided': %r",
                    error_messages["single_line"],
                    value,
                    exc_info=True,
                )
                raise PydanticCustomError("single_line", error_messages["single_line"])
            if not (value[0].isalnum() and value.endswith(".")):
                LOG.critical(
                    "'error': %s 'input_provided': %r",
                    error_messages["format_error"],
                    value,
                    exc_info=True,
                )
                raise PydanticCustomError(
                    "format_error", error_messages["format_error"]
                )
            if len(value) > 72:
                excess_length = len(value) - 72
                err_msg = f"{error_messages['length_error']} {excess_length} characters"
                LOG.critical(
                    "'error': %s 'input_provided': %r", err_msg, value, exc_info=True
                )
                raise PydanticCustomError("length_error", err_msg)
        except PydanticCustomError as e:
            LOG.warning(
                f"Future ValidationError encoutnered. This will become an "
                f"error in a future release. {e}"
            )

        return value
