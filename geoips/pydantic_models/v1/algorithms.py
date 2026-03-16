# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS algorithm plugins."""

# cspell:ignore fcst

# Python Standard Libraries
from typing import Dict, List

# Third-Party Libraries
from pydantic import Field, StrictBool

# GeoIPS imports
from geoips.pydantic_models.v1.bases import FrozenModel


class CommonAlgorithmArgumentsModel(FrozenModel):
    """Common arguments shared by multiple algorithm plugins.

    A Pydantic model defining and validating parameters shared across model-based
    algorithm plugins such as ``model_channel`` and ``model_windbarbs``. These
    parameters control:

    * Selection of data along time or other dimensions
    * Optional scaling of output data variables
    * Processing of values outside the specified data range
    """

    variables: List[str] = Field(
        None,
        description="List of input variables used in algorithm processing, selects the "
        "first when provided.",
    )
    output_data_range: tuple[float, float] | tuple[None, None] = Field(
        [None, None],
        description="list of min and max value for wind speeds (kts or m s-1). "
        "Defaults to None, which results in using data.min and data.max.",
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
    inverse: StrictBool = Field(
        False,
        description="* Boolean flag indicating whether to inverse (True) or not (False)"
        " * If True, returned data will be inverted"
        " * If False, returned data will not be inverted",
    )
    # This should default to (?, 1000) or (1000, ?) or (None, None)
    pressure_level_range: tuple[int, int] | tuple[None, None] = Field(
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


class PressureWindsAlgorithmArgumentsModel(FrozenModel):
    """Arguments specific to Dervied Motion Wind Products."""

    var_map: Dict[str, str] = Field(
        None, description="Dictionary that maps input variables to names used in xobj"
    )


class VisIRSpecificAlgorithmArgumentsModel(FrozenModel):
    """Arguments specific to Visible and Infrared algorithm plugins."""

    gamma_list: List[float] = Field(None)
    min_night_zen: float = Field(None)
    max_night_zen: float = Field(90)
    max_day_zen: float = Field(None)
    mask_night: bool = Field(False)
    mask_day: bool = Field(False)
    scale_factor: float = Field(None)
    sun_zen_correction: bool = Field(
        False,
        description="Boolean flag indicating whether to apply solar zenith correction"
        "(True) or not (False)"
        "  * If True, returned data will have solar zenith correction applied"
        "      (see data_manipulations.corrections.apply_solar_zenith_correction)"
        "  * If False, returned data will not be modified based on solar zenith angle)",
    )
    satellite_zenith_angle_cutoff: float = Field(
        None,
        description="Cutoff for masking data where satellite zenith angle exceeds"
        "threshold. None, no masking",
    )


class ModelSpecificAlgorithmArgumentsModel(FrozenModel):
    """Common arguments shared only by model-based algorithms."""

    pressure_key: str = Field(None)
    time_key: str = Field(...)
    time_fcst: int = Field(-1)
    # verify if the type should be string
    time_dim: str = Field(None)
    grid_geo: bool = Field(False)


class AlgorithmArgumentsModel(
    CommonAlgorithmArgumentsModel,
    ModelSpecificAlgorithmArgumentsModel,
    VisIRSpecificAlgorithmArgumentsModel,
    PressureWindsAlgorithmArgumentsModel,
):
    """Algorithm step argument definition.

    Pydantic model defining and validating Reader step arguments.
    """

    pass
