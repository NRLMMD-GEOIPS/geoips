# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Full NetCDF output format, writing out all channels in full dataset."""

from geoips.interfaces.class_based.output_formatters import NetcdfOutputFormatterPlugin

import logging

LOG = logging.getLogger(__name__)


class NetcdfFullOutputFormatterPlugin(NetcdfOutputFormatterPlugin):
    """Netcdf Full Output formatter plugin class."""

    interface = "output_formatters"
    family = "xarray_data"
    name = "netcdf_full"

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
        for ncdf_fname in output_fnames:
            self.write_xarray_netcdf(
                xarray_obj,
                ncdf_fname,
                clobber=clobber,
                use_compression=use_compression,
                compression_kwargs=compression_kwargs,
            )
        return output_fnames


PLUGIN_CLASS = NetcdfFullOutputFormatterPlugin
