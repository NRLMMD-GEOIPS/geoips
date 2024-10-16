# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module for setting paths used throughout GeoIPS.

This module sets various directory paths required for GeoIPS.
Setting these variables here keeps geoips code and outputs consolidated.
Eventually, we aim to supplant this method of setting variables with a config file.
`GEOIPS_OUTDIRS` serves as the base reference for all other variables.
It defaults to the values set in environment variables.
It also provides a function for creating directories.


Functions
---------
- get_env_var: Retrieve an environment variable or a provided default value.
- initialize_paths: Returns a dictionary with GeoIPS directories and variables.
- make_dirs: Create directories if they don't already exist.

Attributes
----------
- PATHS: Dictionary with initialized paths for various GeoIPS directories and URLs.

Environment Variables:
- GEOIPS_OUTDIRS (required): Base output directory for GeoIPS.
"""

import logging
import os
import socket


def get_env_var(var_name, default, rstrip_path=True):
    """Retrieve environment variable or provided default, optionally rstrip a '/'.

    Parameters
    ----------
    var_name : str
        The name of the environment variable.
    default : str
        The default value to return if the environment variable is not set.
    rstrip_path : bool, optional
        If True, strip trailing slashes from the returned path (default is True).

    Returns
    -------
    str
        The value of the environment variable or the default value if not set.
    """
    env_value = os.getenv(var_name)
    if env_value:
        if rstrip_path:
            return env_value.rstrip("/")
        else:
            return env_value
    else:
        return default


def initialize_paths():
    """
    Initialize and return a dictionary of paths used throughout GeoIPS.

    Returns
    -------
    dict
        A dictionary containing various paths used by GeoIPS.

    Raises
    ------
    KeyError
        If the required environment variable GEOIPS_OUTDIRS is not set.
    """
    paths = {}

    # Base and Documentation Paths
    paths["BASE_PATH"] = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir)
    )

    # Output Directories
    if not os.getenv("GEOIPS_OUTDIRS"):
        raise KeyError(
            "GEOIPS_OUTDIRS must be set in your environment. "
            "Please set GEOIPS_OUTDIRS and try again"
        )
    paths["GEOIPS_OUTDIRS"] = os.getenv("GEOIPS_OUTDIRS").rstrip("/")
    paths["GEOIPS_PACKAGES_DIR"] = os.path.abspath(
        os.path.join(paths["BASE_PATH"], os.pardir, os.pardir)
    )
    paths["GEOIPS_BASEDIR"] = get_env_var(
        "GEOIPS_BASEDIR",
        os.path.abspath(os.path.join(paths["GEOIPS_PACKAGES_DIR"], os.pardir)),
    )

    geoips_global_variables = {
        # GeoIPS Documentation URL
        "GEOIPS_DOCS_URL": r"https://nrlmmd-geoips.github.io/geoips/",
        # Version
        "GEOIPS_VERS": os.getenv("GEOIPS_VERS", "0.0.0"),
        # Operational User
        "GEOIPS_OPERATIONAL_USER": os.getenv("GEOIPS_OPERATIONAL_USER", False),
        # Copyright Information
        "GEOIPS_COPYRIGHT": os.getenv("GEOIPS_COPYRIGHT", "NRL-Monterey"),
        "GEOIPS_COPYRIGHT_ABBREVIATED": os.getenv(
            "GEOIPS_COPYRIGHT_ABBREVIATED", "NRLMRY"
        ),
        # Configuration and Queue
        "GEOIPS_RCFILE": os.getenv("GEOIPS_RCFILE", ""),
        "DEFAULT_QUEUE": os.getenv("DEFAULT_QUEUE", None),
        # Computer Identifier
        "BOXNAME": socket.gethostname(),
        "OUTPUT_CHECKER_THRESHOLD_IMAGE": float(
            os.getenv("OUTPUT_CHECKER_THRESHOLD_IMAGE", 0.05)
        ),
    }

    # these are the defaults for path based environment variables
    # that default to locations under paths set above
    # They can are overridden by set environment variables.
    default_derivative_directory_paths = {
        paths["GEOIPS_BASEDIR"]: {
            "GEOIPS_TESTDATA_DIR": "test_data",
            "GEOIPS_DEPENDENCIES_DIR": "geoips_dependencies",
        },
        paths["GEOIPS_OUTDIRS"]: {
            # Data Output Paths
            "PRESECTORED_DATA_PATH": "preprocessed/sectored",
            "PREREAD_DATA_PATH": "preprocessed/unsectored",
            "PREREGISTERED_DATA_PATH": "preprocessed/registered",
            "PRECALCULATED_DATA_PATH": "preprocessed/algorithms",
            "CLEAN_IMAGERY_PATH": "preprocessed/clean_imagery",
            "ANNOTATED_IMAGERY_PATH": "preprocessed/annotated_imagery",
            "FINAL_DATA_PATH": "preprocessed/final",
            "PREGENERATED_GEOLOCATION_PATH": "preprocessed/geolocation",
            # Scratch Directories
            "SCRATCH": "scratch",
            "LOCALSCRATCH": "scratch",
            "SHAREDSCRATCH": "scratch",
            # Log and Data Directories
            "LOGDIR": "logs",
            "GEOIPSDATA": "geoipsdata",
            # Ancillary Data Directories
            "GEOIPS_ANCILDAT_AUTOGEN": "ancildat_autogen",
            "GEOIPS_ANCILDAT": "ancildat",
            # WWW Paths
            "TCWWW": "preprocessed/tcwww",
            "PUBLICWWW": "preprocessed/publicwww",
            "PRIVATEWWW": "preprocessed/privatewww",
            # Tropical Cyclone Paths
            "TC_DECKS_DB": "longterm_files/tc/tc_decks.db",
            "TC_DECKS_DIR": "longterm_files/tc/decks",
        },
        paths["BASE_PATH"]: {
            "TC_TEMPLATE": "plugins/yaml/sectors/dynamic/tc_web_template.yaml",
        },
    }

    # looping through all the directory-based paths and global variables set above
    # using "get_env_var" function to set the variables to the environment variable
    # specified option (when defined via the first argument)
    # else defaulting to the passed-in default (second argument)
    for key, value in geoips_global_variables.items():
        paths[key] = get_env_var(key, value)

    for top_directory, sub_directories in default_derivative_directory_paths.items():
        for key, sub_path in sub_directories.items():
            paths[key] = get_env_var(key, os.path.join(top_directory, sub_path))

    # Handling special cases now: home for linux/windows
    if not os.getenv("HOME"):
        # need home drive default for windows
        paths["HOME"] = os.getenv("HOMEDRIVE") + os.getenv("HOMEPATH")
    else:
        paths["HOME"] = os.getenv("HOME").rstrip("/")

    # Setting links for WWW Paths
    www_paths = ["TCWWW", "PUBLICWWW", "PRIVATEWWW"]
    for path in www_paths:
        paths[f"{path}_URL"] = get_env_var(f"{path}_URL", paths[path])

    return paths


def make_dirs(path):
    """Make directories, catching exceptions if directory already exists.

    Parameters
    ----------
    path : str
        Path to directory to create

    Returns
    -------
    str
        Path if successfully created
    """
    LOG.info("Creating directory %s if it doesn't already exist.", path)
    os.makedirs(path, mode=0o755, exist_ok=True)
    return path


LOG = logging.getLogger(__name__)

# Initialize the PATHS dictionary
PATHS = initialize_paths()
