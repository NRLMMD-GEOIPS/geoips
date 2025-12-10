# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""TC trackfile parser for F-Deck formatted TC deck files.

Each F-Deck file contains the current, official forecast for a storm. One storm
location per line (split between 2 lines in comments below for readability)::
Format is very similar to B-Deck file but line length is smaller

  AL, 99, 2023082312, 03, OFCL,   0, 187N,  651W,  25,    0, TD,  34, NEQ,
   0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 300,  13,
  AL, 99, 2023082312, 03, OFCL,   3, 188N,  658W,  25, 1009, TD,  34, NEQ,
   0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 285,  13,
  AL, 99, 2023082312, 03, OFCL,  12, 190N,  678W,  25,    0, LO,  34, NEQ,
   0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 275,  13,
  AL, 99, 2023082312, 03, OFCL,  24, 191N,  692W,  25,    0, LO,  34, NEQ,
   0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 270,  16,
  AL, 99, 2023082312, 03, OFCL,  36, 193N,  714W,  25,    0, LO,  34, NEQ,
   0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 270,  16,

or

  WP, 17, 2023111306, 03, JTWC,   0,  81N, 1390E,  25,    0, TD,  34, NEQ,
   0,    0,    0,    0,
  WP, 17, 2023111306, 03, JTWC,  12,  78N, 1386E,  25,    0, TD,  34, NEQ,
   0,    0,    0,    0,
  WP, 17, 2023111306, 03, JTWC,  24,  79N, 1380E,  25,    0, TD,  34, NEQ,
   0,    0,    0,    0,
  WP, 17, 2023111306, 03, JTWC,  36,  80N, 1371E,  30,    0, TD,  34, NEQ,
   0,    0,    0,    0,
  WP, 17, 2023111306, 03, JTWC,  48,  82N, 1356E,  30,    0, TD,  34, NEQ,
   0,    0,    0,    0,
  WP, 17, 2023111306, 03, JTWC,  72,  89N, 1326E,  35,    0, TS,  34, NEQ,
   60,   30,   50,   70,
  WP, 17, 2023111306, 03, JTWC,  96, 101N, 1289E,  40,    0, TS,  34, NEQ,
   70,   70,   50,   80,    0,    0,   0,  50,   0,
  WP, 17, 2023111306, 03, JTWC, 120, 113N, 1257E,  45,    0, TS,  34, NEQ,
   100,  120,   90,  120,    0,    0,   0,  55,   0,

