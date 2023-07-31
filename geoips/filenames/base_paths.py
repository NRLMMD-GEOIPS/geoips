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

"""Collection of base path names used throughout GeoIPS.

Everything defaults to subdirectories relative to the
REQUIRED environment variable GEOIPS_OUTDIRS.

Individual GEOIPS_OUTDIRS relative paths can be overridden
by setting appropriate environment variables.
"""

# Python Standard Libraries
import logging
from os import getenv, listdir
from os.path import exists, dirname, join as pathjoin
import socket

LOG = logging.getLogger(__name__)

PATHS = {}

# Get the base package directory
PATHS["BASE_PATH"] = pathjoin(dirname(__file__), "..")

PATHS["GEOIPS_OPERATIONAL_USER"] = False
if getenv("GEOIPS_OPERATIONAL_USER"):
    PATHS["GEOIPS_OPERATIONAL_USER"] = getenv("GEOIPS_OPERATIONAL_USER")

# At a minimum, GEOIPS_OUTDIRS must be defined.
if not getenv("GEOIPS_OUTDIRS"):
    raise KeyError(
        "GEOIPS_OUTDIRS must be set in your environment.  "
        "Please set GEOIPS_OUTDIRS and try again"
    )
else:
    PATHS["GEOIPS_OUTDIRS"] = getenv("GEOIPS_OUTDIRS").rstrip("/")

if getenv("GEOIPS_PACKAGES_DIR") and exists(getenv("GEOIPS_PACKAGES_DIR")):
    PATHS["GEOIPS_PACKAGES_DIR"] = getenv("GEOIPS_PACKAGES_DIR").rstrip("/")
    PATHS["GEOIPS_PACKAGES"] = listdir(getenv("GEOIPS_PACKAGES_DIR"))
elif getenv("GEOIPS_PACKAGES_DIR"):
    PATHS["GEOIPS_PACKAGES_DIR"] = getenv("GEOIPS_PACKAGES_DIR").rstrip("/")
    PATHS["GEOIPS_PACKAGES"] = ["geoips"]
else:
    PATHS["GEOIPS_PACKAGES_DIR"] = None
    PATHS["GEOIPS_PACKAGES"] = ["geoips"]

if not getenv("GEOIPS_BASEDIR"):
    PATHS["GEOIPS_BASEDIR"] = pathjoin(PATHS["GEOIPS_PACKAGES_DIR"], "..")
else:
    PATHS["GEOIPS_BASEDIR"] = getenv("GEOIPS_BASEDIR").rstrip("/")

if getenv("GEOIPS_TESTDATA_DIR"):
    PATHS["GEOIPS_TESTDATA_DIR"] = getenv("GEOIPS_TESTDATA_DIR")
else:
    PATHS["GEOIPS_TESTDATA_DIR"] = PATHS["GEOIPS_BASEDIR"] + "/test_data"

if getenv("GEOIPS_DEPENDENCIES_DIR"):
    PATHS["GEOIPS_DEPENDENCIES_DIR"] = getenv("GEOIPS_DEPENDENCIES_DIR")
else:
    PATHS["GEOIPS_DEPENDENCIES_DIR"] = PATHS["GEOIPS_BASEDIR"] + "/geoips_dependencies"

# Location for writing out presectored data files, but unregistered
if getenv("PRESECTORED_DATA_PATH"):
    PATHS["PRESECTORED_DATA_PATH"] = getenv("PRESECTORED_DATA_PATH").rstrip("/")
else:
    PATHS["PRESECTORED_DATA_PATH"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "sectored"
    )

# Location for writing out preread, but unsectored/registered, data files
if getenv("PREREAD_DATA_PATH"):
    PATHS["PREREAD_DATA_PATH"] = getenv("PREREAD_DATA_PATH").rstrip("/")
else:
    PATHS["PREREAD_DATA_PATH"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "unsectored"
    )

# Location for writing out preregistered data files, but no algorithms applied
if getenv("PREREGISTERED_DATA_PATH"):
    PATHS["PREREGISTERED_DATA_PATH"] = getenv("PREREGISTERED_DATA_PATH").rstrip("/")
else:
    PATHS["PREREGISTERED_DATA_PATH"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "registered"
    )

