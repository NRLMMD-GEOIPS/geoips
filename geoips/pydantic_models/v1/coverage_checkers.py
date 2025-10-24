# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 coverage-checker plugins."""

# Third-Party Libraries
from pydantic import Field
import xarray
from typing import Optional

# GeoIPS imports
from geoips.pydantic_models.v1 import PermissiveFrozenModel


class CoverageCheckerPluginModel(PermissiveFrozenModel):
    """Coverage-Checker step argument definition.

    Pydantic model defining and validating Coverage Checker step arguments.
    """

    xarray_obj: xarray.Dataset = Field(
        ..., description="xarray object containing variable 'variable_name'"
    )
    variable_name: str = Field(
        ..., description="Variable name to check percent unmasked."
    )
    area_def: str = Field(None, description="Area definition identifier.")
    radius_km: Optional[float] = Field(
        300, description="Radius of center disk to check for coverage."
    )
