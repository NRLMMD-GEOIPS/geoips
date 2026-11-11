# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS algorithm plugins."""

# cspell:ignore fcst

# Python Standard Libraries

# Third-Party Libraries
from pydantic import Field, StrictBool, StrictFloat, StrictInt

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class AlgorithmArgumentsModel(PermissiveFrozenModel):
    """Algorithm step argument definition.

    Pydantic model defining and validating Algorithm step arguments.
    """

    variables: list[str] | None = Field(
        None,
        description=(
            "List of variables to pass to the algorithm from the input data. If"
            " `None`, all variables are passed.",
        ),
    )
    output_data_range: tuple[StrictFloat, StrictFloat] | None = Field(
        None,
        description="Two-element iterator containing the minimum and maximum value "
        " for output data product. This is applied LAST after all other"
        " corrections/adjustments. If None, use data.min() and data.max()",
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
    norm: StrictBool = Field(
        None,
        description="Boolean flag indicating whether to normalize (True) or not (False)"
        "* * If True, returned data will be in the range from 0 to 1:"
        "  * If False, returned data will be in the range from min_val to max_val",
    )
    inverse: StrictBool = Field(
        None,
        description="* Boolean flag indicating whether to inverse (True) or not (False)"
        " * If True, returned data will be inverted"
        " * If False, returned data will not be inverted",
    )
    # This should default to (?, 1000) or (1000, ?) or (None, None)
    # The upper bound in 'windbarbs_dmw_low.yaml' is of type float
    pressure_level_range: tuple[float, float] | None = Field(
        None,
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
    gamma_list: list[StrictFloat] | None = Field(
        None, description="Gamma correction values to apply per channel."
    )
    min_night_zen: float | None = Field(
        None, description="Minimum solar zenith angle in degrees to classify as night."
    )
    max_night_zen: float | None = Field(
        None, description="Maximum solar zenith angle in degrees to classify as night."
    )
    max_day_zen: float | None = Field(
        None, description="Maximum solar zenith angle in degrees to classify as day."
    )
    mask_night: bool | None = Field(
        None,
        description=(
            "If True, mask pixels classified as night based on `max_day_zen` and"
            " `min_night_zen`."
        ),
    )
    mask_day: bool | None = Field(
        None,
        description=("If True, mask pixels classified as day based on `max_day_zen`."),
    )
    scale_factor: float | None = Field(
        None, description="Scalar multiplier applied to the output data."
    )
    sun_zen_correction: StrictBool | None = Field(
        None,
        description=(
            "Whether to apply a solar zenith angle correction to visible radiometric"
            " data. \n"
            "  * If True, a cosine-based solar zenith angle correction is applied."
            " (see data_manipulations.corrections.apply_solar_zenith_correction) \n"
            "  * If False, no solar zenith angle correction is applied."
        ),
    )
    satellite_zenith_angle_cutoff: float | None = Field(
        None,
        description="Cutoff for masking data where satellite zenith angle exceeds"
        "threshold. None, no masking",
    )
    pressure_key: str | None = Field(
        None,
        description="Variable name used to identify pressure levels in the dataset.",
    )
    time_key: str | None = Field(
        None,
        description="Variable name used to identify the time dimension in the dataset.",
    )
    time_fcst: StrictInt | None = Field(
        None, description="Index of the forecast time offset along the time dimension."
    )
    time_dim: StrictInt | None = Field(
        None,
        alias="Time_Dimension",
        description="Number of elements along the time dimension in the dataset.",
    )
    grid_geo: StrictBool | None = Field(
        None, description="If True, regrid data to a geographic grid before processing."
    )
    var_map: dict[str, str] | None = Field(
        {}, description="Dictionary that maps input variables to names used in xobj"
    )
