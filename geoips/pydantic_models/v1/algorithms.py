# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS algorithm plugins."""

# Third-Party Libraries
from pydantic import Field, StrictBool

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class AlgorithmArgumentsModel(PermissiveFrozenModel):
    """Algorithm step argument step definition.

    Pydantic model defining and validating Algorithm step arguments.
    """

    output_data_range: tuple[float, float] = Field(None)
    input_units: str = Field(None)
    output_units: str = Field(None)
    min_outbounds: str = Field("crop")
    max_outbounds: str = Field("mask")
    norm: StrictBool = Field(False)
    inverse: StrictBool = Field(False)
    # This should default to (?, 1000) or (1000, ?) or (None, None)
    pressure_level_range: int = Field()
    pressure_key: str = Field(None)
    time_key: str = Field(...)
    time_fcst: int = Field(-1)
    # verify if the type should be string
    time_dim: str = Field(None)
    grid_geo: bool = Field(False)
    var_map: str = Field(None)
