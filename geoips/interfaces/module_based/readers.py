# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers interface module."""

from geoips.interfaces.base import BaseModuleInterface


class ReadersInterface(BaseModuleInterface):
    """Interface for ingesting a specific data type.

    Provides specification for ingensting a specific data type, and storing in
    the GeoIPS xarray-based internal format.
    """

    name = "readers"
    required_args = {"standard": ["fnames"]}
    required_kwargs = {
        "standard": ["metadata_only", "chans", "area_def", "self_register"]
    }
    allowable_kwargs = {"standard": ["mask_sat_zen_greater"]}


readers = ReadersInterface()
