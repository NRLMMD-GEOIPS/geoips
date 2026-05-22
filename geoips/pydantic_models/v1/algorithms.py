# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS algorithm plugins."""

# cspell:ignore fcst

# Python Standard Libraries
from typing import Dict, List, Optional

# Third-Party Libraries
from pydantic import Field, StrictBool, StrictFloat, StrictInt

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class AlgorithmArgumentsModel(PermissiveFrozenModel):
    """Algorithm step argument definition.

    Pydantic model defining and validating Algorithm step arguments.
    """

    variables: Optional[List[str]] = Field(
        [None],
        description="List of input variables used in algorithm processing",
    )
    output_data_range: tuple[StrictFloat, StrictFloat] | tuple[None, None] = Field(
        [None, None],
        description="list of min and max value for output data product."
        " This is applied LAST after all other corrections/adjustments."
        " If None, use data.min() and data.max()",
    )
    min_outbounds: str | None = Field(
        None,
        description="Method to use when applying minimum value of"
        "'output_data_range', if specified."
        "  Valid values are: "
        " * retain: keep all pixels as is"
        " * mask: mask all pixels that are out of range"
        " * crop: set out of range values to the nearest bound (min_val or max_val)",
    )
    max_outbounds: str | None = Field(
        None,
        description="Method to use when applying maximum value of"
        "'output_data_range', if specified."
        "  Valid values are: "
        " * retain: keep all pixels as is"
        " * mask: mask all pixels that are out of range"
        " * crop: set out of range values to the nearest bound (min_val or max_val)",
    )
    norm: StrictBool | None = Field(
        None,
        description="Boolean flag indicating whether to normalize (True) or not (False)"
        "* * If True, returned data will be in the range from 0 to 1:"
        "  * If False, returned data will be in the range from min_val to max_val",
    )
    inverse: StrictBool | None = Field(
        None,
        description="* Boolean flag indicating whether to inverse (True) or not (False)"
        " * If True, returned data will be inverted"
        " * If False, returned data will not be inverted",
    )
    # This should default to (?, 1000) or (1000, ?) or (None, None)
    # The upper bound in 'windbarbs_dmw_low.yaml' is of type float
    pressure_level_range: tuple[float, float] | tuple[None, None] = Field(
        [None, None],
        description="list of min and max pressure levels to filter derived motion wind"
        " retrievals. Defaults to None, which results in using all wind retrievals.",
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
    gamma_list: Optional[List[StrictFloat]] = Field([])
    min_night_zen: Optional[float] = Field(None)
    max_night_zen: StrictFloat = Field(90)
    max_day_zen: Optional[float] = Field(None)
    mask_night: bool = Field(False)
    mask_day: bool = Field(False)
    scale_factor: Optional[float] = Field(None)
    sun_zen_correction: StrictBool = Field(
        False,
        description="Boolean flag indicating whether to apply solar zenith correction"
        "(True) or not (False)"
        "  * If True, returned data will have solar zenith correction applied"
        "      (see data_manipulations.corrections.apply_solar_zenith_correction)"
        "  * If False, returned data will not be modified based on solar zenith angle)",
    )
    satellite_zenith_angle_cutoff: Optional[float] = Field(
        None,
        description="Cutoff for masking data where satellite zenith angle exceeds"
        "threshold. None, no masking",
    )
    pressure_key: str | None = Field(None)
    time_key: str = Field(None)
    time_fcst: StrictInt = Field(-1)
    time_dim: StrictInt | None = Field(None, alias="Time_Dimension")
    grid_geo: StrictBool = Field(False)
    var_map: Optional[Dict[str, str]] = Field(
        {}, description="Dictionary that maps input variables to names used in xobj"
    )
