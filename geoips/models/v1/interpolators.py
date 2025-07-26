# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models for interpolator plugins validation."""

# Python Standard Libraries
from typing import List, TypeAlias, Union

# Third-Party Libraries
from pydantic import ConfigDict, Field
import xarray as xr

# GeoIPS imports
from geoips.models.v1.bases import PermissiveFrozenModel

dataType: TypeAlias = Union[xr.DataArray, xr.Dataset]

# Question: Only after discussing all of the code in this file
# Should we unset extra=allow for the common class and set it to
# allow for the children class


class CommonInterpolatorArguments(PermissiveFrozenModel):
    """Validate common Interpolator arguments."""

    # Move this to base model if used across multiple models
    # This is needed for xarray based custom data types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    area_def: str = Field(..., description="Area definition identifier.")
    input_xarray: dataType = Field(..., description="Input xarray Dataset")
    # should be optional and default to empty xarray dataset
    # in call: they should be keyword args
    output_xarray: dataType = Field(
        ..., description="Output xarray DataArray or Dataset"
    )
    # None, it should be interpolate everything / all columns
    # in call: they should be keyword args
    # Keep the postiional args in the spefici order as tehy are now for backward compatability 
    varlist: List[str] = Field(
        ..., description="variables required for specific interpolation processing"
    )
    # verify the description
    # verify the datatype (integer or list of integers)
    # I'm inclined towards just an integer based on the code
    array_num: List[int] = Field(
        None, description="Column index to extract from xarray DataArray"
    )


class InterpGaussInterpolator(CommonInterpolatorArguments):
    """Validate InterpGauss Interpolator."""

    # Note the pyresample sigma is not the standard deviation of the gaussian.
    # explore more and discuss with Jeremy
    sigmaval: int = Field(
        None,
        description="Used for interp_type 'gauss' - multiplication factor for sigmas option: * sigmas = [sigmas]*len(list_of_arrays)",
    )

    # We can avoid this and make it a default condition
    # Verify if we can set this to all of the interpolators or not
    # if drop_nan is set to False across all of them; remove this attribute
    drop_nan: bool = Field(
        False, description="Whether to drop the nan values (default:False)"
    )


class InterpNearestInterpolator(CommonInterpolatorArguments):
    """Validate InterpNearest Interpolator."""

    pass


class InterpGridInterpolator(CommonInterpolatorArguments):
    """Validate InterpGrid Interpolator."""

    method: str = Field(None, description="Method of interpolation; defaults to linear")
