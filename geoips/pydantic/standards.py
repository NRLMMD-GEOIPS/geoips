# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic Standard Base Model for GeoIPS."""

from pydantic import BaseModel, ConfigDict


class StaticBaseModel(BaseModel):
    """Static Base Model for Pydantic validation in GeoIPS."""

    model_config = ConfigDict(
        extra="allow", str_strip_whitespace=True, populate_by_name=True
    )


class DynamicBaseModel(BaseModel):
    """Dynamic Base Model for Pydantic validation in GeoIPS."""

    model_config = ConfigDict()


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
