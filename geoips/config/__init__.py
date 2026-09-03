# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS configuration package.

Provides a layered, YAML-based configuration system with environment
variable overrides.

Usage::

    from geoips.config import config

    print(config.outdirs)
    print(config.features.no_color)
    print(config["GEOIPS_OUTDIRS"])  # backward-compatible dict access
"""

from geoips.config.config import GeoIPSConfig, get_config, make_dirs
from geoips.config.plugins import ConfigPlugin
from geoips.config.schema import GeoSettings

config = get_config()

__all__ = [
    "ConfigPlugin",
    "GeoIPSConfig",
    "GeoSettings",
    "config",
    "get_config",
    "make_dirs",
]
