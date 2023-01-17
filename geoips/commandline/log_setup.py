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

"""Geoips module for setting up logging handlers with a specified verbosity."""
import logging
import sys


def setup_logging(verbose=True):
    """Set up logging handler.

    If you do this the first time with no argument, it sets up the logging
    for all submodules. Subsequently, in submodules, you can just do
    LOG = logging.getLogger(__name__)
    """
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s %(module)12s%(lineno)4d%(levelname)7s: %(message)s", "%d_%H%M%S"
    )
    if not verbose:
        fmt = logging.Formatter("%(asctime)s: %(message)s", "%d_%H%M%S")
    stream_hndlr = logging.StreamHandler(sys.stdout)
    stream_hndlr.setFormatter(fmt)
    stream_hndlr.setLevel(logging.INFO)
    log.addHandler(stream_hndlr)
    return log
