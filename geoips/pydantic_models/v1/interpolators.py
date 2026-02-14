# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models for interpolator plugins validation."""

# Python Standard Libraries
from typing import List, TypeAlias, Union

# Third-Party Libraries
from pydantic import ConfigDict, Field
import xarray as xr

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel

dataType: TypeAlias = Union[xr.DataArray, xr.Dataset]


class CommonInterpolatorArguments(PermissiveFrozenModel):
    """Validate common Interpolator arguments."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    area_def: str = Field(..., description="Area definition identifier.")
    input_xarray: dataType = Field(..., description="Input xarray Dataset")
    output_xarray: dataType = Field(
        ..., description="Output xarray DataArray or Dataset"
    )
    varlist: List[str] = Field(
        ..., description="variables required for specific interpolation processing"
    )
    array_num: List[int] = Field(
        None, description="Column index to extract from xarray DataArray"
    )


class InterpGaussInterpolator(CommonInterpolatorArguments):
    """Validate InterpGauss Interpolator."""

    sigmaval: int = Field(
        None,
        description="Used for interp_type 'gauss' - multiplication factor for sigmas"
        " option: * sigmas = [sigmas]*len(list_of_arrays)",
    )

    drop_nan: bool = Field(
        False, description="Whether to drop the nan values (default:False)"
    )


class InterpNearestInterpolator(CommonInterpolatorArguments):
    """Validate InterpNearest Interpolator."""

    pass


class InterpGridInterpolator(CommonInterpolatorArguments):
    """Validate InterpGrid Interpolator."""

    method: str = Field(None, description="Method of interpolation; defaults to linear")
