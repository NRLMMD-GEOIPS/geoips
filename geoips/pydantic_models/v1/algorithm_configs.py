# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS feature annotator plugins."""

from pydantic import Field
from typing import List, Literal, Optional

from geoips.pydantic_models.v1.bases import (
    FrozenModel,
    PluginModel,
)


class RgbGunRecipe(FrozenModel):
    """Specification for a gun of one of the r / g / b components in a rgb recipe."""

    equation: str = Field(
        ...,
        description="The equation for a gun of an rgb recipe.",
    )
    data_range: List[float] = Field(
        ..., description="The data range for a given rgb gun."
    )
    gamma: float = Field(..., description="The gamma value for a rgb gun.")
    input_units: Optional[Literal["kelvin", "celsius", "kts", "m s-1"]] = Field(
        "kelvin",
        description="The input units of the data for the rgb gun.",
    )
    output_units: Optional[Literal["kelvin", "celsius", "kts", "m s-1"]] = Field(
        "kelvin",
        description="The input units of the data for the rgb gun.",
    )


class AlgorithmConfigSpec(FrozenModel):
    """Feature Annotator spec (specification) format."""

    red: RgbGunRecipe = Field(
        ..., description="Specification for the red gun of the rgb recipe."
    )
    green: RgbGunRecipe = Field(
        ..., description="Specification for the green gun of the rgb recipe."
    )
    blue: RgbGunRecipe = Field(
        ..., description="Specification for the blue gun of the rgb recipe."
    )


class AlgorithmConfigPluginModel(PluginModel):
    """Feature Annotator plugin format."""

    spec: AlgorithmConfigSpec = Field(
        ...,
        description=("Specification for algorithm config plugins."),
    )