"""
import os
import logging
from datetime import datetime, timedelta

LOG = logging.getLogger(__name__)

interface = "sector_metadata_generators"
family = "tc"
name = "fdeck_parser"


def call(trackfile_name, allowed_aid_types=None):
    """TC deckfile parser for F-Deck files.

    Each F-Deck file contains the full history of storm BEST tracks, one storm
    location per line. Example b-deck files are available in the GeoIPS repo.

    Parameters
    ----------
    trackfile_name : str
        Path to fdeck file, with full 6 hourly storm track
        history, formatted as follows:
    allowed_aid_type : list
        List of allowed aid types. Defaults to ["ANAL", "JTWC", "OFCL"] if None

    Returns
    -------
    list
        List of Dictionaries of storm metadata fields from each storm location

    See Also
    --------
    :ref:`api`
        Valid fields can be found in geoips.sector_utils.utils.SECTOR_INFO_ATTRS
    """
    if allowed_aid_types is None:
        allowed_aid_types = ["ANAL", "JTWC", "OFCL"]
    LOG.info("STARTING getting fields from %s", trackfile_name)
    # Must get tcyear out of the filename in case a storm
    # crosses TC vs calendar years.
    # tcyear = os.path.basename(trackfile_name)[5:9]
    tc_year = get_stormyear_from_fdeck_filename(trackfile_name)
    # print tcyear

    flatsf_lines = open(trackfile_name).readlines()
    final_storm_name = get_final_storm_name_fdeck(flatsf_lines, tc_year)
    invest_number = get_invest_number_fdeck(flatsf_lines)

    # This just pulls the time of the first entry in the deck file
    entry_storm_start_datetime = get_storm_start_datetime_from_fdeck_entry(flatsf_lines)

    # Note storms are often started with 3 locations, and the first 2 locations
    # are removed in later deck files, so initial storm start time often does
    # not match the final storm start time.
    # Keep track of the start datetime referenced in the filename
    filename_storm_start_datetime = entry_storm_start_datetime
    # filename_storm_start_datetime = get_storm_start_datetime_from_fdeck_filename( #TLO
    #    trackfile_name  #TLO
    # )  #TLO

    LOG.info("  USING final_storm_name from fdeck %s", final_storm_name)
    LOG.info("  USING storm_start_datetime from fdeck %s", entry_storm_start_datetime)
    LOG.info(
        "  USING original_storm_start_datetime from fdeck %s",
        filename_storm_start_datetime,
    )

    # flatsf_lines go from OLDEST to NEWEST (so firsttime is the OLDEST
    # storm location)
    all_fields = []

    for line in flatsf_lines:
        curr_fields = parse_fdeck_line(
            line,
            source_filename=trackfile_name,
            storm_year=tc_year,
            final_storm_name=final_storm_name,
            invest_number=invest_number,
            storm_start_datetime=entry_storm_start_datetime,
            original_storm_start_datetime=filename_storm_start_datetime,
            parser_name="fdeck_parser",
        )
        # Was previously RE-SETTING finalstormname here.
        # That is why we were getting incorrect final_storm_name fields
        all_fields += [curr_fields]

    LOG.info("FINISHED getting fields from %s", trackfile_name)

    return all_fields, final_storm_name, tc_year, allowed_aid_types


def lat_to_dec(lat_str):
    """Return decimal latitude based on N/S specified string."""
    latnodec = lat_str
    latdec = latnodec[:-2] + "." + latnodec[-2:]
    latdecsign = latdec[:-1] if (latdec[-1] == "N") else "-" + latdec[:-1]
    return latdecsign


def lon_to_dec(lon_str):
    """Return decimal longitude based on E/W specified string."""
    lonnodec = lon_str
    londec = lonnodec[:-2] + "." + lonnodec[-2:]
    londecsign = londec[:-1] if (londec[-1] == "E") else "-" + londec[:-1]
    return londecsign


def parse_fdeck_line(
    line,
    source_filename=None,
    storm_year=None,
    final_storm_name=None,
    invest_number=None,
    storm_start_datetime=None,
    original_storm_start_datetime=None,
    parser_name="fdeck_parser",
):
    """Retrieve the storm information from the current line from the deck file.

    Parameters
    ----------
    line : str
        Current line from the deck file including all storm information
        AL, 99, 2023082312, 03, OFCL,   0, 187N,  651W,  25,    0, TD,  34, NEQ,
        0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 300,  13,
        AL, 99, 2023082312, 03, OFCL,   3, 188N,  658W,  25, 1009, TD,  34, NEQ,
        0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 285,  13,
        AL, 99, 2023082312, 03, OFCL,  12, 190N,  678W,  25,    0, LO,  34, NEQ,
        0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 275,  13,
        AL, 99, 2023082312, 03, OFCL,  24, 191N,  692W,  25,    0, LO,  34, NEQ,
        0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 270,  16,
        AL, 99, 2023082312, 03, OFCL,  36, 193N,  714W,  25,    0, LO,  34, NEQ,
        0,    0,    0,    0,    0,    0,   0,  35,   0,    ,   0, ASL, 270,  16,

    Returns
    -------
    dict
        Dictionary of the fields from the current storm location from the
        deck file

    See Also
    --------
    :ref:`api`
        Valid fields can be found in geoips.sector_utils.utils.SECTOR_INFO_ATTRS
    """
    # This works with G (GeoIPS) Deck files.
    # Need separate parser for F decks (forecast files)
    # parts = line.split(',', 40)
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != 18 and len(parts) != 23 and len(parts) != 28 and len(parts) != 36:
        raise ValueError(
            "Incorrectly formatted f-deck file - must have either 28 or 36 fields"
        )
    # if len(parts) != 38 and len(parts) != 30 and len(parts) != 40 and
    # len(parts) != 42:
    #    raise ValueError(
    #        "Incorrectly formatted deck file - must have either 30 or 38 or 42 fields"
    #    )
    fields = {}
    fields["deck_line"] = line.strip()
    fields["storm_basin"] = parts[0]
    fields["storm_num"] = int(parts[1])
    fdatetime = datetime.strptime(parts[2], "%Y%m%d%H")
    fields["aid_type"] = parts[
        4
    ]  # BEST, MBAM, OFCL, JTWC, etc - BEST202101220600 when updated
    # CARQ - not best track, real time, A-deck (Aids), F (Fix), E (Error), B (Best)
    fcsttime = int(parts[5])
    fields["synoptic_time"] = fdatetime + timedelta(hours=fcsttime)
    # fields["synoptic_time"] = datetime.strptime(parts[2], "%Y%m%d%H")

    if isinstance(storm_start_datetime, datetime):
        fields["storm_start_datetime"] = storm_start_datetime
    if isinstance(original_storm_start_datetime, datetime):
        fields["original_storm_start_datetime"] = original_storm_start_datetime

    fields["aid_type"] = parts[
        4
    ]  # BEST, MBAM, OFCL, JTWC, etc - BEST202101220600 when updated
    # CARQ - not best track, real time, A-deck (Aids), F (Fix), E (Error), B (Best)
    fields["clat"] = float(lat_to_dec(parts[6]))
    fields["clon"] = float(lon_to_dec(parts[7]))
    fields["vmax"] = parts[8]
    if fields["vmax"]:
        fields["vmax"] = float(fields["vmax"])
    fields["pressure"] = parts[9]
    if fields["pressure"]:
        fields["pressure"] = float(fields["pressure"])

    fields["storm_name"] = "STORM" + parts[1]  # TLO
    # fields["storm_name"] = parts[27] #TLO
    fields["final_storm_name"] = "unknown"
    fields["invest_storm_name"] = "unknown"  # TLO

    storm_id = parts[2].split(" ")[0]  # TLO
    storm_year = storm_id[0:4]  # TLO
    storm_basin = parts[0]  # TLO
    storm_num = parts[1]  # TLO
    fields["storm_year"] = storm_year  # TLO

    if int(parts[1]) > 89:  # TLO
        fields["final_storm_id"] = (
            "tc" + storm_year + storm_basin + storm_num + "invest"
        )  # TLO
        fields["invest_storm_name"] = "INVEST" + storm_num  # TLO
        fields["invest_number"] = storm_num  # TLO
    else:  # TLO
        fields["final_storm_id"] = "tc" + storm_year + storm_basin + storm_num  # TLO
        fields["final_storm_name"] = "STORM" + storm_num  # TLO

    if source_filename:
        from geoips.geoips_utils import replace_geoips_paths

        if isinstance(source_filename, str):
            fields["source_filename"] = replace_geoips_paths(source_filename)
        else:
            fields["source_filename"] = source_filename
    fields["parser_name"] = parser_name
    print("fields=", fields)
    return fields


def get_invest_number_fdeck(deck_lines):
    """Get invest number from full fdeck file."""
    invest_number = None
    for line in deck_lines:
        fields = parse_fdeck_line(line)
        if fields["storm_num"] > 89:
            invest_number = fields["storm_num"]
    return invest_number


def get_storm_start_datetime_from_fdeck_entry(deck_lines):
    """Get storm start datetime from full fdeck file."""
    # Return the synoptic time of the first fdeck entry
    fields = parse_fdeck_line(deck_lines[0])
    LOG.info("  GETTING storm start time from fdeck entry %s", fields["synoptic_time"])
    return fields["synoptic_time"]


def get_storm_start_datetime_from_fdeck_filename(fdeck_filename):
    """Get storm start datetime from fdeck file name."""
    # Return the synoptic time found in the actual filename, if it exists!
    # This will ONLY be the case for INVESTS, which can use the start
    # Gwp912022.2022101400.dat
    fdeck_parts = os.path.basename(fdeck_filename).split(".")
    storm_start_datetime = None
    if len(fdeck_parts) > 2:
        try:
            storm_start_datetime = datetime.strptime(fdeck_parts[1], "%Y%m%d%H")
            LOG.info(
                "  USING storm start time found in filename %s", storm_start_datetime
            )
        except ValueError:
            LOG.warning(
                "  SKIPPING no valid storm start time found in filename, %s",
                "using first entry in fdeck",
            )
            storm_start_datetime = None
    return storm_start_datetime


def get_stormyear_from_fdeck_filename(fdeck_filename):
    """Get the storm year from the F-deck filename.

    Parameters
    ----------
    fdeck_filename : str
        * Path to deck file to search for storm year
        * Must be of format: xxxxxYYYY.dat - pulls YYYY from filename based on
          location

    Returns
    -------
    int
        Storm year
    """
    return int(os.path.basename(fdeck_filename)[5:9])


def get_final_storm_name_fdeck(deck_lines, tcyear):
    """Get final storm name from full fdeck file."""
    final_storm_name = "INVEST"
    for line in deck_lines:
        # curr_fields = parse_fdeck_line(line, tcyear, finalstormname)
        curr_fields = parse_fdeck_line(line, tcyear, final_storm_name)
        # if curr_fields['storm_name']:
        if curr_fields["storm_name"] and curr_fields["storm_name"] != "INVEST":
            LOG.debug("UPDATING final_storm_name to %s", curr_fields["storm_name"])
            final_storm_name = curr_fields["storm_name"]
    return final_storm_name
