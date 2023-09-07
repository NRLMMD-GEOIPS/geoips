"""Produce PNG test images depicting defined GeoIPS sectors."""

import os
import argparse
from geoips import interfaces


def main():
    """Produce PNG test images depicting defined GeoIPS sectors."""
    parser = argparse.ArgumentParser(
        description="Produce PNG test images depicting defined GeoIPS sectors."
    )
    parser.add_argument("sectors", nargs="+", help="A list of sector names.")
    parser.add_argument("-o", "--outdir", default=".")

    args = parser.parse_args()

    for sector_name in args.sectors:
        fname = os.path.join(args.outdir, f"{sector_name}.png")
        sect = interfaces.sectors.get_plugin(sector_name)
        print(f"Creating {fname}")
        sect.create_test_plot(fname)


if __name__ == "__main__":
    main()
