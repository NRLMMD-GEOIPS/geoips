# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters interface class."""

from datetime import datetime
import functools
import inspect
import json
import logging
from os.path import dirname, exists
import warnings

import cartopy.crs as crs
import numpy as np
import xarray as xr

from geoips.filenames.base_paths import make_dirs
from geoips.errors import BoundaryIOError

from geoips.interfaces.class_based_plugin import BaseClassPlugin





