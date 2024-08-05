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
        "Please set GEOIPS_OUTDIRS and try again"
    )


def get_env_path(var_name, default_path, rstrip_path=True):
    """Retrieve environment variable or return a default path."""
    env_value = os.getenv(var_name)
    if env_value:
        if rstrip_path:
            return env_value.rstrip("/")
        else:
            return env_value
    else:
        return default_path


def initialize_paths():
    """Initialize the PATHS dictionary with environment paths and defaults."""
    paths = {}

    # Base and Documentation Paths
    paths["BASE_PATH"] = os.path.join(os.path.dirname(__file__), "..")
    paths["GEOIPS_DOCS_URL"] = r"https://nrlmmd-geoips.github.io/geoips/"

    # Operational User
    paths["GEOIPS_OPERATIONAL_USER"] = os.getenv("GEOIPS_OPERATIONAL_USER", False)

    # Output Directories
    geoips_outdirs = os.getenv("GEOIPS_OUTDIRS")
    if not geoips_outdirs:
        raise KeyError(
            "GEOIPS_OUTDIRS must be set in your environment. "
            "Please set GEOIPS_OUTDIRS and try again"
        )
    paths["GEOIPS_OUTDIRS"] = geoips_outdirs.rstrip("/")

    # Package Directories
    geoips_packages_dir = get_env_path(
        "GEOIPS_PACKAGES_DIR", os.path.join(paths["BASE_PATH"], "..", "..")
    )
    if os.path.exists(geoips_packages_dir):
        paths["GEOIPS_PACKAGES_DIR"] = geoips_packages_dir

    # Base Directory
    paths["GEOIPS_BASEDIR"] = get_env_path(
        "GEOIPS_BASEDIR", os.path.join(paths["GEOIPS_PACKAGES_DIR"], "..")
    )

    # Test Data Directory
    paths["GEOIPS_TESTDATA_DIR"] = get_env_path(
        "GEOIPS_TESTDATA_DIR", paths["GEOIPS_BASEDIR"] + "/test_data"
    )

    # Dependencies Directory
    paths["GEOIPS_DEPENDENCIES_DIR"] = get_env_path(
        "GEOIPS_DEPENDENCIES_DIR", paths["GEOIPS_BASEDIR"] + "/geoips_dependencies"
    )

    # Data Processing Paths
    data_paths = {
        "PRESECTORED_DATA_PATH": "preprocessed/sectored",
        "PREREAD_DATA_PATH": "preprocessed/unsectored",
        "PREREGISTERED_DATA_PATH": "preprocessed/registered",
        "PRECALCULATED_DATA_PATH": "preprocessed/algorithms",
        "CLEAN_IMAGERY_PATH": "preprocessed/clean_imagery",
        "ANNOTATED_IMAGERY_PATH": "preprocessed/annotated_imagery",
        "FINAL_DATA_PATH": "preprocessed/final",
        "PREGENERATED_GEOLOCATION_PATH": "preprocessed/geolocation",
    }

    for key, subdir in data_paths.items():
        paths[key] = get_env_path(key, os.path.join(paths["GEOIPS_OUTDIRS"], subdir))

    # Copyright Information
    paths["GEOIPS_COPYRIGHT"] = os.getenv("GEOIPS_COPYRIGHT", "NRL-Monterey")
    paths["GEOIPS_COPYRIGHT_ABBREVIATED"] = os.getenv(
        "GEOIPS_COPYRIGHT_ABBREVIATED", "NRLMRY"
    )

    # Configuration and Queue
    paths["GEOIPS_RCFILE"] = os.getenv("GEOIPS_RCFILE", "")
    paths["DEFAULT_QUEUE"] = os.getenv("DEFAULT_QUEUE", None)

    # Hostname and Home Directory
    paths["BOXNAME"] = socket.gethostname()
    if not os.getenv("HOME"):
        # need home drive default for windows
        paths["HOME"] = os.getenv("HOMEDRIVE") + os.getenv("HOMEPATH")
    else:
        paths["HOME"] = os.getenv("HOME").rstrip("/")

    # Scratch Directories
    scratch_dir = get_env_path(
        "SCRATCH", os.path.join(paths["GEOIPS_OUTDIRS"], "scratch")
    )
    paths["SCRATCH"] = scratch_dir
    paths["LOCALSCRATCH"] = get_env_path("LOCALSCRATCH", scratch_dir)
    paths["SHAREDSCRATCH"] = get_env_path("SHAREDSCRATCH", scratch_dir)

    # Ancillary Data Directories
    paths["GEOIPS_ANCILDAT"] = get_env_path(
        "GEOIPS_ANCILDAT", os.path.join(paths["GEOIPS_OUTDIRS"], "ancildat")
    )
    paths["GEOIPS_ANCILDAT_AUTOGEN"] = get_env_path(
        "GEOIPS_ANCILDAT_AUTOGEN",
        os.path.join(paths["GEOIPS_OUTDIRS"], "ancildat_autogen"),
    )

    # Log and Data Directories
    paths["LOGDIR"] = get_env_path(
        "LOGDIR", os.path.join(paths["GEOIPS_OUTDIRS"], "logs")
    )
    paths["GEOIPSDATA"] = get_env_path(
        "GEOIPSDATA", os.path.join(paths["GEOIPS_OUTDIRS"], "geoipsdata")
    )

    # Version
    paths["GEOIPS_VERS"] = os.getenv("GEOIPS_VERS", "0.0.0")

    # WWW Paths
    www_paths = {
        "TCWWW": "preprocessed/tcwww",
        "PUBLICWWW": "preprocessed/publicwww",
        "PRIVATEWWW": "preprocessed/privatewww",
    }

    for key, subdir in www_paths.items():
        paths[key] = get_env_path(key, os.path.join(paths["GEOIPS_OUTDIRS"], subdir))
        paths[f"{key}_URL"] = get_env_path(f"{key}_URL", paths[key])

    # Tropical Cyclone Paths
    paths["TC_DECKS_DB"] = get_env_path(
        "TC_DECKS_DB",
        os.path.join(paths["GEOIPS_OUTDIRS"], "longterm_files/tc/tc_decks.db"),
    )
    paths["TC_DECKS_DIR"] = get_env_path(
        "TC_DECKS_DIR", os.path.join(paths["GEOIPS_OUTDIRS"], "longterm_files/tc/decks")
    )

    # Template Paths
    paths["TC_TEMPLATE"] = get_env_path(
        "TC_TEMPLATE",
        os.path.join(
            paths["BASE_PATH"], "plugins/yaml/sectors/dynamic/tc_web_template.yaml"
        ),
    )

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

    if not os.path.exists(path):
        try:
            LOG.info("Creating directory %s", path)
            makedirs(path, mode=0o755)
        except OSError as resp:
            LOG.warning(
                "%s: We thought %s did not exist, but then it did. "
                "Not trying to make directory",
                resp,
                path,
            )
    return path


# Initialize the PATHS dictionary
PATHS = initialize_paths()
