# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard xarray-based NetCDF output format."""

from geoips.interfaces.class_based.output_formatters import BaseOutputFormatterPlugin

import logging
from datetime import datetime
import json
import numpy as np

LOG = logging.getLogger(__name__)


class NetcdfXarrayOutputFormatterPlugin(BaseOutputFormatterPlugin):
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

    def clean_attr_for_netcdf(self, xobj, attr):
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
            xobj.attrs[attr] = json.dumps(
                xobj.attrs[attr], default=self.make_json_friendly
            )
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
