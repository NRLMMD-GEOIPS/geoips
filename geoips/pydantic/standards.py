# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic Standard Base Model for GeoIPS."""

# Python Standard Libraries
import keyword
import logging

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.functional_validators import AfterValidator
from typing import ClassVar
from typing_extensions import Annotated


logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


class CoreBaseModel(BaseModel):
    """Make Pydantic models pretty-print by default.

    This model overrides the default string representation of Pydantic models to
    generate a user-friendly, JSON-formatted output with two-space indentation.
    """
    model_config = ConfigDict(str_strip_whitespace=True, loc_by_alias=False)
    # model_config = ConfigDict(
    #     extra="allow", populate_by_name=True, str_strip_whitespace=True,
    #     loc_by_alias=True
    # )

    def __str__(self) -> str:
        """Return a pretty-print string representation of a Pydantic model.

        The returned string will be formatted as JSON with two-space indentation.

        Returns
        -------
        str
            A JSON-formatted string representation of the Pydantic model.
        """
        return self.model_dump_json(indent=2, by_alias=False)
        # return self.model_dump_json(indent=2, by_alias=False)


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
        # LOG.interactive(error_message, exc_info=True)
        LOG.info(error_message, exc_info=True)
        raise ValueError(error_message)

    return val


# Create the PythonIdentifier type
PythonIdentifier = Annotated[str, AfterValidator(python_identifier)]


class StaticBaseModel(CoreBaseModel):
    """
    Pydantic model with a customized ``ConfigDict`` configurations for GeoIPS.

    This model extends ``CoreBaseModel`` and uses Pydantic ConfigDict to provide
    customized configurations such as forbidding extra fields.

    # Attributes
    # ----------
    # model_config : ConfigDict
    #     Configuration for the Pydantic model:
    #     - `extra="forbid"`: Does not allow any additional fields in the input data.
    #     - `populate_by_name=True`: Enables populating fields by their aliases.
    """

    model_config = ConfigDict(
        extra="allow", populate_by_name=True, loc_by_alias=True
    )

    # sets the model name as the title
    @property
    def model_title(self):
        return self.__class__.__name__

    has_disallowed_fields: ClassVar[bool] = False  # Default: no disallowed fields
    #  has_disallowed_fields = True
    #  set this in the inherited models, preferably before field definitions
    #  when you would like to call check_internal_fields

    @classmethod
    def _has_key_nested(cls, obj, key):
        """
        Recursively searches if an internal field exists in the input dictionary.

        Parameters
        ----------
        obj : dict
            Input dictionary to search.
        key : str
            The internal field to look for.

        Returns
        -------
        bool
            True if the internal field exists, False otherwise.
        """
        if isinstance(obj, dict):
            if key in obj:
                return True
            return any(cls._has_key_nested(v, key) for v in obj.values())
        elif isinstance(obj, list):
            return any(cls._has_key_nested(item, key) for item in obj)
        return False

    @model_validator(mode="before")
    def check_internal_fields(cls, values):
        """
        Validate internal fields and warn if the user tries to set them.

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
            If a disallowed field is found in the input.
        """
        disallowed_fields = cls.get_disallowed_fields()
        for field in disallowed_fields:
            # if field in values and values[field] is not None:
            if cls._has_key_nested(values, field):
                raise ValueError(f"{field} can't be user-defined; set internally")
        return values

    @classmethod
    def get_disallowed_fields(cls):
        """
        Return a list of fields restricted from user user input.

        Submodels should override this method to specify fields where user input
        is restricted. By default, it returns an empty list, indicating no fields are
        restricted.

        Returns
        -------
        list
            A list of field names (strings)

        """
        return []


class Instrument(StaticBaseModel):
    """Model for validating instrument information."""

    sensor: str = Field(
        ...,
        min_length=1,
        max_length=25,
        pattern="^[A-Za-z0-9 _-]+$",
        description="sensor_name",
    )
    spacecraft: str = Field(
        default="GOES-R", description="The spacecraft associated with the instrument."
    )
    status: PythonIdentifier = Field(
        ..., pattern="^(Active|Inactive|Testing|Decommissioned)$"
    )


product = Instrument(
    sensor="Advanced Baseline Imagery", spacecraft="GOES-R  ", status="Active"
)

print(product.model_title)
print(product.model_dump_json(indent=2))

# print("Including only 'sensor' attribute using 'include' argument:")
# print(ABI.model_dump_json(indent=2, include={"sensor"}))

# print("Excluding 'sensor' attribute using 'exclude' argument")
# print(ABI.model_dump_json(indent=2, exclude={"sensor"}))


# class Instrument(StaticBaseModel):
#     """Validate Instrument informaton."""

#     name: str
#     spacecraft: str


# ABI = Instrument(name="Advanced Baseline Imager", y="GOES-R")
# print(ABI.model_dump())
