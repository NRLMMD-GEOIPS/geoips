# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard xarray-based NetCDF output format."""

from geoips.interfaces.class_based.output_formatters import NetcdfOutputFormatterPlugin

import logging

LOG = logging.getLogger(__name__)


class NetcdfXarrayOutputFormatterPlugin(NetcdfOutputFormatterPlugin):
    """Netcdf Xarray Output formatter plugin class."""

    interface = "output_formatters"
    family = "xarray_data"
    name = "netcdf_xarray"

    def call(
        self,
        xarray_obj,
        product_names,
        output_fnames,
        clobber=False,
        use_compression=True,
        compression_kwargs=None,
    ):
        """Write xarray-based NetCDF outputs to disk."""
        for ncdf_fname in output_fnames:
            self.write_xarray_netcdf(
                xarray_obj,
                ncdf_fname,
                clobber=clobber,
                use_compression=use_compression,
                compression_kwargs=compression_kwargs,
            )
        return output_fnames


PLUGIN_CLASS = NetcdfXarrayOutputFormatterPlugin
