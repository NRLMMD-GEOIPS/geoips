# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Deprecated -- use ``geoips.config`` instead.

This module exists for backward compatibility and will be removed in
a future release. The ``PATHS`` dictionary is now populated from the
new ``geoips.config.GeoIPSConfig`` singleton.
"""

import logging
import os
from warnings import warn

from geoips.config import config, make_dirs as _make_dirs

LOG = logging.getLogger(__name__)

warn(
    "geoips.filenames.base_paths is deprecated; use geoips.config instead.",
    DeprecationWarning,
    stacklevel=4,
)

PATHS = config.to_legacy_dict()


def make_dirs(path):
    """Make directories, catching exceptions if directory already exists.

    Deprecated: Use ``geoips.config.make_dirs`` instead.
    """
    return _make_dirs(path)


def cast_string_to_bool_or_none(value):
    """Cast string environment variables to True, False, or None.

    Deprecated: Handled automatically by ``geoips.config.GeoIPSConfig``.
    """
    if value.lower() == "false":
        return False
    elif value.lower() == "true":
        return True
    elif value.lower() in ["none", "null"]:
        return None
    else:
        return value


def get_env_var(var_name, default, rstrip_path=True):
    """Retrieve environment variable or provided default.

    Deprecated: Use ``geoips.config.GeoIPSConfig`` instead.
    """
    env_value = os.getenv(var_name)
    retval = default
    if env_value:
        if rstrip_path:
            env_value = env_value.rstrip("/")
        env_value = cast_string_to_bool_or_none(env_value)
        retval = env_value
    return retval


def initialize_paths():
    """Initialize and return a dictionary of paths used throughout GeoIPS.

    Deprecated: Use ``geoips.config.GeoIPSConfig.to_legacy_dict`` instead.
    """
    return config.to_legacy_dict()
