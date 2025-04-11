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
name = "interp_ndim"


def call(area_def, input_xarray, output_xarray, varlist, method="nearest"):
    """Xarray interpolation, default as nearest, GeoIPS plugin."""
    LOG.info(
        "Interpolating using xarray.DataArray.interp with method {}".format(method)
    )

    min_gridlon = area_def.area_extent_ll[0]
    max_gridlon = area_def.area_extent_ll[2]
    min_gridlat = area_def.area_extent_ll[1]
    max_gridlat = area_def.area_extent_ll[3]
    numx_grid = area_def.width
    numy_grid = area_def.height
    # create grid
    if min_gridlon > 0 and max_gridlon < 0:
        input_xarray.update(
            {
                "longitude": xarray.where(
                    input_xarray.longitude > 0,
                    input_xarray.longitude,
                    input_xarray.longitude + 360,
                )
            }
        )
        max_gridlon = 360 + max_gridlon

    xx = np.linspace(min_gridlon,max_gridlon,int(numx_grid))
    yy = np.linspace(max_gridlat,min_gridlat,int(numy_grid))
    output_xarray = input_xarray.interp(latitude=yy,longitude=xx,method='nearest')
    
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
