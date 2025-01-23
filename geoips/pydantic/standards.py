# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic Standard Base Model for GeoIPS."""

from pydantic import BaseModel, ConfigDict


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


class StandardBaseModel(BaseModel):
    """Standard Base Model for Pydantic validation in GeoIPS."""

    model_config = ConfigDict(extra="allow")


class Model(StandardBaseModel):
    """Model specifically meant for testing StandardBaseModel."""

    x: str


m = Model(x="hello", y="world")

print(m.model_dump())
