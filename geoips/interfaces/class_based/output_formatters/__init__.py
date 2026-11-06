# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters interface classes."""

from geoips.interfaces.class_based.output_formatters.base import (
    BaseOutputFormatterPlugin,
    OutputFormattersInterface,
    output_formatters,
    DATA_PARAM_NAMES,
    _is_area_definition,
    _call_with_original_order,
    _normalize_output_formatter_call_signature,
)
from geoips.interfaces.class_based.output_formatters.netcdf import (
    NetcdfOutputFormatterPlugin,
)
from geoips.interfaces.class_based.output_formatters.windbarb import (
    WindbarbOutputFormatterPlugin,
)

__all__ = [
    "BaseOutputFormatterPlugin",
    "NetcdfOutputFormatterPlugin",
    "OutputFormattersInterface",
    "WindbarbOutputFormatterPlugin",
    "output_formatters",
    "DATA_PARAM_NAMES",
    "_is_area_definition",
    "_call_with_original_order",
    "_normalize_output_formatter_call_signature",
]