# Location for writing out precalculated data files (algorithms applied)
if getenv("PRECALCULATED_DATA_PATH"):
    PATHS["PRECALCULATED_DATA_PATH"] = getenv("PRECALCULATED_DATA_PATH").rstrip("/")
else:
    PATHS["PRECALCULATED_DATA_PATH"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "algorithms"
    )

# Location for writing out pregenerated "clean" imagery files
if getenv("CLEAN_IMAGERY_PATH"):
    PATHS["CLEAN_IMAGERY_PATH"] = getenv("CLEAN_IMAGERY_PATH").rstrip("/")
else:
    PATHS["CLEAN_IMAGERY_PATH"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "clean_imagery"
    )

# Location for writing out pregenerated "clean" imagery files
if getenv("ANNOTATED_IMAGERY_PATH"):
    PATHS["ANNOTATED_IMAGERY_PATH"] = getenv("ANNOTATED_IMAGERY_PATH").rstrip("/")
else:
    PATHS["ANNOTATED_IMAGERY_PATH"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "annotated_imagery"
    )

# Location for writing out precalculated data files (algorithms applied)
if getenv("FINAL_DATA_PATH"):
    PATHS["FINAL_DATA_PATH"] = getenv("FINAL_DATA_PATH").rstrip("/")
else:
    PATHS["FINAL_DATA_PATH"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "final"
    )

# Location for writing out pregenerated geolocation netcdf files
if getenv("PREGENERATED_GEOLOCATION_PATH"):
    PATHS["PREGENERATED_GEOLOCATION_PATH"] = getenv(
        "PREGENERATED_GEOLOCATION_PATH"
    ).rstrip("/")
else:
    PATHS["PREGENERATED_GEOLOCATION_PATH"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "geolocation"
    )

# GEOIPS_COPYRIGHT determines what organization name displays in imagery titles, etc.
PATHS["GEOIPS_COPYRIGHT"] = "NRL-Monterey"
if getenv("GEOIPS_COPYRIGHT"):
    PATHS["GEOIPS_COPYRIGHT"] = getenv("GEOIPS_COPYRIGHT")

# GEOIPS_COPYRIGHT_ABBREVIATED provides an abbreviated version of the
# copyright, best for filenames, etc.
PATHS["GEOIPS_COPYRIGHT_ABBREVIATED"] = "NRLMRY"
if getenv("GEOIPS_COPYRIGHT_ABBREVIATED"):
    PATHS["GEOIPS_COPYRIGHT_ABBREVIATED"] = getenv("GEOIPS_COPYRIGHT_ABBREVIATED")

PATHS["GEOIPS_RCFILE"] = ""
if getenv("GEOIPS_RCFILE"):
    PATHS["GEOIPS_RCFILE"] = getenv("GEOIPS_RCFILE")

PATHS["TC_TEMPLATE"] = pathjoin(
    PATHS["BASE_PATH"], "plugins", "yaml", "sectors", "dynamic", "tc_web_template.yaml"
)
if getenv("TC_TEMPLATE"):
    PATHS["TC_TEMPLATE"] = getenv("TC_TEMPLATE")

PATHS["DEFAULT_QUEUE"] = None
if getenv("DEFAULT_QUEUE"):
    PATHS["DEFAULT_QUEUE"] = getenv("DEFAULT_QUEUE")

PATHS["BOXNAME"] = socket.gethostname()
if not getenv("HOME"):
    # Windows
    PATHS["HOME"] = getenv("HOMEDRIVE") + getenv("HOMEPATH")
else:
    PATHS["HOME"] = getenv("HOME").rstrip("/")

if not getenv("SCRATCH"):
    PATHS["SCRATCH"] = pathjoin(getenv("GEOIPS_OUTDIRS"), "scratch")
else:
    PATHS["SCRATCH"] = getenv("SCRATCH").rstrip("/")

if not getenv("LOCALSCRATCH"):
    PATHS["LOCALSCRATCH"] = PATHS["SCRATCH"]
else:
    PATHS["LOCALSCRATCH"] = getenv("LOCALSCRATCH").rstrip("/")

if not getenv("SHAREDSCRATCH"):
    PATHS["SHAREDSCRATCH"] = PATHS["SCRATCH"]
else:
    PATHS["SHAREDSCRATCH"] = getenv("SHAREDSCRATCH").rstrip("/")

