# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""TC trackfile parser for B-Deck formatted TC deck files.

Each B-Deck file contains the full history of storm BEST tracks, on storm per
location per line (split between 3 lines each in comments for readability)::

  AL, 20, 2020091318,   , BEST,   0, 126N,  374W,  30, 1006, TD,   0,    ,    0,
      0,    0,    0, 1011,  240, 100,  40,   0,   L,   0,    ,   0,   0,
           TWENTY, M, 12, NEQ,   60,    0,    0,   60, genesis-num, 039,
  AL, 20, 2020091400,   , BEST,   0, 130N,  386W,  30, 1006, TD,   0,    ,    0,
          0,    0,    0, 1011,  240, 100,  40,   0,   L,   0,    ,   0,   0,
           TWENTY, M, 12, NEQ,   60,   60,    0,    0, genesis-num, 039,
  AL, 20, 2020091406,   , BEST,   0, 130N,  404W,  35, 1004, TS,  34, NEQ,    0,
          0,   40,   40, 1011,  240,  40,   0,   0,   L,   0,    ,   0,   0,
            TEDDY, M,  0,    ,    0,    0,    0,    0, genesis-num, 039,
  AL, 20, 2020091412,   , BEST,   0, 128N,  422W,  35, 1004, TS,  34, NEQ,   50,
         30,    0,   50, 1011,  240,  40,  45,   0,   L,   0,    ,   0,   0,
            TEDDY, M,  0,    ,    0,    0,    0,    0, genesis-num, 039,
  AL, 20, 2020091418,   , BEST,   0, 129N,  434W,  40, 1003, TS,  34, NEQ,   80,
         40,    0,   70, 1012,  210,  50,  55,   0,   L,   0,    ,   0,   0,
            TEDDY, M, 12, NEQ,   90,   30,    0,   30, genesis-num, 039,
  AL, 20, 2020091500,   , BEST,   0, 130N,  445W,  45, 1002, TS,  34, NEQ,  100,
         50,    0,   80, 1012,  210,  40,  55,   0,   L,   0,    ,   0,   0,
            TEDDY, M, 12, NEQ,   90,   30,    0,   30, genesis-num, 039,
  AL, 20, 2020091506,   , BEST,   0, 134N,  455W,  50, 1001, TS,  34, NEQ,  100,
         50,   20,   80, 1012,  210,  20,  60,   0,   L,   0,    ,   0,   0,
            TEDDY, M, 12, NEQ,  300,  210,   30,    0, genesis-num, 039,
  AL, 20, 2020091506,   , BEST,   0, 134N,  455W,  50, 1001, TS,  50, NEQ,   20,
          0,    0,    0, 1012,  210,  20,  60,   0,   L,   0,    ,   0,   0,
            TEDDY, M, 12, NEQ,  300,  210,   30,    0, genesis-num, 039,
  AL, 20, 2020091512,   , BEST,   0, 138N,  466W,  55,  999, TS,  34, NEQ,  140,
     60,   40,  160, 1011,  250,  20,  65,   0,   L,   0,    ,   0,   0,
        TEDDY, D, 12, NEQ,  300,  210,   30,   30, genesis-num, 039,
  AL, 20, 2020091512,   , BEST,   0, 138N,  466W,  55,  999, TS,  50, NEQ,   30,
      0,    0,   30, 1011,  250,  20,  65,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  210,   30,   30, genesis-num, 039,
  AL, 20, 2020091518,   , BEST,   0, 142N,  475W,  55,  997, TS,  34, NEQ,  140,
     80,   40,  160, 1011,  250,  20,  65,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  240,   60,   60, genesis-num, 039,
  AL, 20, 2020091518,   , BEST,   0, 142N,  475W,  55,  997, TS,  50, NEQ,   30,
      0,    0,   30, 1011,  250,  20,  65,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  240,   60,   60, genesis-num, 039,
  AL, 20, 2020091600,   , BEST,   0, 147N,  480W,  65,  987, HU,  34, NEQ,  140,
     80,   40,  150, 1010,  180,  20,  75,   0,   L,   0,    ,   0,   0,
            TEDDY, D,  0,    ,    0,    0,    0,    0, genesis-num, 039,
  AL, 20, 2020091600,   , BEST,   0, 147N,  480W,  65,  987, HU,  50, NEQ,   40,
     30,    0,   30, 1010,  180,  20,  75,   0,   L,   0,    ,   0,   0,
            TEDDY, D,  0,    ,    0,    0,    0,    0, genesis-num, 039,
  AL, 20, 2020091600,   , BEST,   0, 147N,  480W,  65,  987, HU,  64, NEQ,   20,
      0,    0,    0, 1010,  180,  20,  75,   0,   L,   0,    ,   0,   0,
            TEDDY, D,  0,    ,    0,    0,    0,    0, genesis-num, 039,
  AL, 20, 2020091606,   , BEST,   0, 154N,  486W,  80,  978, HU,  34, NEQ,  140,
     80,   40,  150, 1010,  180,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  240,  120,  150, genesis-num, 039,
  AL, 20, 2020091606,   , BEST,   0, 154N,  486W,  80,  978, HU,  50, NEQ,   40,
     30,   20,   30, 1010,  180,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  240,  120,  150, genesis-num, 039,
  AL, 20, 2020091606,   , BEST,   0, 154N,  486W,  80,  978, HU,  64, NEQ,   20,
     10,   10,   20, 1010,  180,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  240,  120,  150, genesis-num, 039,
  AL, 20, 2020091612,   , BEST,   0, 161N,  493W,  85,  973, HU,  34, NEQ,  170,
    170,   40,  150, 1010,  180,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  270,  270,  240,  270, genesis-num, 039,
  AL, 20, 2020091612,   , BEST,   0, 161N,  493W,  85,  973, HU,  50, NEQ,   50,
     50,   20,   30, 1010,  180,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  270,  270,  240,  270, genesis-num, 039,
  AL, 20, 2020091612,   , BEST,   0, 161N,  493W,  85,  973, HU,  64, NEQ,   25,
     25,   10,   20, 1010,  180,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  270,  270,  240,  270, genesis-num, 039,
  AL, 20, 2020091618,   , BEST,   0, 168N,  502W,  85,  973, HU,  34, NEQ,  190,
    100,   70,  170, 1010,  180,  20, 105,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  300,  240,  300, genesis-num, 039,
  AL, 20, 2020091618,   , BEST,   0, 168N,  502W,  85,  973, HU,  50, NEQ,   80,
     50,   30,   90, 1010,  180,  20, 105,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  300,  240,  300, genesis-num, 039,
  AL, 20, 2020091618,   , BEST,   0, 168N,  502W,  85,  973, HU,  64, NEQ,   30,
     25,    0,   30, 1010,  180,  20, 105,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  300,  300,  240,  300, genesis-num, 039,
  AL, 20, 2020091700,   , BEST,   0, 174N,  511W,  85,  973, HU,  34, NEQ,  220,
    100,   80,  170, 1009,  210,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  330,  300,  270,  300, genesis-num, 039,
  AL, 20, 2020091700,   , BEST,   0, 174N,  511W,  85,  973, HU,  50, NEQ,   60,
     50,   50,   70, 1009,  210,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  330,  300,  270,  300, genesis-num, 039,
  AL, 20, 2020091700,   , BEST,   0, 174N,  511W,  85,  973, HU,  64, NEQ,   30,
     25,   20,   30, 1009,  210,  20, 100,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  330,  300,  270,  300, genesis-num, 039,
  AL, 20, 2020091706,   , BEST,   0, 180N,  520W,  85,  973, HU,  34, NEQ,  220,
    100,   80,  170, 1009,  210,  20, 105,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  330,  360,  300,  300, genesis-num, 039,
  AL, 20, 2020091706,   , BEST,   0, 180N,  520W,  85,  973, HU,  50, NEQ,   60,
     50,   50,   70, 1009,  210,  20, 105,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  330,  360,  300,  300, genesis-num, 039,
  AL, 20, 2020091706,   , BEST,   0, 180N,  520W,  85,  973, HU,  64, NEQ,   30,
     25,   20,   30, 1009,  210,  20, 105,   0,   L,   0,    ,   0,   0,
            TEDDY, D, 12, NEQ,  330,  360,  300,  300, genesis-num, 039,
