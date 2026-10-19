# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters base interface class."""


import xarray as xr

import logging


LOG = logging.getLogger(__name__)

DATA_PARAM_NAMES = ("xarray_obj", "xarray_dict")