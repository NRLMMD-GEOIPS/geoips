# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Collection of base path names used throughout GeoIPS.

Everything defaults to subdirectories relative to the
REQUIRED environment variable GEOIPS_OUTDIRS.

Individual GEOIPS_OUTDIRS relative paths can be overridden
by setting appropriate environment variables.
"""

# Python Standard Libraries
import logging
import os
import socket

LOG = logging.getLogger(__name__)

# At a minimum, GEOIPS_OUTDIRS must be defined.
if not os.getenv("GEOIPS_OUTDIRS"):
    raise KeyError(
        "GEOIPS_OUTDIRS must be set in your environment."
        "Please set GEOIPS_OUTDIRS and try again."
    )


def get_env_var(var_name, default, rstrip_path=True):
    """Retrieve environment variable or provided default, optionally rstrip a '/'."""
    env_value = os.getenv(var_name)
    if env_value:
        if rstrip_path:
            return env_value.rstrip("/")
        else:
            return env_value
    else:
        return default


def initialize_paths():
    """Initialize the PATHS dictionary with environment paths and defaults."""
    paths = {}

    # Base and Documentation Paths
    paths["BASE_PATH"] = os.path.join(os.path.dirname(__file__), "..")

    # Output Directories
    if not os.getenv("GEOIPS_OUTDIRS"):
        raise KeyError(
            "GEOIPS_OUTDIRS must be set in your environment. "
            "Please set GEOIPS_OUTDIRS and try again"
        )
    paths["GEOIPS_OUTDIRS"] = os.getenv("GEOIPS_OUTDIRS").rstrip("/")
    paths["GEOIPS_PACKAGES_DIR"] = os.path.join(paths["BASE_PATH"], "..", "..")
    paths["GEOIPS_BASEDIR"] = get_env_var(
        "GEOIPS_BASEDIR", os.path.join(paths["GEOIPS_PACKAGES_DIR"], "..")
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
    }

    paths.update(geoips_global_variables)

    derivative_directory_paths = {
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

    for top_directory, sub_directories in derivative_directory_paths.items():
        for key, sub_path in sub_directories.items():
            paths[key] = os.path.join(top_directory, sub_path)

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
    """Make directories, catching exceptions if directory already os.path.exists.

    Parameters
    ----------
    path : str
        Path to directory to create

    Returns
    -------
    str
        Path if successfully created
    """
    from os import makedirs

    LOG.info("Creating directory %s if it doesn't exist already.", path)
    makedirs(path, mode=0o755, exist_ok=True)

    return path


# Initialize the PATHS dictionary
PATHS = initialize_paths()