"""
import os
import logging
from datetime import datetime, timezone

LOG = logging.getLogger(__name__)

interface = "sector_metadata_generators"
family = "tc"
name = "bdeck_parser"


def call(trackfile_name):
    """TC deckfile parser for B-Deck files.

    Each B-Deck file contains the full history of storm BEST tracks, one storm
    location per line. Example b-deck files are available in the GeoIPS repo.

    Parameters
    ----------
    trackfile_name : str
        Path to bdeck file, with full 6 hourly storm track
        history, formatted as follows:

    Returns
    -------
    list
        List of Dictionaries of storm metadata fields from each storm location

    See Also
    --------
    :ref:`api`
        Valid fields can be found in geoips.sector_utils.utils.SECTOR_INFO_ATTRS
    """
    LOG.info("STARTING getting fields from %s", trackfile_name)
    # Must get tcyear out of the filename in case a storm
    # crosses TC vs calendar years.
    # tcyear = os.path.basename(trackfile_name)[5:9]
    tc_year = get_stormyear_from_bdeck_filename(trackfile_name)
    # print tcyear

    flatsf_lines = open(trackfile_name).readlines()
    final_storm_name = get_final_storm_name_bdeck(flatsf_lines, tc_year, trackfile_name)
    invest_number = get_invest_number_bdeck(flatsf_lines)

    # This just pulls the time of the first entry in the deck file
    entry_storm_start_datetime = get_storm_start_datetime_from_bdeck_entry(flatsf_lines)

    # Note storms are often started with 3 locations, and the first 2 locations
    # are removed in later deck files, so initial storm start time often does
    # not match the final storm start time.
    # Keep track of the start datetime referenced in the filename
    filename_storm_start_datetime = get_storm_start_datetime_from_bdeck_filename(
        trackfile_name
    )

    LOG.info("  USING final_storm_name from bdeck %s", final_storm_name)
    LOG.info("  USING storm_start_datetime from bdeck %s", entry_storm_start_datetime)
    LOG.info(
        "  USING original_storm_start_datetime from bdeck %s",
        filename_storm_start_datetime,
    )

    # flatsf_lines go from OLDEST to NEWEST (so firsttime is the OLDEST
    # storm location)
    all_fields = []

    for line in flatsf_lines:
        curr_fields = parse_bdeck_line(
            line,
            source_filename=trackfile_name,
            storm_year=tc_year,
            final_storm_name=final_storm_name,
            invest_number=invest_number,
            storm_start_datetime=entry_storm_start_datetime,
            original_storm_start_datetime=filename_storm_start_datetime,
            parser_name="bdeck_parser",
        )
        # Was previously RE-SETTING finalstormname here.
        # That is why we were getting incorrect final_storm_name fields
        all_fields += [curr_fields]

    LOG.info("FINISHED getting fields from %s", trackfile_name)

    return all_fields, final_storm_name, tc_year


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


def parse_bdeck_line(
    line,
    source_filename=None,
    storm_year=None,
    final_storm_name=None,
    invest_number=None,
    storm_start_datetime=None,
    original_storm_start_datetime=None,
    parser_name="bdeck_parser",
):
    """Retrieve the storm information from the current line from the deck file.

    Parameters
    ----------
    line : str
        Current line from the deck file including all storm information

        * AL, 20, 2020091618,   , BEST,   0, 168N,  502W,  85,  973, HU,  64,
          NEQ,   30,   25,    0,   30, 1010,  180,  20, 105,   0,   L,   0,    ,
          0,   0,      TEDDY, D, 12, NEQ,  300,  300,  240,  300,
          genesis-num, 039,
        * AL, 20, 2020091700,   , BEST,   0, 174N,  511W,  85,  973, HU,  34,
          NEQ,  220,  100,   80,  170, 1009,  210,  20, 100,   0,   L,   0,    ,
          0,   0,      TEDDY, D, 12, NEQ,  330,  300,  270,  300,
          genesis-num, 039,
        * AL, 20, 2020091700,   , BEST,   0, 174N,  511W,  85,  973, HU,  50,
          NEQ,   60,   50,   50,   70, 1009,  210,  20, 100,   0,   L,   0,    ,
          0,   0,      TEDDY, D, 12, NEQ,  330,  300,  270,  300,
          genesis-num, 039,

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
    # Need separate parser for B decks (best tracks)
    # parts = line.split(',', 40)
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != 38 and len(parts) != 30 and len(parts) != 40 and len(parts) != 42:
        LOG.interactive(source_filename)
        LOG.interactive(line)
        raise ValueError(
            "Incorrectly formatted deck file - "
            "must have either 30 or 38 or 42 fields, "
            f"had {len(parts)}",
        )
    fields = {}
    fields["deck_line"] = line.strip()
    fields["storm_basin"] = parts[0]
    fields["storm_num"] = int(parts[1])
    synoptic_time = datetime.strptime(parts[2], "%Y%m%d%H")
    fields["synoptic_time"] = synoptic_time.replace(tzinfo=timezone.utc)

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

    fields["storm_name"] = parts[27]
    fields["final_storm_name"] = "unknown"
    if final_storm_name:
        LOG.debug("USING passed final_storm_name %s", final_storm_name)
        fields["final_storm_name"] = final_storm_name
    else:
        LOG.debug("USING storm_name as final_storm_name %s", fields["storm_name"])
        fields["final_storm_name"] = fields["storm_name"]
    if storm_year:
        fields["storm_year"] = storm_year
    if parts[-3] == "TRANSITIONED":
        # shB02021
        invest_id = parts[-2].split(" ")[0]
        invest_year = invest_id[4:]
        invest_basin = invest_id[0:2]
        invest_num = "9" + invest_id[3]
        # tc2021sh90invest
        fields["invest_storm_id"] = (
            "tc" + invest_year + invest_basin + invest_num + "invest"
        )
    fields["invest_number"] = None

    if invest_number:
        fields["invest_number"] = invest_number

    if source_filename:
        from geoips.geoips_utils import replace_geoips_paths

        if isinstance(source_filename, str):
            fields["source_filename"] = replace_geoips_paths(source_filename)
        else:
            fields["source_filename"] = source_filename
    fields["parser_name"] = parser_name
    return fields


