# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard xarray-based NetCDF output format."""

import logging
from datetime import datetime
import json
import numpy as np

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xarray_data"
name = "netcdf_xarray"


def call(
    xarray_obj,
    product_names,
    output_fnames,
    clobber=False,
    use_compression=True,
    compression_kwargs=None,
):
    """Write xarray-based NetCDF outputs to disk."""
    for ncdf_fname in output_fnames:
        write_xarray_netcdf(
            xarray_obj,
            ncdf_fname,
            clobber=clobber,
            use_compression=use_compression,
            compression_kwargs=compression_kwargs,
        )
    return output_fnames


def clean_attr_for_netcdf(xobj, attr):
    """Check xarray attributes."""
    # datetime
    if isinstance(xobj.attrs[attr], datetime):
        xobj.attrs[attr] = xobj.attrs[attr].strftime("%c")
    # None cast as string.
    elif xobj.attrs[attr] is None:
        xobj.attrs[attr] = str(xobj.attrs[attr])
    # bools cast as string.
    elif isinstance(xobj.attrs[attr], bool):
        xobj.attrs[attr] = str(xobj.attrs[attr])
    # use json.dumps for dict, list, and tuples.
    elif isinstance(xobj.attrs[attr], (dict, list, tuple)):
        xobj.attrs[attr] = json.dumps(xobj.attrs[attr], default=make_json_friendly)
    # str, bytes, int, float are natively handled
    elif isinstance(xobj.attrs[attr], (str, bytes, int, float)):
        xobj.attrs[attr] = xobj.attrs[attr]
    # other non-native types can just be cast to string.
    # We may want to remove this case, if we want to explicitly handle non-supported
    # types, for easier conversion when reading back in.
    elif not isinstance(xobj.attrs[attr], (str, bytes, int, float)):
        xobj.attrs[attr] = str(xobj.attrs[attr])
    else:
        LOG.warning(
            "SKIPPING attr %s %s, unsupported type %s",
            attr,
            xobj.attrs[attr],
            type(attr),
        )
        xobj.attrs.pop(attr)


def make_json_friendly(value):
    """Return a JSON-serializable version of `value`."""
    # Handle NumPy scalars
    if isinstance(value, np.generic):
        return value.item()  # convert np.int32 -> int, np.float64 -> float, etc.

    # Handle common non-serializable types
    if isinstance(value, (dict, list, tuple)):
        # Recursively make contents JSON-friendly
        return json.loads(json.dumps(value, default=make_json_friendly))
    if isinstance(value, datetime):
        return value.isoformat()

    # Simple types that JSON already understands
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    # Fallback: string representation
    return str(value)


def write_xarray_netcdf(
    xarray_obj,
    ncdf_fname,
    clobber=False,
    use_compression=True,
    compression_kwargs=None,
):
    """Write out xarray_obj to netcdf file named ncdf_fname."""
    from geoips.filenames.base_paths import make_dirs
    from os.path import dirname

    make_dirs(dirname(ncdf_fname))

    orig_attrs = xarray_obj.attrs.copy()
    orig_var_attrs = {}

    # Specially handled attributes.
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

    # Standard attribute cleaning for proper serialization for xarray.to_netcdf.
    for attr in xarray_obj.attrs.copy().keys():
        clean_attr_for_netcdf(xarray_obj, attr)
    for varname in xarray_obj.variables.keys():
        orig_var_attrs[varname] = xarray_obj[varname].attrs.copy()
        for attr in xarray_obj[varname].attrs.keys():
            clean_attr_for_netcdf(xarray_obj[varname], attr)

    # Strings to print to the log statement, not used in any other way.
    # If an attribute is not defined, print 'none'.
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

    if use_compression:
        if compression_kwargs is None:
            compression_kwargs = {"zlib": True, "complevel": 5}
        encoding = {x: compression_kwargs for x in list(xarray_obj)}
    else:
        encoding = {}

    # Only re-write the file if requested.
    if clobber is True or not exists(ncdf_fname):
        xarray_obj.to_netcdf(ncdf_fname, encoding=encoding)
    else:
        LOG.warning("SKIPPING not outputing file %s, exists", ncdf_fname)

    # Put the original attributes back at both the dataset level and the variable
    # level. We do not want the serializable attributes on the original dataset.
    xarray_obj.attrs = orig_attrs
    for varname in xarray_obj.variables.keys():
        xarray_obj[varname].attrs = orig_var_attrs[varname]

    return [ncdf_fname]
