# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Compatibility wrapper around ``geoips_yaml_utils``.

Usage:
    import geoips.utils.yaml_utils as yaml

GeoIPS historically imported this module as its YAML facade. Keep that import
path working while delegating the actual implementation to the standalone
``geoips_yaml_utils`` package.

``safe_load`` and ``safe_load_all`` intentionally use
``EnvVarLoaderNoDuplicates`` so existing GeoIPS callers get both duplicate-key
detection and ``!ENV`` expansion.
"""

from geoips_yaml_utils import *  # noqa: F401, F403
import geoips_yaml_utils as _yaml


def load(stream, Loader=EnvVarLoaderNoDuplicates, *args, **kwargs):  # noqa: F405
    """Load YAML with GeoIPS defaults.

    Defaults to a safe loader that rejects duplicate keys and expands ``!ENV``
    tags. Callers may pass a different ``Loader`` to preserve PyYAML's normal
    ``load`` flexibility.
    """
    return _yaml.load(stream, Loader=Loader, *args, **kwargs)


def load_all(stream, Loader=EnvVarLoaderNoDuplicates, *args, **kwargs):  # noqa: F405
    """Load all YAML documents with GeoIPS defaults."""
    return _yaml.load_all(stream, Loader=Loader, *args, **kwargs)


safe_load = load
safe_load_all = load_all
