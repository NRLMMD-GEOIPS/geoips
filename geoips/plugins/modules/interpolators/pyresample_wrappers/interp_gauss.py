# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geoips plugin for driving pyresample Gaussian interpolation."""

import logging

import xarray

from geoips.plugins.modules.interpolators.utils.interp_pyresample import (
    interp_kd_tree,
    get_data_box_definition,
)
from geoips.geoips_utils import copy_standard_metadata, remove_unsupported_kwargs

LOG = logging.getLogger(__name__)

interface = "interpolators"
family = "2d"
name = "interp_gauss"


def call(
    area_def,
    input_xarray,
    output_xarray,
    varlist,
    array_num=None,
    sigmaval=None,
    drop_nan=False,
    **kwargs,
):
    """Pyresample interp_kd_tree gaussian interpolation GeoIPS plugin."""
    LOG.info(
        "Interpolating using standard scifile register method: "
        "kd_tree gauss sigmaval %s",
        sigmaval,
    )

    goodinds = None

    vars_to_interp = []
    if array_num is not None:
        lons = input_xarray["longitude"][:, :, array_num]
        lats = input_xarray["latitude"][:, :, array_num]
        if drop_nan is True:
            # Make sure we get any bad lat/lon values
            goodinds = ~input_xarray["latitude"][:, :, array_num].isnull()
            goodinds = ~input_xarray["longitude"][:, :, array_num].isnull() & goodinds
        for varname in varlist:
            if drop_nan is True:
                # Cumulative mask over all channels. What could go wrong?
                goodinds = ~input_xarray[varname][:, :, array_num].isnull() & goodinds
                vars_to_interp += [input_xarray[varname][:, :, array_num]]
            else:
                vars_to_interp += [
                    input_xarray[varname].to_masked_array()[:, :, array_num]
                ]
    else:
        lons = input_xarray["longitude"]
        lats = input_xarray["latitude"]
        if drop_nan is True:
            # Make sure we get any bad lat/lon values
            goodinds = ~input_xarray["latitude"].isnull()
            goodinds = ~input_xarray["longitude"].isnull() & goodinds
        for varname in varlist:
            if drop_nan is True:
                # Cumulative mask over all channels. What could go wrong?
                goodinds = ~input_xarray[varname].isnull() & goodinds
                vars_to_interp += [input_xarray[varname]]
            else:
                vars_to_interp += [input_xarray[varname].to_masked_array()]

    if drop_nan is True:
        final_vars_to_interp = []
        lats = lats.where(goodinds, drop=True)
        lons = lons.where(goodinds, drop=True)
        for var in vars_to_interp:
            final_vars_to_interp += [var.where(goodinds, drop=True).to_masked_array()]
        vars_to_interp = final_vars_to_interp
    lats = lats.to_masked_array()
    lons = lons.to_masked_array()
    # Use standard scifile / pyresample registration
    data_box_definition = get_data_box_definition(input_xarray.source_name, lons, lats)

    # Set s default value of igmaval as 10000

    if sigmaval is None:
        sigmaval = 10000

    kd_kwargs = remove_unsupported_kwargs(interp_kd_tree, kwargs)
    interp_data = interp_kd_tree(
        vars_to_interp,
        area_def,
        data_box_definition,
        input_xarray.interpolation_radius_of_influence,
        interp_type="gauss",
        sigmas=sigmaval,
        **kd_kwargs,
    )
    if output_xarray is None:
        output_xarray = xarray.Dataset()
    if "latitude" not in output_xarray.variables.keys():
        interp_lons, interp_lats = area_def.get_lonlats()
        output_xarray["latitude"] = xarray.DataArray(interp_lats)
        output_xarray["longitude"] = xarray.DataArray(interp_lons)
    copy_standard_metadata(input_xarray, output_xarray, force=False)
    output_xarray.attrs["registered_dataset"] = True
    output_xarray.attrs["area_definition"] = area_def

    for ind in range(len(varlist)):
        output_xarray[varlist[ind]] = xarray.DataArray(interp_data[ind])

    return output_xarray
