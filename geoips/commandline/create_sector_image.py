"""Produce PNG test images depicting defined GeoIPS sectors."""

import os
import argparse
from geoips import interfaces
from geoips.commandline.log_setup import setup_logging


def main():
    """Produce PNG test images depicting defined GeoIPS sectors."""
    "logging_level", "sector_list"

    parser = argparse.ArgumentParser(
        description="Produce PNG test images depicting defined GeoIPS sectors."
    )
    parser.add_argument(
        "-l",
        "--logging_level",
        choices=["INTERACTIVE", "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"],
        default="INTERACTIVE",
        help="""Specify logging config level for GeoIPS run_procflow command.""",
        type=str.upper,
    )
    parser.add_argument(
        "-s",
        "--sector_list",
        nargs="*",
        default=None,
        help="""A list of short sector plugin names found within YAML sectorfiles
                over which the data file should be processed.""",
    )
    parser.add_argument("-o", "--outdir", default=".")

    args = parser.parse_args()

    LOG = setup_logging(logging_level="INFO")

    for sector_name in args.sector_list:
        fname = os.path.join(args.outdir, f"{sector_name}.png")
        sect = interfaces.sectors.get_plugin(sector_name)
        LOG.info(f"Creating {fname}")
        sect.create_test_plot(fname)


if __name__ == "__main__":
    main()
