# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geoips style NetCDF output format."""
import logging

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xarray_data"
name = "netcdf_geoips"


def call(
    xarray_obj,
    product_names,
    output_fnames,
    clobber=False,
    use_compression=True,
    compression_kwargs=None,
):
    """Write GeoIPS style NetCDF to disk."""
    import xarray

    prod_xarray = xarray.Dataset()

    from geoips.geoips_utils import copy_standard_metadata

    copy_standard_metadata(xarray_obj, prod_xarray)
    for product_name in product_names:
        prod_xarray[product_name] = xarray_obj[product_name]

    from geoips.plugins.modules.output_formatters.netcdf_xarray import (
        write_xarray_netcdf,
    )

    for ncdf_fname in output_fnames:
        write_xarray_netcdf(
            prod_xarray,
            ncdf_fname,
            clobber=clobber,
            use_compression=use_compression,
            compression_kwargs=compression_kwargs,
        )
    return output_fnames
