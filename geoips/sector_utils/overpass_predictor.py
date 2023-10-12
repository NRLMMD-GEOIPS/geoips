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

"""Overpass predictor, based on Two Line Element files."""

# Standard libraries
from datetime import timedelta
import math

# Installed libraries
import ephem
from pyresample import spherical_geometry

from logging import getLogger

LOG = getLogger()


def check_tle_name_to_passed_names(tle_name, satellite_names_list):
    """Check if the satellite name in the TLE files is in the satellite names list.

    Satellite names in the TLE files may be longer than the names passed to the
    overpass predictor For example, a user might request 'GCOM-W1', and the name
    in the TLE file is 'GCOM-W1 (SHIZUKU)'.

    Parameters
    ----------
    tle_name : str
        satellite name read from the TLE file
    satellite_names_list : list of str
        list of user specified satellites to read from TLE file

    Returns
    -------
    bool
        True if tle_name is in the passed satellite names list
    """
    satellite_in_list = any(
        [x.lower() in tle_name.lower() for x in satellite_names_list]
    )
    return satellite_in_list


def read_satellite_tle(tlefile, satellite_list):
    """Open and extract satellite infromation from TLE file.

    Parameters
    ----------
    tlefile : str
        file path of TLE
    satellite_list : list of str
        list of satellites to read from TLE

    Returns
    -------
    dict
        satellite TLE data
    """
    with open(tlefile, "r") as tfile:
        tle_content = tfile.readlines()
    satellite_tles = {}
    for i, line in enumerate(tle_content):
        if line[0] in ["1", "2"]:
            continue
        satellite = line.strip()
        if check_tle_name_to_passed_names(satellite, satellite_list):
            line1 = tle_content[i + 1].strip()
            line2 = tle_content[i + 2].strip()
            clean_name = satellite.split(" (")[0]
            satellite_tles[clean_name] = {"line1": line1, "line2": line2}
    return satellite_tles


def floor_minute(datetime_obj):
    """Remove seconds and microseconds from datetime object.

    Parameters
    ----------
    datetime_obj : datetime.datetime
        datetime

    Returns
    -------
    datetime.datetime
        datetime with no seconds/microseconds
    """
    second = datetime_obj.second
    micro = datetime_obj.microsecond
    return datetime_obj - timedelta(seconds=second, microseconds=micro)


def calculate_overpass(tle, observer_lat, observer_lon, date, satellite_name):
    """Calculate next overpass for a satellite at an observer location and time.

    Parameters
    ----------
    tle : ephem.EarthSatellite
        tle for satellite
    observer_lat : float
        observer latitude
    observer_lon : float
        observer longitude
    date : datetime.datetime
        start time for next overpass
    satellite_name : str
        name of satellite

    Returns
    -------
    dict
        next overpass information
    """
    sector = ephem.Observer()
    sector.lon = str(observer_lon)
    sector.lat = str(observer_lat)
    sector.date = date.strftime("%Y/%m/%d %H:%M:%S")
    sector.elevation = 0.0
    moon = ephem.Moon()
    sun = ephem.Sun()
    moon.compute(sector)
    sun.compute(sector)
    if not sun.rise_time:
        LOG.info(
            "%s:Something went wrong when calculating sun rise time for %s!",
            satellite_name,
            date,
        )
        return None
    if not sun.set_time:
        LOG.info(
            "%s:Something went wrong when calculating sun set time for %s!",
            satellite_name,
            date,
        )
        return None
    sunrise = sun.rise_time.datetime()
    sunset = sun.set_time.datetime()
    if sunset <= sunrise:
        sunset += timedelta(days=1)
    opass_info = {
        "check datetime": date,
        "sunrise": sunrise,
        "sunset": sunset,
        "moon phase": moon.phase,
    }
    try:
        opass = sector.next_pass(tle)
        is_geostationary = False
        max_alt_time = floor_minute(opass[2].datetime())
        opass_info["rise time"] = floor_minute(opass[0].datetime())
        opass_info["max altitude time"] = max_alt_time
        opass_info["max altitude"] = opass[3]
        opass_info["set time"] = floor_minute(opass[4].datetime())
        opass_info["is daytime"] = (max_alt_time >= sunrise) & (max_alt_time < sunset)
        opass_info["is geostationary"] = False
    except ValueError as resp:
        if "circumpolar" in str(resp):
            is_geostationary = True
            is_above_horizon = True
        else:
            # LOG.info(resp)
            return None
        opass_info["rise time"] = date
        opass_info["max altitude time"] = date
        opass_info["max altitude"] = date
        opass_info["set time"] = date
        opass_info["is geostationary"] = is_geostationary
        opass_info["above horizon"] = is_above_horizon
        opass_info["is daytime"] = (date >= sunrise) & (date < sunset)
    except AttributeError as resp:
        LOG.info(
            "%s: Something when wrong with calculating the next overpass for %s "
            "(AttributeError)",
            satellite_name,
            date,
        )
        LOG.debug(resp)
        return None
    except TypeError as resp:
        LOG.info(
            "%s: Something when wrong with calculating the next overpass for %s "
            "(TypeError)",
            satellite_name,
            date,
        )
        LOG.debug(resp)
        return None
    if is_geostationary:
        tle.compute(sector)
    else:
        tle.compute(opass_info["max altitude time"])
    opass_info["sublon"] = math.degrees(tle.sublong)
    opass_info["sublat"] = math.degrees(tle.sublat)
    ptsatdeg = spherical_geometry.Coordinate(
        lon=opass_info["sublon"], lat=opass_info["sublat"]
    )
    ptsecdeg = spherical_geometry.Coordinate(
        lon=math.degrees(sector.lon), lat=math.degrees(sector.lat)
    )
    earth_radius_km = 6730.0
    cpa_km = ptsatdeg.distance(ptsecdeg) * earth_radius_km
    opass_info["closest pass approach (km)"] = cpa_km
    return opass_info


