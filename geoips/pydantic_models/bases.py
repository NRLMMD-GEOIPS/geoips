# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic base models for GeoIPS.

Intended for use by other base models.

``PluginModel`` should be used as the parent class of all other plugin models.

Other models defined here validate field types within child plugin models.
"""

from __future__ import annotations

# Python Standard Libraries
import keyword
import logging
from typing import ClassVar, Union, Tuple

# Third-Party Libraries
from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
)
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

# GeoIPS imports
from geoips import interfaces

# from geoips.pydantic_models.bases import FrozenModel
from geoips.geoips_utils import get_interface_module

LOG = logging.getLogger(__name__)

ColorTuple = Union[Tuple[float, float, float], Tuple[float, float, float, float]]
ColorType = Union[ColorTuple, str]


class CoreBaseModel(BaseModel):
    """CoreBaseModel for GeoIPS Order-Based Procflow data model validation.

    This model provides a standardized Pydantic base class with custom configuration
    and validation logic for all GeoIPS models built using Pydantic library. It
    consolidates useful configurations, custom validators, and utility methods.

    Features
    --------
    - Pretty-printing:
        Make Pydantic models pretty-print by default. Overrides the default string
        representation of Pydantic models to generate a user-friendly, JSON-formatted
        output with two-space indentation.

    - Configured Options:
        Includes a customized ``ConfigDict`` with the following options set:

        - `str_strip_whitespace=True` to trim whitespace around input.
        - `validate_by_alias=True` to populate data using aliased field names.
        - `validate_by_name=True` to populate an aliased using its model-defined name.
        - `loc_by_alias=False` to disallow usage of alias field name in error locations.
        - `validate_assignment=False` Disables model revalidation when data is changed.
        - `arbitrary_types_allowed=True` to allow custom data types as field types.
        - `strict=False` to disallow coercion of values to declared type when possible.
        - `allow_inf_nan=False` to disallow +/-infinity and NaN values in float and
                                decimal fields.

    - `check_restricted_fields`:
        - Model-level validator that disallows user input for restricted fields.
        - Allows defining a list of restricted fields globally or at the class level.
        - Raises a validation error if a restricted field is provided by the user.

    - `model_name`:
        - Prints the model name along with the data.
        - Useful for debugging and logging purposes(for dev).
        - This method would be further enhanced in future PR
    """

    restricted_fields: ClassVar[Tuple[str, ...]] = ()
    model_config = ConfigDict(
        # If True, trim white space around input
        str_strip_whitespace=True,
        # If True, populate data using aliased field names
        validate_by_alias=True,
        # If True, aliased field can be populated by its name as defined in the model
        validate_by_name=True,
        # If True, error locations use the alias field name when provided in input
        loc_by_alias=False,
        # If True, revalidates the model when data is modified
        # No use case in OBP-v1; planned for future releases
        validate_assignment=False,
        # If True, allow arbitrary / custom data types as field types
        # Example: PythonIdentifier
        arbitrary_types_allowed=True,
        # If True, values are not coerced; if False, values are coerced to declared
        # type when possible
        # use Field(strict=True) to enforce strict type validation on a field
        strict=False,
        # If True, allow +/-infinity and NaN values in float and decimal fields
        # use Field(allow_inf_nan=True) to allow +/-infinity and NaN values.
        # Do not enable this configuration at model level. Restrict your usage to
        # field level if required
        allow_inf_nan=False,
    )

    def __str__(self) -> str:
        """Return a pretty-print string representation of a Pydantic model.

        The returned string will be formatted as JSON with two-space indentation.

        Returns
        -------
        str
            A JSON-formatted string representation of the Pydantic model.
        """
        # Check if exclude unset removes all None attributes or just those which weren't
        # set. I.e. field = None, vs field defaults to None, and hasn't been supplied
        return self.model_dump_json(indent=2, exclude_unset=True)

    @property
    def model_name(self):
        """Return the model name for logging and end-user interactions."""
        return self.__class__.__name__

    @classmethod
    def _has_key_nested(cls, obj, key):
        """
        Recursively searches if a restricted field exists in the nested structures.

        Parameters
        ----------
        obj : dict
            Input dictionary to search.
        key : str
            The restricted field to look for.

        Returns
        -------
        bool
            True if the restricted field exists, False otherwise.
        """
        if isinstance(obj, dict):
            if key in obj:
                return True
            return any(cls._has_key_nested(v, key) for v in obj.values())
        elif isinstance(obj, list):
            return any(cls._has_key_nested(item, key) for item in obj)
        return False

    @model_validator(mode="before")
    def check_restricted_fields(cls, values):
        """
        Validate restricted fields and warn if the user tries to set them.

        Parameters
        ----------
        values: dict
            dictionary containing step details.

        Returns
        -------
        dict
            dictionary containing step details.

        Raises
        ------
        ValueError
            If a restricted field is found in the input.

        Notes
        -----
            This function was initially implemented to handle a restricted field called
            `plugin_type`, which was removed as part of of architectural changes.
            Although it is currently unused, we anticipate a strong use case moving
            forward.
        """
        for field in cls.restricted_fields:
            # if field in values and values[field] is not None:
            if cls._has_key_nested(values, field):
                raise ValueError(f"{field} can't be user-defined; set internally")
        return values


class FrozenModel(CoreBaseModel):
    """
    Inherits all of the configuration from `CoreBaseModel`.

    The following overrides are applied:
    - extra="forbid": Forbids additional fields beyond those defined in the model.
    - frozen=True: Disallows modification of field values after object instantiation.

    This model is intended for cases where additional fields are not permitted and the
    object data must remain immutable after initialization.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class PermissiveFrozenModel(CoreBaseModel):
    """
    Inherits all of the configuration from `CoreBaseModel`.

    The following overrides are applied:
    - extra="allow": Allows additional fields beyond those defined in the model.
    - frozen=True: Disallows modification of field values after object instantiation.

    This model is intended for cases where additional fields are permitted and the
    object data must remain immutable after initialization.
    """

    model_config = ConfigDict(extra="allow", frozen=True)


class DynamicModel(CoreBaseModel):
    """
    Inherits all of the configuration from `CoreBaseModel`.

    The following overrides are applied:
    - extra="forbid": Forbids additional fields beyond those defined in the model.
    - frozen=False: Allows modification of field values after object instantiation.

    This model is intended for cases where additional fields are not permitted and the
    object data remains mutable after initialization.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)


class PermissiveDynamicModel(CoreBaseModel):
    """
    Inherits all of the configuration from `CoreBaseModel`.

    The following overrides are applied:
    - extra="allow": Allows additional fields beyond those defined in the model.
    - frozen=False: Allows modification of field values after object instantiation.

    This model is intended for cases where additional fields are permitted and the
    object data remains immutable after initialization.
    """

    model_config = ConfigDict(extra="allow", frozen=False)


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


def get_interfaces(namespace) -> set[str]:
    """Return a set of distinct interfaces.

    This function returns all available plugin interfaces. The results are cached for
    runtime memory optimization.

    Returns
    -------
    set of str
        set of interfaces
    """
    if namespace == "geoips.plugin_packages":
        return {
            available_interfaces
            for ifs in interfaces.list_available_interfaces().values()
            for available_interfaces in ifs
        }
    else:
        mod = get_interface_module(namespace)
        return set(mod.__all__)
