# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters base interface class."""


import xarray as xr

import logging


LOG = logging.getLogger(__name__)

DATA_PARAM_NAMES = ("xarray_obj", "xarray_dict")

def _is_area_definition(obj):
    """Return True if *obj* looks like a pyresample Geometry (duck-typed).

    Avoids a mandatory ``pyresample`` import while still reliably detecting
    ``AreaDefinition`` / ``SwathDefinition`` objects at call time.  Only those
    classes expose the ``area_extent`` attribute.
    """
    return hasattr(obj, "area_extent") and not isinstance(obj, xr.DataTree)
