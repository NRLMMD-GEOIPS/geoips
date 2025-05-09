# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""
The Geolocated Information Processing System (GeoIPS).

GeoIPS |unireg| Base Package
----------------------------

The GeoIPS Base Package provides a Python 3 based architecture supporting a wide
variety of satellite and weather data processing. The modular nature of the GeoIPS
base infrastructure also allows plug-and-play capability for user-specified custom
functionality.

Homepage: https://github.com/NRLMMD-GEOIPS/geoips

.. |unireg|    unicode:: U+000AE .. REGISTERED SIGN
"""
from matplotlib import rcParams
from geoips import errors
from geoips import filenames
from geoips import interfaces
from geoips import utils
from geoips import xarray_utils
from ._version import __version__, __version_tuple__

import logging  # noqa
from geoips.commandline.log_setup import add_logging_level

# Turn off image interpolation for matplotlib by default.
rcParams["image.interpolation"] = "none"

# Setting INTERACTIVE to 25 as this is between INFO (20) and WARNING (30). This way,
# WARNING output will still be shown if INFO or INTERACTIVE is set.
add_logging_level("INTERACTIVE", 25)

__all__ = [
    "interfaces",
    "errors",
    "filenames",
    "utils",
    "xarray_utils",
    "__version__",
    "__version_tuple__",
]
