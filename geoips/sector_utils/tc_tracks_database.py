# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utilities for creating a database of tropical cyclone tracks."""

from geoips.filenames.base_paths import PATHS as gpaths
import logging

import sqlite3

LOG = logging.getLogger(__name__)

TC_DECKS_DB = gpaths["TC_DECKS_DB"]
TC_DECKS_DIR = gpaths["TC_DECKS_DIR"]


def open_tc_db(dbname=TC_DECKS_DB):
    """Open the TC Decks Database, create it if it doesn't exist."""
    # Make sure the directory exists.  If the db doesn't exist,
    # the sqlite3.connect command will create it - which will
    # fail if the directory doesn't exist.
    from os.path import dirname as pathdirname
    from geoips.filenames.base_paths import make_dirs

    make_dirs(pathdirname(dbname))

    conn = sqlite3.connect(dbname)
    LOG.interactive("Opening tc db: %s", dbname)
    conn_cursor = conn.cursor()
    # Try to create the table - if it already exists, it will just fail
    # trying to create, pass, and return the already opened db.
    try:
        conn_cursor.execute(
            """CREATE TABLE tc_trackfiles
            (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                filename text,
                last_updated timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                storm_num integer,
                storm_basin text,
                start_datetime timestamp,
                start_lat real,
                start_lon real,
                start_vmax real,
                start_name real,
                vmax real,
                end_datetime timestamp)"""
        )
        # Add in at some point?
        # storm_start_datetime timestamp,
    except sqlite3.OperationalError:
        pass
    return conn_cursor, conn


def check_db(filenames=None, process=False):
    """Check TC database for passed filenames.

    filenames is a list of filenames and directories. if a list element is a
    string directory name, it expands to list of files in dir.
    """
    from os.path import join as pathjoin
    from glob import glob

    if filenames is None:
        filenames = glob(pathjoin(TC_DECKS_DIR, "*"))

    updated_files = []
    cc, conn = open_tc_db()

    # We might want to rearrange this so we don't open up every file...
    # Check timestamps first.
    for filename in filenames:
        try:
            updated_files += update_fields(filename, cc, conn, process=process)
        except IndexError:
            LOG.warning("Failed parsing %s", filename)
            continue

    cc.execute("SELECT * FROM tc_trackfiles")
    # data = cc.fetchall()
    conn.close()
    # return data
    LOG.interactive("%s updated storms", len(updated_files))
    return updated_files


