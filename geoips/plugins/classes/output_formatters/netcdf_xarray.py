# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard xarray-based NetCDF output format."""

from geoips.interfaces.class_based.output_formatters import NetcdfOutputFormatterPlugin

import logging
from datetime import datetime
import json
import numpy as np

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

    def make_json_friendly(self, value):
        """Return a JSON-serializable version of `value`."""
        # Handle NumPy scalars
        if isinstance(value, np.generic):
            return value.item()  # convert np.int32 -> int, np.float64 -> float, etc.

        # Handle common non-serializable types
        if isinstance(value, (dict, list, tuple)):
            # Recursively make contents JSON-friendly
            return json.loads(json.dumps(value, default=self.make_json_friendly))
        if isinstance(value, datetime):
            return value.isoformat()

        # Simple types that JSON already understands
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value

        # Fallback: string representation
        return str(value)


PLUGIN_CLASS = NetcdfXarrayOutputFormatterPlugin
