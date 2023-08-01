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
    from os.path import dirname as pathdirname
    from glob import glob

    if filenames is None:
        filenames = glob(pathjoin(TC_DECKS_DIR, "*"))

    updated_files = []
    cc, conn = open_tc_db()

    # We might want to rearrange this so we don't open up every file...
    # Check timestamps first.
    for filename in filenames:
        updated_files += update_fields(filename, cc, conn, process=process)

    cc.execute("SELECT * FROM tc_trackfiles")
    # data = cc.fetchall()
    conn.close()
    # return data
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
    if not re.compile("G\D\D\d\d\d\d\d\d\.\d\d\d\d\d\d\d\d\d\d.dat").match(
        pathbasename(tc_trackfilename)
    ) and not re.compile("G\D\D\d\d\d\d\d\d\.dat").match(
        pathbasename(tc_trackfilename)
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
        database_timestamp = datetime.strptime(
            cc.execute(
                "SELECT last_updated from tc_trackfiles WHERE filename = ?",
                (tc_trackfilename,),
            ).fetchone()[0],
            "%Y-%m-%d %H:%M:%S.%f",
        )
        if file_timestamp < database_timestamp:
            LOG.info("")
            LOG.info(
                "%s already in %s and up to date, not doing anything",
                tc_trackfilename,
                TC_DECKS_DB,
            )
            return []

    lines = open(tc_trackfilename, "r").readlines()
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
        LOG.info("")
        LOG.info(
            "Updating start/end datetime and last_updated fields for "
            + tc_trackfilename
            + " in "
            + TC_DECKS_DB
        )
        old_start_datetime, old_end_datetime, old_vmax = cc.execute(
            "SELECT start_datetime,end_datetime,vmax from tc_trackfiles WHERE filename = ?",
            (tc_trackfilename,),
        ).fetchone()
        # Eventually add in storm_start_datetime
        # old_storm_start_datetime,old_start_datetime,old_end_datetime,old_vmax = cc.execute("SELECT storm_start_datetime,start_datetime,end_datetime,vmax from tc_trackfiles WHERE filename = ?", (tc_trackfilename,)).fetchone()
        if old_start_datetime == start_datetime.strftime("%Y-%m-%d %H:%M:%S"):
            LOG.info("    UNCHANGED start_datetime: " + old_start_datetime)
        else:
            LOG.info(
                "    Old start_datetime: "
                + old_start_datetime
                + " to new: "
                + start_datetime.strftime("%Y-%m-%d %H:%M:%S")
            )
            updated_files += [tc_trackfilename]
        # if old_storm_start_datetime == storm_start_datetime.strftime('%Y-%m-%d %H:%M:%S'):
        #    LOG.info('    UNCHANGED storm_start_datetime: '+old_storm_start_datetime)
        # else:
        #    LOG.info('    Old storm_start_datetime: '+old_storm_start_datetime+' to new: '+storm_start_datetime.strftime('%Y-%m-%d %H:%M:%S'))
        if old_end_datetime == end_datetime.strftime("%Y-%m-%d %H:%M:%S"):
            LOG.info("    UNCHANGED end_datetime: " + old_end_datetime)
        else:
            LOG.info(
                "    Old end_datetime: "
                + old_end_datetime
                + " to new: "
                + end_datetime.strftime("%Y-%m-%d %H:%M:%S")
            )
            updated_files += [tc_trackfilename]
        if database_timestamp == file_timestamp:
            LOG.info(
                "    UNCHANGED last_updated: "
                + database_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            LOG.info(
                "    Old last_updated: "
                + database_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                + " to new: "
                + file_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
            updated_files += [tc_trackfilename]
        if old_vmax == vmax:
            LOG.info("    UNCHANGED vmax: " + str(old_vmax))
        else:
            LOG.info("    Old vmax: " + str(old_vmax) + " to new: " + str(vmax))
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

    start_lat = start_line[6]
    start_lon = start_line[7]
    storm_basin = start_line[0]
    storm_num = start_line[1]
    try:
        start_name = start_line[48] + start_line[49]
    except IndexError:
        start_name = start_line[41]

    if data == None:
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
        LOG.info("    Adding " + tc_trackfilename + " to " + TC_DECKS_DB)
        updated_files += [tc_trackfilename]
        conn.commit()

        # This ONLY runs if it is a brand new storm file and we requested
        # processing.
        if process:
            reprocess_storm(tc_trackfilename)
    return updated_files


def reprocess_storm(tc_trackfilename):
    """Reprocess storm tc_trackfilename, using info in TC tracks database."""
    # from IPython import embed as shell; shell()

    datelist = [startdt.strftime("%Y%m%d")]
    for nn in range((enddt - startdt).days + 2):
        datelist += [(startdt + timedelta(nn)).strftime("%Y%m%d")]

    hourlist = []
    for ii in range(24):
        hourlist += [(enddt - timedelta(hours=ii)).strftime("%H")]
    hourlist.sort()
    # Do newest first
    datelist.sort(reverse=True)

    for sat, sensor in [
        ("gcom-w1", "amsr2"),
        ("gpm", "gmi"),
        ("npp", "viirs"),
        ("jpss-1", "viirs"),
        ("aqua", "modis"),
        ("terra", "modis"),
        ("himawari-8", "ahi"),
        ("goes-16", "abi"),
        ("goes-17", "abi"),
    ]:
        for datestr in datelist:
            process_overpass(
                sat,
                sensor,
                productlist=None,
                sectorlist=[startstormsect.name],
                sectorfiles=None,
                extra_dirs=None,
                sector_file=sector_file,
                datelist=[datestr],
                hourlist=hourlist,
                queue=os.getenv("DEFAULT_QUEUE"),
                mp_max_cpus=3,
                allstatic=False,
                alldynamic=True,
                # list=True will just list files and not actually run
                # list=True,
                list=False,
                quiet=True,
                start_datetime=startdt,
                end_datetime=enddt,
            )
    # shell()


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
            LOG.info("Deck file does not exist! %s", deck_filename)
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
    # return None if no storm matched
    return return_area_defs