def update_fields(tc_trackfilename, cc, conn, process=False):
    """Update fields in TC track database with passed tc_trackfilename."""
    # Must be of form similar to
    # Gal912016.dat

    import re
    from datetime import datetime, timedelta
    from os.path import basename as pathbasename
    from os import stat as osstat

    updated_files = []

    LOG.info("Checking " + tc_trackfilename + " ... process " + str(process))

    # Check if we match Gxxdddddd.dat filename format.
    # If not just return and don't do anything.
    if (
        not re.compile(r"G\D\D\d\d\d\d\d\d\.\d\d\d\d\d\d\d\d\d\d.dat").match(
            pathbasename(tc_trackfilename)
        )
        and not re.compile(r"G\D\D\d\d\d\d\d\d\.dat").match(
            pathbasename(tc_trackfilename)
        )
        and not re.compile(r"b\D\D\d\d\d\d\d\d\.\d\d\d\d\d\d\d\d\d\d.dat").match(
            pathbasename(tc_trackfilename)
        )
        and not re.compile(r"b\D\D\d\d\d\d\d\d\.dat").match(
            pathbasename(tc_trackfilename)
        )
    ):
        LOG.info("")
        LOG.warning(
            "    DID NOT MATCH REQUIRED FILENAME FORMAT, SKIPPING: %s", tc_trackfilename
        )
        return []

    # Get all fields for the database entry for the current filename
    cc.execute("SELECT * FROM tc_trackfiles WHERE filename = ?", (tc_trackfilename,))
    data = cc.fetchone()

    file_timestamp = datetime.fromtimestamp(osstat(tc_trackfilename).st_mtime)
    # Reads timestamp out as string - convert to datetime object.
    # Check if timestamp on file is newer than timestamp in database -
    # if not, just return and don't do anything.
    if data:
        try:
            database_timestamp = datetime.strptime(
                cc.execute(
                    "SELECT last_updated from tc_trackfiles WHERE filename = ?",
                    (tc_trackfilename,),
                ).fetchone()[0],
                "%Y-%m-%d %H:%M:%S.%f",
            )
        except ValueError as resp:
            LOG.exception(f"Failed on {tc_trackfilename}")
            raise (ValueError(f"FAILED ON {tc_trackfilename}: {resp}"))
        if file_timestamp < database_timestamp:
            LOG.info("")
            LOG.interactive(
                "%s already in %s and up to date, not doing anything",
                tc_trackfilename,
                TC_DECKS_DB,
            )
            return []

    lines = open(tc_trackfilename, "r").readlines()
    # Remove any whitespace from the loaded deck file lines - otherwise will fail
    # parsing datetime information downstream
    lines = [x.replace(" ", "") for x in lines]
    start_line = lines[0].split(",")
    # Start 24h prior to start in sectorfile, for initial processing
    # storm_start_datetime = datetime.strptime(start_line[2],'%Y%m%d%H')
    start_datetime = datetime.strptime(start_line[2], "%Y%m%d%H") - timedelta(hours=24)
    end_datetime = datetime.strptime(lines[-1].split(",")[2], "%Y%m%d%H")
    start_vmax = start_line[8]
    vmax = 0
    for line in lines:
        currv = line.split(",")[8]
        track = line.split(",")[4]
        if currv and track == "BEST" and float(currv) > vmax:
            vmax = float(currv)

    if data and database_timestamp < file_timestamp:
        LOG.interactive("")
        LOG.interactive(
            "Updating start/end datetime and last_updated fields for "
            + tc_trackfilename
            + " in "
            + TC_DECKS_DB
        )
        old_start_datetime, old_end_datetime, old_vmax = cc.execute(
            "SELECT start_datetime,end_datetime,vmax from tc_trackfiles WHERE "
            "filename = ?",
            (tc_trackfilename,),
        ).fetchone()
        # Eventually add in storm_start_datetime
        # old_storm_start_datetime,old_start_datetime,old_end_datetime,old_vmax =
        #   cc.execute("SELECT storm_start_datetime,start_datetime,end_datetime,vmax
        #   from tc_trackfiles WHERE filename = ?", (tc_trackfilename,)).fetchone()
        if old_start_datetime == start_datetime.strftime("%Y-%m-%d %H:%M:%S"):
            LOG.interactive("    UNCHANGED start_datetime: " + old_start_datetime)
        else:
            LOG.interactive(
                "    Old start_datetime: "
                + old_start_datetime
                + " to new: "
                + start_datetime.strftime("%Y-%m-%d %H:%M:%S")
            )
            updated_files += [tc_trackfilename]
        # if old_storm_start_datetime ==
        #                            storm_start_datetime.strftime('%Y-%m-%d %H:%M:%S'):
        #    LOG.info('    UNCHANGED storm_start_datetime: '+old_storm_start_datetime)
        # else:
        #    LOG.info('    Old storm_start_datetime: '+old_storm_start_datetime+' to
        #              new: '+storm_start_datetime.strftime('%Y-%m-%d %H:%M:%S'))
        if old_end_datetime == end_datetime.strftime("%Y-%m-%d %H:%M:%S"):
            LOG.interactive("    UNCHANGED end_datetime: " + old_end_datetime)
        else:
            LOG.interactive(
                "    Old end_datetime: "
                + old_end_datetime
                + " to new: "
                + end_datetime.strftime("%Y-%m-%d %H:%M:%S")
            )
            updated_files += [tc_trackfilename]
        if database_timestamp == file_timestamp:
            LOG.interactive(
                "    UNCHANGED last_updated: "
                + database_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            LOG.interactive(
                "    Old last_updated: "
                + database_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                + " to new: "
                + file_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
            updated_files += [tc_trackfilename]
        if old_vmax == vmax:
            LOG.interactive("    UNCHANGED vmax: " + str(old_vmax))
        else:
            LOG.interactive("    Old vmax: " + str(old_vmax) + " to new: " + str(vmax))
            updated_files += [tc_trackfilename]
        cc.execute(
            """UPDATE tc_trackfiles SET
                        last_updated=?,
                        start_datetime=?,
                        end_datetime=?,
                        vmax=?
                      WHERE filename = ?""",
            # Eventually add in ?
            # storm_start_datetime=?,
            (
                file_timestamp,
                # storm_start_datetime,
                start_datetime,
                end_datetime,
                str(vmax),
                tc_trackfilename,
            ),
        )
        conn.commit()
        return updated_files

    start_lat = start_line[6].replace("N", "")
    if "S" in start_lat:
        start_lat = "-" + start_lat.replace("S", "")
    start_lon = start_line[7].replace("E", "")
    if "W" in start_lon:
        start_lon = "-" + start_lon.replace("W", "")
    storm_basin = start_line[0]
    storm_num = start_line[1]
    if re.compile(r"b\D\D\d\d\d\d\d\d\.dat").match(
        pathbasename(tc_trackfilename)
    ) or re.compile(r"b\D\D\d\d\d\d\d\d\.\d\d\d\d\d\d\d\d\d\d.dat").match(
        pathbasename(tc_trackfilename)
    ):
        # For the most part, b-deck files line up fairly with G-deck files, but the
        # index of the start name is wildly different. I almost wonder if we should
        # use the b-deck parser to grab all this information, but this is hopefully
        # good enough
        start_name = start_line[27]
    else:
        # Keep the old logic for parsing the start_name out of the G-deck files
        try:
            start_name = start_line[48] + start_line[49]
        except IndexError:
            start_name = start_line[41]

    if data is None:
        # print '    Adding '+tc_trackfilename+' to '+TC_DECKS_DB
        cc.execute(
            """insert into tc_trackfiles(
                        filename,
                        last_updated,
                        vmax,
                        storm_num,
                        storm_basin,
                        start_datetime,
                        start_lat,
                        start_lon,
                        start_vmax,
                        start_name,
                        end_datetime) values(?, ?,?, ?,?,?,?,?,?,?,?)""",
            # Eventually add in ?
            # end_datetime) values(?, ?, ?,?, ?,?,?,?,?,?,?,?)''',
            # storm_start_datetime,
            (
                tc_trackfilename,
                file_timestamp,
                str(vmax),
                storm_num,
                storm_basin,
                # storm_start_datetime,
                start_datetime,
                start_lat,
                start_lon,
                start_vmax,
                start_name,
                end_datetime,
            ),
        )
        LOG.info("")
        LOG.interactive("    Adding " + tc_trackfilename + " to " + TC_DECKS_DB)
        updated_files += [tc_trackfilename]
        conn.commit()

        # This ONLY runs if it is a brand new storm file and we requested
        # processing. Not used right now -- includes errors.
        # if process:
        #     reprocess_storm(tc_trackfilename)
    return updated_files


# The function below was commented out as it included errors, and is not used by GeoIPS
# at this time. 9/27/23

# def reprocess_storm(tc_trackfilename):
#     """Reprocess storm tc_trackfilename, using info in TC tracks database."""
#     datelist = [startdt.strftime("%Y%m%d")]
#     for nn in range((enddt - startdt).days + 2):
#         datelist += [(startdt + timedelta(nn)).strftime("%Y%m%d")]

#     hourlist = []
#     for ii in range(24):
#         hourlist += [(enddt - timedelta(hours=ii)).strftime("%H")]
#     hourlist.sort()
#     # Do newest first
#     datelist.sort(reverse=True)

#     for sat, sensor in [
#         ("gcom-w1", "amsr2"),
#         ("gpm", "gmi"),
#         ("npp", "viirs"),
#         ("jpss-1", "viirs"),
#         ("aqua", "modis"),
#         ("terra", "modis"),
#         ("himawari-8", "ahi"),
#         ("goes-16", "abi"),
#         ("goes-17", "abi"),
#     ]:
#         for datestr in datelist:
#             process_overpass(
#                 sat,
#                 sensor,
#                 productlist=None,
#                 sectorlist=[startstormsect.name],
#                 sectorfiles=None,
#                 extra_dirs=None,
#                 sector_file=sector_file,
#                 datelist=[datestr],
#                 hourlist=hourlist,
#                 queue=os.getenv("DEFAULT_QUEUE"),
#                 mp_max_cpus=3,
#                 allstatic=False,
#                 alldynamic=True,
#                 # list=True will just list files and not actually run
#                 # list=True,
#                 list=False,
#                 quiet=True,
#                 start_datetime=startdt,
#                 end_datetime=enddt,
#             )


def get_all_storms_from_db(
    start_datetime,
    end_datetime,
    tc_spec_template=None,
    trackfile_parser=None,
    include_track_files=False,
):
    """Get all entries from all storms within a specific range of time from the TC DB.

    Parameters
    ----------
    start_datetime : datetime.datetime
        Start time of desired range
    end_datetime : datetime.datetime
        End time of desired range

    Returns
    -------
    list of pyresample Area Definitions
        List of pyresample Area Definitions, each storm location that falls
        within the desired time range.

    Examples
    --------
    >>> startdt = datetime.strptime('20200216', '%Y%m%d')
    >>> enddt = datetime.strptime('20200217', '%Y%m%d')
    >>> get_storm_from_db(startdt, enddt)
    """
    from os.path import exists as path_exists

    return_area_defs = []
    connection_cursor, connection = open_tc_db()
    LOG.interactive(
        "Getting all storms from tcdb from '%s' to '%s'",
        start_datetime,
        end_datetime,
    )
    LOG.info("connection: %s", connection)
    try:
        connection_cursor.execute(
            """SELECT filename from tc_trackfiles WHERE
                                     end_datetime >= ?
                                     AND start_datetime <= ?""",
            (start_datetime, end_datetime),
        )
    except sqlite3.InterfaceError as resp:
        LOG.exception(f"{resp} error getting fields from database, return empty list")
        return return_area_defs
    deck_filenames = connection_cursor.fetchall()
    from geoips.sector_utils.tc_tracks import trackfile_to_area_defs

    for deck_filename in deck_filenames:
        if deck_filename is not None:
            # Is a tuple
            (deck_filename,) = deck_filename
        LOG.info("deck_filename %s", deck_filename)
        if not path_exists(deck_filename):
            LOG.warning("Deck file does not exist! %s", deck_filename)
            continue
        area_defs = trackfile_to_area_defs(
            deck_filename,
            trackfile_parser=trackfile_parser,
            tc_spec_template=tc_spec_template,
        )
        for area_def in area_defs:
            if (
                area_def.sector_start_datetime > start_datetime
                and area_def.sector_start_datetime < end_datetime
            ):
                if include_track_files:
                    return_area_defs += [(area_def, deck_filename)]
                else:
                    return_area_defs += [area_def]
    LOG.interactive("%s storms found in time range in tcdb!", len(return_area_defs))
    # return None if no storm matched
    return return_area_defs
