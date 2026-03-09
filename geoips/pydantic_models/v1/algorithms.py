# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS algorithm plugins."""

# Third-Party Libraries
from pydantic import Field

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
    norm: bool = Field(False)
    inverse: bool = Field(False)
