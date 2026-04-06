# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Parser for dyanmic volcanoes csv files."""

import logging

import pandas as pd

LOG = logging.getLogger(__name__)

interface = "sector_metadata_generators"
family = "volc"
name = "volc_parser"


def call(trackfile_name):
    """Parse a sample volcano csv file.

    Parameters
    ----------
    trackfile_name: str, or path
        * Path to trackfile csv file with the format:
        * columns: lat lon time
        * lat/lon format: decimal
        * time format: YYYYMMDDTHHMM
    """
    csv_parser = pd.read_csv(trackfile_name)

    all_fields = []

    for i in csv_parser.iterrows():
        tmp_fields = i[1]
        fields = {}

        fields["clat"] = tmp_fields["Lat"]
        fields["clon"] = tmp_fields["Lon"]
        fields["time"] = pd.to_datetime(tmp_fields["Time"]).to_pydatetime()
        all_fields.append(fields)

    volcano_name = tmp_fields["Name"]
    if "volcano" not in volcano_name.lower():
        volcano_name = volcano_name.upper() + "_VOLCANO"
    return all_fields, volcano_name, fields["time"].strftime("%Y"), "BEST"
