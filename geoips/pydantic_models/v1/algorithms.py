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

    output_data_range: tuple[float, float] | tuple[None, None] = Field(
        [None, None],
        description="list of min and max value for wind speeds (kts or m s-1). "
        "Defaults to None, which results in using data.min and data.max.",
    )
    input_units: str = Field(
        None,
        description="Units of input data, for applying "
        "necessary conversions. Defaults to None, resulting in no unit conversions.",
    )
    output_units: str = Field(
        None,
        description="Units of input data, for applying "
        "necessary conversions. Defaults to None, resulting in no unit conversions.",
    )
    min_outbounds: str = Field(
        ...,
        description="Method to use when applying bounds."
        "  Valid values are: "
        " * retain: keep all pixels as is"
        " * mask: mask all pixels that are out of range"
        " * crop: set out of range values to the nearest bound (min_val or max_val)",
    )
    max_outbounds: str = Field(
        ...,
        description="Method to use when applying bounds."
        "  Valid values are: "
        " * retain: keep all pixels as is"
        " * mask: mask all pixels that are out of range"
        " * crop: set out of range values to the nearest bound (min_val or max_val)",
    )
    norm: StrictBool = Field(
        False,
        description="Boolean flag indicating whether to normalize (True) or not (False)"
        "* * If True, returned data will be in the range from 0 to 1:"
        "  * If False, returned data will be in the range from min_val to max_val",
    )
    inverse: StrictBool = Field(False)
    # This should default to (?, 1000) or (1000, ?) or (None, None)
    pressure_level_range: tuple[int, int] | tuple[None, None] = Field(
        [None, None],
        description="list of min and max pressure levels to filter derived motion wind"
        " retrievals. Defaults to None, which results in using all wind retrievals.",
    )
    pressure_key: str = Field(None)
    time_key: str = Field(...)
    time_fcst: int = Field(-1)
    # verify if the type should be string
    time_dim: str = Field(None)
    grid_geo: bool = Field(False)
    var_map: str = Field(None)
