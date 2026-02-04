# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module for setting paths used throughout GeoIPS.

This module sets various directory paths required for GeoIPS.
Setting these variables here keeps geoips code and outputs consolidated.
Eventually, we aim to supplant this method of setting variables with a config file.
`GEOIPS_OUTDIRS` serves as the base reference for all other variables and defaults
to the current directory.

The module defaults to the values set in environment variables for all other variables.
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
import platformdirs

LOG = logging.getLogger(__name__)


def cast_to_bool(value):
    """Cast the environment variable with value 'value' to a boolean.

    For example, if the variable was 'GEOIPS_REBUILD_REGISTRIES' and its value was '0',
    then this variable would be cast as a False boolean.

    Parameters
    ----------
    value: Any
        - The value of an environment variable.

    Returns
    -------
    value: bool
        - The boolean casted value of the corresponding environment variable.
    """
    if value == "0" or value == "False" or value == "false":
        return False
    else:
        return True


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
    try:
        paths["GEOIPS_OUTDIRS"] = os.environ["GEOIPS_OUTDIRS"].rstrip("/")
    except KeyError:
        LOG.warning(
            "GEOIPS_OUTDIRS is not set in your environment. "
            "Defaulting to $HOME/GEOIPS_OUTDIRS as output dir. "
            "Please set GEOIPS_OUTDIRS if you want to write to a "
            "different directory by default."
        )
        try:
            home_dir = os.environ["HOME"]
        except KeyError:
            LOG.error(
                "Could not resolve enviorment variable " "'$HOME', using '/' as default"
            )
            home_dir = "/"
        paths["GEOIPS_OUTDIRS"] = os.path.join(home_dir, "GEOIPS_OUTDIRS")
    paths["GEOIPS_PACKAGES_DIR"] = os.path.abspath(
        os.path.join(paths["BASE_PATH"], os.pardir, os.pardir)
    )
    paths["GEOIPS_BASEDIR"] = get_env_var(
        "GEOIPS_BASEDIR",
        os.path.abspath(os.path.join(paths["GEOIPS_PACKAGES_DIR"], os.pardir)),
    )
    paths["GEOIPS_REBUILD_REGISTRIES"] = get_env_var(
        "GEOIPS_REBUILD_REGISTRIES",
        True,
    )
    paths["NO_COLOR"] = get_env_var(
        "NO_COLOR",
        True,
    )
    paths["GEOIPS_GEOLOCATION_CACHE_BACKEND"] = get_env_var(
        "GEOIPS_GEOLOCATION_CACHE_BACKEND",
        "memmap",
    )
    paths["GEOIPS_DATA_CACHE_DIR"] = get_env_var(
        "GEOIPS_DATA_CACHE_DIR",
        os.path.join(paths["GEOIPS_OUTDIRS"], "cache", "geoips"),
    )
    paths["SATPY_DATA_CACHE_DIR"] = get_env_var(
        "SATPY_DATA_CACHE_DIR", os.path.join(paths["GEOIPS_OUTDIRS"], "cache", "satpy")
    )
    # This list should include all env vars that could end up in output product paths
    # or metadata. This ensures consistent tests and generalized output paths.
    # This GEOIPS_REPLACE_OUTPUT_PATHS is referenced in the following scripts and files:
    # * geoips/geoips/geoips_utils.py
    # * geoips/tests/integration_tests/test_integration.py
    # * geoips/geoips/filenames/base_paths.py
    replace_output_paths = get_env_var(
        "GEOIPS_REPLACE_OUTPUT_PATHS",
        "TCWWW TCPRIVATEWWW PRIVATEWWW PUBLICWWW GEOTIFF_IMAGERY_PATH "
        "ANNOTATED_IMAGERY_PATH CLEAN_IMAGERY_PATH ",
    )
    paths["GEOIPS_REPLACE_OUTPUT_PATHS"] = replace_output_paths.split(" ")
    # Convert the string to a bool
    paths["GEOIPS_REBUILD_REGISTRIES"] = cast_to_bool(
        paths["GEOIPS_REBUILD_REGISTRIES"]
    )
    # NOTE: Environment variable 'NO_COLOR' will disable any colored output from the
    # terminal, even if it's not produced via GeoIPS. For example, if this is set to
    # True in your bashrc, even pytest output will be monochrome. We chose this variable
    # name as it is consistent with the settings that other software packages use.
    paths["NO_COLOR"] = cast_to_bool(paths["NO_COLOR"])

    # Identify defaults for global GeoIPS variables.  The actual values for
    # these variables will be set using get_env_var below.
    geoips_global_variable_defaults = {
        # GeoIPS Documentation URL
        "GEOIPS_DOCS_URL": r"https://nrlmmd-geoips.github.io/geoips/",
        # Version
        "GEOIPS_VERS": "0.0.0",
        # Operational User
        "GEOIPS_OPERATIONAL_USER": False,
        # Copyright Information
        "GEOIPS_COPYRIGHT": "NRL-Monterey",
        "GEOIPS_COPYRIGHT_ABBREVIATED": "NRLMRY",
        # Configuration and Queue
        # Note: platformdirs provides functions to retrieve appropriate directory paths
        # for different use types on different operating systems. GEOIPS_CACHE_DIR will
        # resolve to a different path on Linux/WSL, OSX, and Windows.
        "GEOIPS_CACHE_DIR": platformdirs.user_cache_dir("geoips"),
        "GEOIPS_RCFILE": "",
        "DEFAULT_QUEUE": None,
        # Computer Identifier
        "BOXNAME": socket.gethostname(),
        # Threshold for image-based output checks.  This will be cast to float below.
        "OUTPUT_CHECKER_THRESHOLD_IMAGE": 0.05,
        # Minimal default
        # "GEOIPS_LOG_FMT_STRING": "%(asctime)s: %(message)s"
        # "GEOIPS_LOG_DATEFMT_STRING": "%d_%H%M%S"
        # More informative default
        "GEOIPS_LOGGING_FMT_STRING": "%(asctime)s %(module)12s.py:%(lineno)-4d "
        "%(levelname)7s: %(message)s",
        "GEOIPS_LOGGING_DATEFMT_STRING": "%d_%H%M%S",
        "GEOIPS_LOGGING_LEVEL": "interactive",
        # Changes the warning level used for warnings.simplefilter
        # Valid options are "ignore", "default", "error", "always", "module", "once"
        # See https://docs.python.org/3/library/warnings.html#the-warnings-filter
        # for details on each option.
        "GEOIPS_WARNING_LEVEL": "default",
        "GEOIPS_TEST_PRINT_TEXT_OUTPUT_CHECKER_TO_CONSOLE": True,
        "GEOIPS_RICH_CONSOLE_OUTPUT": False,
        "GEOIPS_PROMPT_TO_OVERWRITE_COMPARISON_FILE_IF_MISMATCH": False,
    }

    # Long variables names to avoid black and flake8 conflicts.
    # flake8 was flagging for long lines, but black was not correcting them.
    # If someone can figure out how to get flake8 and black to play nicely with that
    # line, please resolve!
    dyn_geo_var = "GEOIPS_PREGENERATED_DYNAMIC_GEOLOCATION"
    # Identify the defaults for relative path-based environment variables,
    # these paths default to locations under base paths set above.
    # The actual variables will be set using get_env_var below.
    default_derivative_directory_path_defaults = {
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
            "GEOTIFF_IMAGERY_PATH": "preprocessed/geotiff_imagery",
            "FINAL_DATA_PATH": "preprocessed/final",
            "PREGENERATED_GEOLOCATION_PATH": "preprocessed/geolocation",
            # Used in geostationary_geolocation - use longterm_files
            # for now to maintain backwards compatibility
            "GEOIPS_PREGENERATED_STATIC_GEOLOCATION": "longterm_files/geolocation",
            dyn_geo_var: "longterm_files/geolocation_dynamic",
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
            "TCPRIVATEWWW": "preprocessed/tcprivatewww",
            "PUBLICWWW": "preprocessed/publicwww",
            "PRIVATEWWW": "preprocessed/privatewww",
            # Tropical Cyclone Paths
            "GEOIPS_TC_DECKS_DB": "longterm_files/tc/tc_decks.db",
            "GEOIPS_TC_DECKS_DIR": "longterm_files/tc/decks",
            "GEOIPS_TC_DECKS_TYPE": "bdecks",
        },
        paths["GEOIPS_DATA_CACHE_DIR"]: {
            "GEOIPS_DATA_CACHE_DIR_LONGTERM_GEOLOCATION_DYNAMIC": (
                "longterm/geolocation/dynamic"
            ),
            "GEOIPS_DATA_CACHE_DIR_LONGTERM_GEOLOCATION_STATIC": (
                "longterm/geolocation/static"
            ),
            "GEOIPS_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_SOLAR_ANGLES": (
                "shortterm/geolocation/solar"
            ),
            "GEOIPS_DATA_CACHE_DIR_SHORTTERM_CALIBRATED_DATA": (
                "shortterm/calibrated_data"
            ),
        },
        paths["SATPY_DATA_CACHE_DIR"]: {
            "SATPY_DATA_CACHE_DIR_SHORTTERM_CALIBRATED_DATA": (
                "shortterm/calibrated_data"
            ),
            "SATPY_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_SOLAR_ANGLES": (
                "shortterm/geolocation/solar"
            ),
        },
        paths["BASE_PATH"]: {
            "TC_TEMPLATE": "plugins/yaml/sectors/dynamic/tc_web_template.yaml",
        },
        paths["GEOIPS_REBUILD_REGISTRIES"]: {
            "GEOIPS_REBUILD_REGISTRIES_TRUE": True,
            "GEOIPS_REBUILD_REGISTRIES_FALSE": False,
        },
        paths["NO_COLOR"]: {
            "NO_COLOR_TRUE": True,
            "NO_COLOR_FALSE": False,
        },
    }

    # looping through all the directory-based paths and global variables set above
    # using "get_env_var" function to set the variables to the environment variable
    # specified option (when defined via the first argument)
    # else defaulting to the passed-in default (second argument)
    for key, value in geoips_global_variable_defaults.items():
        paths[key] = get_env_var(key, value)

    for (
        top_directory,
        sub_directories,
    ) in default_derivative_directory_path_defaults.items():
        for key, sub_path in sub_directories.items():
            if "GEOIPS_REBUILD_REGISTRIES" in key or "NO_COLOR" in key:
                paths[key] = get_env_var(key, sub_path, rstrip_path=False)
            else:
                paths[key] = get_env_var(key, os.path.join(top_directory, sub_path))

    # Handling special cases now: home for linux/windows
    if not os.getenv("HOME"):
        # need home drive default for windows
        paths["HOME"] = os.getenv("HOMEDRIVE") + os.getenv("HOMEPATH")
    else:
        paths["HOME"] = os.getenv("HOME").rstrip("/")

    # Setting links for WWW Paths
    www_paths = ["TCWWW", "TCPRIVATEWWW", "PUBLICWWW", "PRIVATEWWW"]
    for path in www_paths:
        paths[f"{path}_URL"] = get_env_var(f"{path}_URL", paths[path])

    # This needs to be a float
    paths["OUTPUT_CHECKER_THRESHOLD_IMAGE"] = float(
        paths["OUTPUT_CHECKER_THRESHOLD_IMAGE"]
    )

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


# Initialize the PATHS dictionary
PATHS = initialize_paths()
