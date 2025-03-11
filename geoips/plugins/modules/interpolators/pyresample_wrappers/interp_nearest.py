# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geoips plugin for driving pyresample Nearest Neighbor interpolation."""

import logging

import xarray

from geoips.plugins.modules.interpolators.utils.interp_pyresample import (
    interp_kd_tree,
    get_data_box_definition,
)
from geoips.data_manipulations.info import percent_unmasked
from geoips.geoips_utils import copy_standard_metadata, remove_unsupported_kwargs

LOG = logging.getLogger(__name__)

interface = "interpolators"
family = "2d"
name = "interp_nearest"


def get_final_roi(xarray_obj, area_def):
    """Get the final interpolation Radius of Influence.

    This takes the maximum of the xarray attribute, area_def pixel width,
    and area_def pixel height.
    """
    roi = None
    if "interpolation_radius_of_influence" in xarray_obj.attrs.keys():
        roi = xarray_obj.interpolation_radius_of_influence
        LOG.info("    USING XARRAY ROI of %s", roi)
    if not roi or area_def.pixel_size_x > roi:
        roi = area_def.pixel_size_x
        LOG.info("    USING AREA_DEF X ROI of %s", roi)
    if area_def.pixel_size_y > roi:
        roi = area_def.pixel_size_y
        LOG.info("    USING AREA_DEF Y ROI of %s", roi)
    return roi


def call(area_def, input_xarray, output_xarray, varlist, array_num=None, **kwargs):
    """Pyresample interp_kd_tree nearest neighbor GeoIPS plugin."""
    LOG.info(
        "Interpolating nearest using standard scifile register method: kd_tree nearest"
    )

    roi = get_final_roi(input_xarray, area_def)

    vars_to_interp = []
    if array_num is not None:
        if len(input_xarray[varlist[0]].shape) == 2:
            if len(input_xarray["latitude"].shape) == 2:
                lons = input_xarray["longitude"].to_masked_array()[:, array_num]
                lats = input_xarray["latitude"].to_masked_array()[:, array_num]
            else:
                lons = input_xarray["longitude"].to_masked_array()
                lats = input_xarray["latitude"].to_masked_array()
            for varname in varlist:
                vars_to_interp += [
                    input_xarray[varname].to_masked_array()[:, array_num]
                ]
        else:
            if len(input_xarray["latitude"].shape) == 2:
                lons = input_xarray["longitude"].to_masked_array()
                lats = input_xarray["latitude"].to_masked_array()
            else:
                lons = input_xarray["longitude"].to_masked_array()[:, :, array_num]
                lats = input_xarray["latitude"].to_masked_array()[:, :, array_num]
            for varname in varlist:
                vars_to_interp += [
                    input_xarray[varname].to_masked_array()[:, :, array_num]
                ]
    else:
        lons = input_xarray["longitude"].to_masked_array()
        lats = input_xarray["latitude"].to_masked_array()
        for varname in varlist:
            vars_to_interp += [input_xarray[varname].to_masked_array()]

    # Use standard scifile / pyresample registration
    data_box_definition = get_data_box_definition(input_xarray.source_name, lons, lats)

    kd_kwargs = remove_unsupported_kwargs(interp_kd_tree, kwargs)
    interp_data = interp_kd_tree(
        vars_to_interp,
        area_def,
        data_box_definition,
        float(roi),
        interp_type="nearest",
        **kd_kwargs,
    )

    for arr, orig, varname in zip(interp_data, vars_to_interp, varlist):
        LOG.info("%s min/max before: %s to %s", varname, orig.min(), orig.max())
        LOG.info("%s min/max after:  %s to %s", varname, arr.min(), arr.max())
        LOG.info("%s Percent unmasked before %s", varname, percent_unmasked(orig))
        LOG.info("%s Percent unmasked after  %s", varname, percent_unmasked(arr))

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
