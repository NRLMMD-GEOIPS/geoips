# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard xarray-based NetCDF output format."""

import logging

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xarray_data"
name = "netcdf_xarray"


def call(xarray_obj, product_names, output_fnames, clobber=False):
    """Write xarray-based NetCDF outputs to disk."""
    for ncdf_fname in output_fnames:
        write_xarray_netcdf(xarray_obj, ncdf_fname)
    return output_fnames


def write_xarray_netcdf(xarray_obj, ncdf_fname, clobber=False):
    """Write out xarray_obj to netcdf file named ncdf_fname."""

    def check_attr(xobj, attr):
        """Check xarray attributes."""
        if isinstance(xobj.attrs[attr], datetime):
            xobj.attrs[attr] = xobj.attrs[attr].strftime("%c")
        if xobj.attrs[attr] is None:
            xobj.attrs[attr] = str(xobj.attrs[attr])
        if isinstance(xobj.attrs[attr], bool):
            xobj.attrs[attr] = str(xobj.attrs[attr])
        # DO NOT attempt to store dicts - they are not supported
        if isinstance(xobj.attrs[attr], dict):
            LOG.warning(
                "SKIPPING attr %s %s, dictionaries not supported for netcdf output",
                attr,
                xobj.attrs[attr],
            )
            xobj.attrs.pop(attr)

    from geoips.filenames.base_paths import make_dirs
    from os.path import dirname

    make_dirs(dirname(ncdf_fname))

    orig_attrs = xarray_obj.attrs.copy()
    orig_var_attrs = {}

    from datetime import datetime

    for attr in xarray_obj.attrs.copy().keys():
        check_attr(xarray_obj, attr)
    for varname in xarray_obj.variables.keys():
        orig_var_attrs[varname] = xarray_obj[varname].attrs.copy()
        for attr in xarray_obj[varname].attrs.keys():
            check_attr(xarray_obj[varname], attr)

    roi_str = "none"
    if "interpolation_radius_of_influence" in xarray_obj.attrs.keys():
        roi_str = xarray_obj.interpolation_radius_of_influence

    sdt_str = "none"
    if "start_datetime" in xarray_obj.attrs.keys():
        sdt_str = xarray_obj.attrs["start_datetime"]

    edt_str = "none"
    if "end_datetime" in xarray_obj.attrs.keys():
        edt_str = xarray_obj.attrs["end_datetime"]

    dp_str = "none"
    if "data_provider" in xarray_obj.attrs.keys():
        dp_str = xarray_obj.attrs["data_provider"]

    area_def_str = "none"
    # GEOIPS 1 COMPATIBILITY
    if "area_def" in xarray_obj.attrs.keys():
        # Must pop off the actual area_defintion - does not write to xarray properly
        area_def = xarray_obj.attrs.pop("area_def")
        area_def_str = repr(area_def)
        xarray_obj.attrs["area_def_str"] = area_def_str
    # If actual area_definition object, write it out to xarray as str
    elif "area_definition" in xarray_obj.attrs.keys():
        # If area_definition_str was explicitly defined on the area_definition
        # object, use that
        if hasattr(xarray_obj.area_definition, "area_definition_str"):
            # Must pop off the actual area_defintion - does not write to xarray properly
            area_def_str = xarray_obj.area_definition.area_definition_str
            area_def = xarray_obj.attrs.pop("area_definition")
            xarray_obj.attrs["area_definition_str"] = area_def_str
        else:
            # Must pop off the actual area_defintion - does not write to xarray properly
            area_def = xarray_obj.attrs.pop("area_definition")
            area_def_str = repr(area_def)
            xarray_obj.attrs["area_definition_str"] = area_def_str

    LOG.info(
        "Writing xarray obj to file %s, source %s, platform %s, start_dt %s, end_dt %s,"
        " %s %s, %s %s, %s %s",
        ncdf_fname,
        xarray_obj.source_name,
        xarray_obj.platform_name,
        sdt_str,
        edt_str,
        "provider",
        dp_str,
        "roi",
        roi_str,
        "area_def",
        area_def_str,
    )

    from os.path import exists

    if clobber is True or not exists(ncdf_fname):
        xarray_obj.to_netcdf(ncdf_fname)
    else:
        LOG.warning("SKIPPING not outputing file %s, exists", ncdf_fname)
    xarray_obj.attrs = orig_attrs
    for varname in xarray_obj.variables.keys():
        xarray_obj[varname].attrs = orig_var_attrs[varname]

    return [ncdf_fname]