def get_invest_number_bdeck(deck_lines):
    """Get invest number from full bdeck file."""
    invest_number = None
    for line in deck_lines:
        fields = parse_bdeck_line(line)
        if fields["storm_name"] == "INVEST" and fields["storm_num"] > 89:
            invest_number = fields["storm_num"]
        if "invest_storm_id" in fields:
            invest_number = int(fields["invest_storm_id"][8:10])
    return invest_number


def get_storm_start_datetime_from_bdeck_entry(deck_lines):
    """Get storm start datetime from full bdeck file."""
    # Return the synoptic time of the first bdeck entry
    fields = parse_bdeck_line(deck_lines[0])
    LOG.info("  GETTING storm start time from bdeck entry %s", fields["synoptic_time"])
    return fields["synoptic_time"]


def get_storm_start_datetime_from_bdeck_filename(bdeck_filename):
    """Get storm start datetime from bdeck file name."""
    # Return the synoptic time found in the actual filename, if it exists!
    # This will ONLY be the case for INVESTS, which can use the start
    # Gwp912022.2022101400.dat
    bdeck_parts = os.path.basename(bdeck_filename).split(".")
    storm_start_datetime = None
    if len(bdeck_parts) > 2:
        try:
            storm_start_datetime = datetime.strptime(bdeck_parts[1], "%Y%m%d%H")
            storm_start_datetime = storm_start_datetime.replace(tzinfo=timezone.utc)
            LOG.info(
                "  USING storm start time found in filename %s", storm_start_datetime
            )
        except ValueError:
            LOG.warning(
                "  SKIPPING no valid storm start time found in filename, %s",
                "using first entry in bdeck",
            )
            storm_start_datetime = None
    return storm_start_datetime


def get_stormyear_from_bdeck_filename(bdeck_filename):
    """Get the storm year from the B-deck filename.

    Parameters
    ----------
    bdeck_filename : str
        * Path to deck file to search for storm year
        * Must be of format: xxxxxYYYY.dat - pulls YYYY from filename based on
          location

    Returns
    -------
    int
        Storm year
    """
    return int(os.path.basename(bdeck_filename)[5:9])


def get_final_storm_name_bdeck(deck_lines, tcyear, trackfile_name=None):
    """Get final storm name from full bdeck file."""
    final_storm_name = "INVEST"
    for line in deck_lines:
        # curr_fields = parse_bdeck_line(line, tcyear, finalstormname)
        curr_fields = parse_bdeck_line(
            line,
            storm_year=tcyear,
            final_storm_name=final_storm_name,
            source_filename=trackfile_name,
        )
        # if curr_fields['storm_name']:
        if curr_fields["storm_name"] and curr_fields["storm_name"] != "INVEST":
            LOG.debug("UPDATING final_storm_name to %s", curr_fields["storm_name"])
            final_storm_name = curr_fields["storm_name"]
    return final_storm_name