def predict_satellite_overpass(
    tlefile,
    satellite_name,
    satellite_tle,
    area_def,
    start_datetime,
    check_midpoints=False,
):
    """Estimate next satellite overpass information with ephem.

    Parameters
    ----------
    tlefile : str
        file path of TLE
    satellite_name : str
        name of satellite
    satellite_tle : dict
        dictionary holding satellite tle line1 and line2 data
    area_def : pyresample AreaDefinition
        area definition
    start_datetime :datetime.datetime
        start time to find the next available overpass
    check_midpoints :bool
        check mid points of area definition for additional overpassses

    Returns
    -------
    dict
        dictionary holding next overpass information
    """
    tle = ephem.readtle(tlefile, satellite_tle["line1"], satellite_tle["line2"])
    ll_lon, ll_lat, ur_lon, ur_lat = area_def.area_extent_ll
    center_lon = (ll_lon + ur_lon) / 2.0
    center_lat = (ll_lat + ur_lat) / 2.0
    observers = [(center_lat, center_lon)]
    if check_midpoints:
        mid_lon_upper = (center_lon + ur_lon) / 2.0
        mid_lon_lower = (center_lon + ll_lon) / 2.0
        mid_lat_upper = (center_lat + ur_lat) / 2.0
        mid_lat_lower = (center_lat + ll_lat) / 2.0
        observers.append((mid_lat_upper, center_lon))
        observers.append((mid_lat_lower, center_lon))
        observers.append((center_lat, mid_lon_upper))
        observers.append((center_lat, mid_lon_lower))
    overpasses = {}
    rise_times = []
    valid_overpasses = 0
    for i, observer in enumerate(observers):
        observer_lat, observer_lon = observer
        opass_info = calculate_overpass(
            tle, observer_lat, observer_lon, start_datetime, satellite_name
        )
        if isinstance(opass_info, type(None)):
            # Either something went wrong in the predictor, or found a
            # geostationary satellite that does not overpass the sector, ever!
            overpasses = None
            continue
        if i < 1:
            # Keep track of center rise set times
            center_rise = opass_info["rise time"]
            center_set = opass_info["set time"]
            valid_overpasses += 1
            overpasses["pass {0}".format(valid_overpasses)] = opass_info
        # Only add if overpass does not intersect
        # with the sector's center observer point
        max_t = opass_info["max altitude time"]
        if (max_t < center_rise) or (max_t > center_set):
            rise_times.append(opass_info["rise time"])
            valid_overpasses += 1
            overpasses["pass {0}".format(valid_overpasses)] = opass_info
    return overpasses


def predict_overpass_area_def(
    tlefile, area_definition, satellite_list, start_datetime, check_midpoints=False
):
    """Predict satellite overpass for an area_definition.

    Parameters
    ----------
    tlefile : str
        file path of TLE
    area_definition : pyresample AreaDefinition
        pyresample area definition
    satellite_list : list
        list of satellites to predict the overpass times
    start_datetime : datetime.datetime
        start time to find the next available overpass
    check_midpoints : bool
        check mid points of area definition for additional overpassses

    Returns
    -------
    dict
        dictionary holding next satellite overpass estimates
        (sorted by satellite -> overpass info)
    """
    if not isinstance(satellite_list, list):
        raise TypeError("satellite_list must be type list")
    area_def_overpasses = {}
    satellite_tle_dict = read_satellite_tle(tlefile, satellite_list)
    for satellite, sat_tle in satellite_tle_dict.items():
        next_overpass = predict_satellite_overpass(
            tlefile,
            satellite,
            sat_tle,
            area_definition,
            start_datetime,
            check_midpoints=check_midpoints,
        )
        if next_overpass:
            area_def_overpasses[satellite] = next_overpass
    return area_def_overpasses


def predict_overpass_yaml(
    tlefile,
    sectorfile,
    sector_list,
    satellite_list,
    start_datetime,
    check_midpoints=False,
):
    """Predict satellite overpass for sectors from a given yaml sector file.

    Parameters
    ----------
    tlefile : str
        file path of TLE
    sectorfile  : str
        file path of sectorfile
    sector_list : list
        list of sectors held within the sectorfile
    satellite_list : list
        list of satellites to predict the overpass times
    start_datetime : datetime.datetime
        start time to find the next available overpass
    check_midpoints : bool
        check mid points of area definition for additional overpassses

    Returns
    -------
    dict
        dictionary holding next satellite overpass estimates for sectors
        (sorted by sector -> satellite -> overpass info)
    """
    from geoips.sector_utils.utils import create_areadefinition_from_yaml

    if not isinstance(satellite_list, list):
        raise TypeError("satellite_list must be type list")
    sector_overpasses = {}
    for yaml_sector in sector_list:
        sector_area_def = create_areadefinition_from_yaml(sectorfile, yaml_sector)
        overpasses = predict_overpass_area_def(
            tlefile,
            sector_area_def,
            satellite_list,
            start_datetime,
            check_midpoints=check_midpoints,
        )
        sector_overpasses[yaml_sector] = overpasses
    return sector_overpasses
