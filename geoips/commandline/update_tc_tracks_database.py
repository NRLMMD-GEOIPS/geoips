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

"""Command line script for updating the TC database."""


def main():
    """Update TC tracks database via command line."""
    import sys
    from geoips.commandline.log_setup import setup_logging

    LOG = setup_logging()
    from geoips.sector_utils.tc_tracks_database import check_db

    if len(sys.argv) > 2:
        LOG.info("Calling with arg %s", sys.argv[1:])
        check_db(sys.argv[1:])
    else:
        check_db()


if __name__ == "__main__":
    main()
