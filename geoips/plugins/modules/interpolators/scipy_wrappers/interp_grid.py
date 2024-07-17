# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geoips plugin for driving scipy griddata interpolation."""

import logging

import xarray

from geoips.geoips_utils import copy_standard_metadata
from geoips.plugins.modules.interpolators.utils.interp_scipy import interp_griddata

LOG = logging.getLogger(__name__)

interface = "interpolators"
family = "grid"
name = "interp_grid"


def call(area_def, input_xarray, output_xarray, varlist, array_num=None, method=None):
    """Scipy griddata interpolation GeoIPS plugin."""
    LOG.info("Interpolating using scipy.interpolate.griddata %s", method)

    interp_datas = []
    for varname in varlist:
        if array_num is not None:
            lons = input_xarray["longitude"].to_masked_array()[:, :, array_num]
            lats = input_xarray["latitude"].to_masked_array()[:, :, array_num]
            var_to_interp = input_xarray[varname].to_masked_array()[:, :, array_num]
        else:
            lons = input_xarray["longitude"].to_masked_array()
            lats = input_xarray["latitude"].to_masked_array()
            var_to_interp = input_xarray[varname].to_masked_array()

        min_gridlon = area_def.area_extent_ll[0]
        max_gridlon = area_def.area_extent_ll[2]
        min_gridlat = area_def.area_extent_ll[1]
        max_gridlat = area_def.area_extent_ll[3]
        numx_grid = area_def.width
        numy_grid = area_def.height

        interp_datas += [
            interp_griddata(
                var_to_interp,
                lons,
                lats,
                min_gridlon,
                max_gridlon,
                min_gridlat,
                max_gridlat,
                numx_grid,
                numy_grid,
                method,
            )
        ]

    if output_xarray is None:
        output_xarray = xarray.Dataset()
    if "latitude" not in output_xarray.variables.keys():
        interp_lons, interp_lats = area_def.get_lonlats()
        output_xarray["latitude"] = xarray.DataArray(interp_lats)
        output_xarray["longitude"] = xarray.DataArray(interp_lons)
    copy_standard_metadata(input_xarray, output_xarray)
    output_xarray.attrs["registered_dataset"] = True
    output_xarray.attrs["area_definition"] = area_def

    for ind in range(len(varlist)):
        output_xarray[varlist[ind]] = xarray.DataArray(interp_datas[ind])

    return output_xarray