# This is the default ANCILDATDIR specified in $GEOIPS/geoips/geoalgs/Makefile
# These MUST match or geoalgs won't find ancildat files
# (ANCILDATDIR gets built into fortran routines).
# Used to be $GEOIPS/geoips/geoalgs/dat, but decided it shouldn't be relative to
# source by default...
# Also note I added GEOALGSAUTOGENDATA - these were going directly in ancildat
# previously, which can get rather crowded with TCs and other dynamic sectors.
# Also, separating the auto-generated files from the source files allows for
# individual users to read from the shared ancildat, and write to their own
# auto-generated location
if not getenv("ANCILDATDIR"):
    PATHS["ANCILDATDIR"] = pathjoin(PATHS["GEOIPS_OUTDIRS"], "ancildat")
    PATHS["ANCILDATEXTERNAL"] = pathjoin(PATHS["GEOIPS_OUTDIRS"], "ancildat_external")
    PATHS["ANCILDATAUTOGEN"] = pathjoin(PATHS["GEOIPS_OUTDIRS"], "ancildat_autogen")
else:
    PATHS["ANCILDATDIR"] = getenv("ANCILDATDIR").rstrip("/")
    PATHS["ANCILDATEXTERNAL"] = pathjoin(getenv("ANCILDATDIR"), "external")
    PATHS["ANCILDATAUTOGEN"] = pathjoin(getenv("ANCILDATDIR"), "autogen")

if not getenv("LOGDIR"):
    PATHS["LOGDIR"] = pathjoin(PATHS["GEOIPS_OUTDIRS"], "logs")
else:
    PATHS["LOGDIR"] = getenv("LOGDIR").rstrip("/")

if not getenv("GEOIPSDATA"):
    PATHS["GEOIPSDATA"] = pathjoin(PATHS["GEOIPS_OUTDIRS"], "geoipsdata")
else:
    PATHS["GEOIPSDATA"] = getenv("GEOIPSDATA").rstrip("/")

if getenv("TCWWW"):
    PATHS["TCWWW"] = getenv("TCWWW").rstrip("/")
else:
    PATHS["TCWWW"] = pathjoin(PATHS["GEOIPS_OUTDIRS"], "preprocessed", "tcwww")

if getenv("TCWWW_URL"):
    PATHS["TCWWW_URL"] = getenv("TCWWW_URL").rstrip("/")
else:
    PATHS["TCWWW_URL"] = PATHS["TCWWW"]

if getenv("PUBLICWWW"):
    PATHS["PUBLICWWW"] = getenv("PUBLICWWW").rstrip("/")
else:
    PATHS["PUBLICWWW"] = pathjoin(PATHS["GEOIPS_OUTDIRS"], "preprocessed", "publicwww")

if getenv("PUBLICWWW_URL"):
    PATHS["PUBLICWWW_URL"] = getenv("PUBLICWWW_URL").rstrip("/")
else:
    PATHS["PUBLICWWW_URL"] = PATHS["PUBLICWWW"]

if getenv("PRIVATEWWW"):
    PATHS["PRIVATEWWW"] = getenv("PRIVATEWWW").rstrip("/")
else:
    PATHS["PRIVATEWWW"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "preprocessed", "privatewww"
    )

if getenv("PRIVATEWWW_URL"):
    PATHS["PRIVATEWWW_URL"] = getenv("PRIVATEWWW_URL").rstrip("/")
else:
    PATHS["PRIVATEWWW_URL"] = PATHS["PRIVATEWWW"]

PATHS["TC_DECKS_DB"] = pathjoin(
    PATHS["GEOIPS_OUTDIRS"], "longterm_files", "tc", "tc_decks.db"
)
if getenv("TC_DECKS_DB"):
    PATHS["TC_DECKS_DB"] = getenv("TC_DECKS_DB")

if getenv("TC_DECKS_DIR"):
    PATHS["TC_DECKS_DIR"] = getenv("TC_DECKS_DIR").rstrip("/")
else:
    PATHS["TC_DECKS_DIR"] = pathjoin(
        PATHS["GEOIPS_OUTDIRS"], "longterm_files", "tc", "decks"
    )


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
    from os import makedirs

    if not exists(path):
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
