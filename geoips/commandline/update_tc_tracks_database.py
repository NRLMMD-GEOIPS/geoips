# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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
