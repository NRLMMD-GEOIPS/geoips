# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

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

from geoips import errors
from geoips import filenames
from geoips import interfaces
from geoips import utils
from geoips import xarray_utils
from ._version import __version__, __version_tuple__

__all__ = [
    "interfaces",
    "errors",
    "filenames",
    "utils",
    "xarray_utils",
    "__version__",
    "__version_tuple__",
]
