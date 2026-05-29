# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geoips style NetCDF output format."""

from geoips.interfaces.class_based.output_formatters import BaseOutputFormatterPlugin

import logging

LOG = logging.getLogger(__name__)


class NetcdfGeoipOutputFormatterPlugin(BaseOutputFormatterPlugin):
    """Netcdf Geoip Output formatter plugin class."""

    interface = "output_formatters"
    family = "xarray_data"
    name = "netcdf_geoips"

    def call(
        self,
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

        for ncdf_fname in output_fnames:
            self.write_xarray_netcdf(
                prod_xarray,
                ncdf_fname,
                clobber=clobber,
                use_compression=use_compression,
                compression_kwargs=compression_kwargs,
            )
        return output_fnames


PLUGIN_CLASS = NetcdfGeoipOutputFormatterPlugin
