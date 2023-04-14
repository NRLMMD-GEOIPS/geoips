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

"""Simple script to validate a list of plugins provided command line."""

from sys import argv
import logging
from geoips.schema import validate

LOG = logging.getLogger(__name__)


def main():
    """Validate list of plugins passed command line."""
    for plugin_path in argv[1:]:
        LOG.info("Testing {plugin_path}...")
        validate(argv[1])


if __name__ == "__main__":
    main()
