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
from geoips.commandline.log_setup import setup_logging
from geoips.schema import validate


def main():
    """Validate list of plugins passed command line."""

    LOG = setup_logging()
    failed_plugins = []
    successful_plugins = []
    for plugin_path in argv[1:]:
        LOG.info(f"Testing {plugin_path}...")
        try:
            validate(argv[1])
            successful_plugins += [f"SUCCESS {plugin_path}: correctly validated"]
        except Exception as resp:
            failed_plugins += [f"FAIL {plugin_path}: did not validate"]
            LOG.exception(str(resp))

    print("")
    for failed_plugin in failed_plugins:
        LOG.error(failed_plugin)
    print("")
    for successful_plugin in successful_plugins:
        LOG.info(successful_plugin)
    print("")


if __name__ == "__main__":
    main()
