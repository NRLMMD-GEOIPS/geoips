# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic Standard Base Model for GeoIPS."""

from pydantic import BaseModel, ConfigDict


class StandardBaseModel(BaseModel):
    """Standard Base Model for Pydantic validation in GeoIPS."""

    model_config = ConfigDict(extra='allow')


class Model(StandardBaseModel):
    """Model specifically meant for testing StandardBaseModel."""

    x: str


m = Model(x="hello", y="world")

print(m.model_dump())
