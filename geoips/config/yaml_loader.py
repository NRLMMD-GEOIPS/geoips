# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""YAML configuration file loading utilities.

Searches for project-level GeoIPS configuration files in multiple
locations, following a priority order.
"""

import logging
import os

import yaml

LOG = logging.getLogger(__name__)


def _default_search_locations() -> list[str]:
    """Return the ordered list of project config file search locations.

    Priority order (first found wins):
        1. ``$GEOIPS_RCFILE`` (if set and file exists)
        2. ``./.geoips.yaml`` (current working directory)
        3. ``~/.config/geoips/config.yaml`` (platform-appropriate user config dir)

    Returns
    -------
    list[str]
        Ordered list of candidate file paths to check.
    """
    locations = []

    rcfile = os.getenv("GEOIPS_RCFILE", "")
    if rcfile and os.path.isfile(rcfile):
        locations.append(rcfile)

    cwd_config = os.path.join(os.getcwd(), ".geoips.yaml")
    locations.append(cwd_config)

    home = os.path.expanduser("~")
    xdg_config = os.path.join(home, ".config", "geoips", "config.yaml")
    locations.append(xdg_config)

    return locations


def find_project_config(project_config_path: str | None = None) -> str | None:
    """Find the project-level YAML configuration file.

    If *project_config_path* is supplied, only that path is checked. Otherwise,
    searches locations returned by :func:`_default_search_locations` in order,
    returning the first file path that exists.

    Parameters
    ----------
    project_config_path : str or None, optional
        Explicit project config path to use instead of the default search locations.

    Returns
    -------
    str or None
        Absolute path to the found config file, or ``None`` if no file was found
        during default search.

    Raises
    ------
    FileNotFoundError
        If *project_config_path* is supplied and does not exist.
    """
    if project_config_path is not None:
        if os.path.isfile(project_config_path):
            LOG.debug("Found project config: %s", project_config_path)
            return os.path.abspath(project_config_path)
        raise FileNotFoundError(
            f"Project config file {project_config_path!r} does not exist."
        )

    for candidate in _default_search_locations():
        if os.path.isfile(candidate):
            LOG.debug("Found project config: %s", candidate)
            return os.path.abspath(candidate)
    return None


def load_project_config(project_config_path: str | None = None) -> dict | None:
    """Load the project-level YAML configuration as a dictionary.

    Finds and parses the project config file using
    :func:`find_project_config`.

    Parameters
    ----------
    project_config_path : str or None, optional
        Explicit project config path to use instead of the default search locations.

    Returns
    -------
    dict or None
        Parsed YAML dictionary if a config file was found, otherwise ``None``.
    """
    config_path = find_project_config(project_config_path)
    if config_path is None:
        return None
    with open(config_path, "r") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        LOG.warning(
            "Project config file %s is not a valid YAML mapping, ignoring.",
            config_path,
        )
        return None
    return data
