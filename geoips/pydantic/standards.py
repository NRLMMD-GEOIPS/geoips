# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic Standard Base Model for GeoIPS."""

from pydantic import BaseModel, ConfigDict, model_validator
from typing import ClassVar


class StaticBaseModel(BaseModel):
    """Static Base Model for Pydantic validation in GeoIPS."""

    model_config = ConfigDict(
        extra="allow", str_strip_whitespace=True, populate_by_name=True
    )


class DynamicBaseModel(BaseModel):
    """Dynamic Base Model for Pydantic validation in GeoIPS."""

    model_config = ConfigDict()
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


class Model(StaticBaseModel):
    """Model specifically meant for testing StandardBaseModel."""

    x: str
    y: str


# Won't strip white space from field values that are not members of the model
# but are passed with extra=allow.
# Won't strip the whitepsace if you pass the dictionary without initializing.
# m = Model(x="hello ", y="world ")


data = {"x": " hello", "y": "world "}
model = Model(**data)
print(model.model_dump())
