# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""TC trackfile parser for flat text sectorfiles containing current active storms.

These files contain no storm history, only the currently active storm locations.
Potentially useful for real-time processing.

10S JOSHUA 210120 1200 21.8S 78.1E SHEM 20 1007
12S ELOISE 210120 1800 15.6S 44.9E SHEM 35 1001
92S INVEST 210120 1800 14.9S 120.8E SHEM 30 1002
93S INVEST 210120 1800 12.6S 98.5E SHEM 30 1003
"""
import logging

LOG = logging.getLogger(__name__)

interface = "sector_metadata_generators"
family = "tc"
name = "tc_sector_file_parser"


def call(trackfile_name):
    """TC trackfile parser for flat text sectorfiles containing current active storms.

    These files contain no storm history, only the currently active storm locations.
    Potentially useful for real-time processing.

    Parameters
    ----------
    trackfile_name : str
        Flat text sector file name containing all currently active storm locations,
        formatted as follows:
        * 10S JOSHUA 210120 1200 21.8S 78.1E SHEM 20 1007
        * 12S ELOISE 210120 1800 15.6S 44.9E SHEM 35 1001
        * 92S INVEST 210120 1800 14.9S 120.8E SHEM 30 1002
        * 93S INVEST 210120 1800 12.6S 98.5E SHEM 30 1003

    Returns
    -------
    list
        List of Dictionaries of storm metadata fields from each storm location
        in the flat text sector file

    See Also
    --------
    :ref:`api`
        Valid fields can be found in geoips.sector_utils.utils.SECTOR_INFO_ATTRS
    """
    # These flat text sectorfiles contain all storms -
    # no overall final_storm_name or tc_year
    final_storm_name = None
    tc_year = None

    flatsf_lines = open(trackfile_name).readlines()
    all_fields = []

    for line in flatsf_lines:
        if not line.strip():
            continue
        curr_fields = parse_flat_sectorfile_line(
            line, trackfile_name, parser_name="flat_sectorfile_parser"
        )
        # Was previously RE-SETTING finalstormname here.
        # That is why we were getting incorrect final_storm_name fields
        all_fields += [curr_fields]
    return all_fields, final_storm_name, tc_year


def parse_flat_sectorfile_line(
    line, source_filename, parser_name="flat_sectorfile_parser"
):
    """Retrieve the storm information from the current line from the deck file.

    Parameters
    ----------
    line : str
        Current line from the deck file including all storm information
        * 10S JOSHUA 210120 1200 21.8S 78.1E SHEM 20 1007

    Returns
    -------
    dict
        Dictionary of the fields from the current storm location from the deck file

    See Also
    --------
    :ref:`api`
        Valid fields can be found in geoips.sector_utils.utils.SECTOR_INFO_ATTRS
    """
    from datetime import datetime

    parts = [part.strip() for part in line.split()]
    LOG.info(len(parts))
    if len(parts) < 8:
        raise ValueError(
            "Incorrectly formatted flat text sectorfile - fewer than 8 fields"
        )

    basin_ids = {
        "L": "AL",
        "Q": "SL",
        "A": "IO",
        "B": "IO",
        "S": "SH",
        "P": "SH",
        "C": "CP",
        "E": "EP",
        "W": "WP",
    }

    fields = {}
    # 10S JOSHUA 210120 1200 21.8S 78.1E SHEM 20 1007
    fields["deck_line"] = line.strip()
    fields["storm_basin"] = basin_ids[parts[0][-1]]
    fields["storm_num"] = int(parts[0][:-1])
    fields["synoptic_time"] = datetime.strptime(parts[2] + parts[3], "%y%m%d%H%M")
    fields["aid_type"] = "BEST"
    fields["clat"] = NSEW_to_float(parts[4])
    fields["clon"] = NSEW_to_float(parts[5])
    fields["vmax"] = float(parts[7])
    fields["pressure"] = float(parts[8])

    fields["storm_name"] = parts[1]
    fields["final_storm_name"] = fields["storm_name"]
    fields["storm_year"] = get_storm_year(
        fields["storm_basin"],
        current_month=int(parts[2][2:4]),
        current_year=int("20" + parts[2][0:2]),
    )
    fields["parser"] = parser_name
    fields["source_filename"] = source_filename

    return fields


def NSEW_to_float(lat_lon_val):
    """Convert lat/lon values with NSEW identifiers to positive or negative floats.

    Parameters
    ----------
    lat_lon_val : str
        Latitude or longitude value as a string,
        with hemisphere specified by NSEW identifiers

    Returns
    -------
    float
        Latitude or Longitude value as a float.
    """
    if "S" in lat_lon_val or "W" in lat_lon_val:
        lat_lon_val = -float(lat_lon_val.replace("S", "").replace("W", ""))
    else:
        lat_lon_val = float(lat_lon_val.replace("N", "").replace("E", ""))

    return lat_lon_val


def get_storm_year(storm_basin, current_month, current_year):
    """Ensure correct storm_year is applied.

    For Southern Hemisphere storms that initiate late in the year,
    the storm year identifier is for the following year.

    Parameters
    ----------
    storm_basin : str
        basin of current storm, one of SH, AL, EP, CP, WP, IO
    current_month : int
        Current month of storm location
    current_year : int
        Current year of storm location

    Returns
    -------
    int
        Storm year identifier. current year, unless SH storm later than June,
        then current year + 1
    """
    storm_year = current_year
    if storm_basin == "SH" and current_month > 6:
        storm_year = current_year + 1
    return storm_year
