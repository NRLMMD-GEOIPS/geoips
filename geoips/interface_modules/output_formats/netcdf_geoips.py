# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Geoips style NetCDF output format."""
import logging

LOG = logging.getLogger(__name__)

output_type = "xarray_data"


def netcdf_geoips(xarray_obj, product_names, output_fnames):
    """Write GeoIPS style NetCDF to disk."""
    import xarray

    prod_xarray = xarray.Dataset()

    from geoips.dev.utils import copy_standard_metadata

    copy_standard_metadata(xarray_obj, prod_xarray)
    for product_name in product_names:
        prod_xarray[product_name] = xarray_obj[product_name]

    from geoips.interface_modules.output_formats.netcdf_xarray import (
        write_xarray_netcdf,
    )

    for ncdf_fname in output_fnames:
        write_xarray_netcdf(prod_xarray, ncdf_fname)
    return output_fnames
