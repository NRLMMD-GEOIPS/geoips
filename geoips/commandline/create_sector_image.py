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

"""Produce PNG test images depicting defined GeoIPS sectors."""

import os

from geoips import interfaces
from geoips.commandline.log_setup import setup_logging
from geoips.commandline.args import get_command_line_args, check_command_line_args


def main():
    """Produce PNG test images depicting defined GeoIPS sectors."""
    supported_args = ["logging_level", "sector_list", "outdir"]

    # Use standard GeoIPS argparser - use standard formatting for standard args.
    ARGS = get_command_line_args(
        arglist=supported_args,
        description="Produce PNG test images depicting defined GeoIPS sectors.",
    )

    # Get the dictionary of command line args.
    COMMAND_LINE_ARGS = ARGS.__dict__
    # Check included arguments for appropriate formatting / type.
    check_command_line_args(supported_args, COMMAND_LINE_ARGS)

    # Setup logging at the requested logging level.
    LOG = setup_logging(logging_level=COMMAND_LINE_ARGS["logging_level"])

    # For this console script, sector_list is explicitly required.
    if not COMMAND_LINE_ARGS["sector_list"]:
        raise TypeError("Must pass list of sectors")

    # Create an image for each requested sector, including just the
    # map and white background.
    for sector_name in COMMAND_LINE_ARGS["sector_list"]:
        fname = os.path.join(COMMAND_LINE_ARGS["outdir"], f"{sector_name}.png")
        sect = interfaces.sectors.get_plugin(sector_name)
        LOG.interactive(f"Creating {fname}")
        sect.create_test_plot(fname)


if __name__ == "__main__":
    main()
