"""Module for handling cached files in GeoIPS.

This modules provides functions to manage cache files in GeoIPS.
Cache files will be stored in the user cache directory, which is platform-dependent. The
correct cache directory is determined using the GEOIPS_CACHE_DIR environment variable
which defaults to `platformdirs.user_cache_dir("geoips")` if not set.
"""

import os
import yaml
import json
from logging import getLogger
from geoips.filenames.base_paths import PATHS

LOG = getLogger(__name__)


def source_modified(source, dest):
    """Check if the source file was modified more recently than the destination file.

    This uses os.path.getmtime() to determine whether the source file has been modified
    more recently than the destination file. Returns True if the source file was
    modified more recently than the destination file, False otherwise.

    Parameters
    ----------
    source: str
        The path to the source file we are monitoring for changes.
    dest: str
        The path to the destination file we will update if the source file changes.

    Returns
    -------
    bool
        True if the source file was modified more recently than the destination file,
        False otherwise.
    """
    if not os.path.exists(dest) or os.path.getmtime(source) > os.path.getmtime(dest):
        return True
    return False


def create_cached_json_from_yaml(source, cache_dir=None):
    """Create a cached JSON file from a YAML file.

    This function reads a YAML file and writes its contents to a JSON file in the user
    cache directory. The JSON file will be created if it does not already exist, or
    updated if it does.

    Parameters
    ----------
    source: str
        The path to the source YAML file.
    cache_dir: str, optional
        The path to the cache directory. If not provided, the default user cache
        directory will be used.

    Returns
    -------
    str
        The path to the cached JSON file.
    """
    if not cache_dir:
        cache_dir = PATHS["GEOIPS_CACHE_DIR"]

    os.makedirs(cache_dir, exist_ok=True)
    dest = os.path.join(cache_dir, os.path.basename(source).replace(".yaml", ".json"))

    if source_modified(source, dest):
        with open(source, "r") as yaml_file:
            data = yaml.safe_load(yaml_file)

        with open(dest, "w") as json_file:
            json.dump(data, json_file, indent=4)
    return dest


def get_cached_json(source, cache_dir=None):
    """Get the cached JSON file corresponding to a YAML file.

    Some files in GeoIPS are stored in YAML format, but we want to use JSON at runtime
    because loading JSON is faster than loading YAML. This function checks if the cached
    JSON file exists and is up to date. If it does not exist or is out of date, it
    creates a new cached JSON file from the YAML file. It then returns the contents of
    the cached JSON file.

    Parameters
    ----------
    source: str
        The path to the source YAML file.
    cache_dir: str, optional
        The path to the cache directory. If not provided, the default user cache
        directory will be used.
    """
    cache_file = create_cached_json_from_yaml(source)
    with open(cache_file, "r") as json_file:
        return json.load(json_file)
