# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Overpass predictor, based on Two Line Element files."""

# Standard libraries
from datetime import timedelta
import math
from numpy import linspace

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


def create_sector_observers(ll_lon, ll_lat, ur_lon, ur_lat, spacing=50):
    """Create multiple prediction points for large sectors.

    Parameters
    ----------
    ll_lon : float
        Lower left longitude of sector.
    ll_lat : float
        Lower left latitude of sector.
    ur_lon : float
        Upper right longtitude of sector.
    ur_lat : float
        Upper right latitude of sector.
    spacing : int, optional
        Spacing between latitude/longitude observer points (degrees), by default 50

    Returns
    -------
    list
        List of observer points for sector.
    """
    if ur_lon < ll_lon:
        # Check if sector crosses dateline.
        # Convert lons to 0 - 360 just to make things easier.
        ur_lon = 360 + ur_lon
    # Find how wide and tall the sector is
    lon_delta = abs((ur_lon - spacing) - (ll_lon - spacing))
    lat_delta = abs((ur_lat - spacing) - (ll_lat - spacing))
    # Determine how many observers we'd expect for this sector.
    n_lat_points = round(round(lat_delta) / spacing)
    n_lon_points = round(round(lon_delta) / spacing)
    # Create list of latitude observer points.
    # Only try to create multiple observers if the expected
    # number of observers is greater than one.
    if n_lat_points > 1:
        check_lats = linspace(ll_lat + spacing / 2, ur_lat - spacing / 2, n_lat_points)
    else:
        check_lats = [(ur_lat + ll_lat) / 2]
    # Create list of longitude observer points.
    # Only try to create multiple observers if the expected
    # number of observers is greater than one.
    if n_lon_points > 1:
        check_lons = linspace(ll_lon + spacing / 2, ur_lon - spacing / 2, n_lon_points)
        # Convert back to -180 - 180
        check_lons[check_lons > 180] -= 360
    else:
        center_lon = (ur_lon + ll_lon) / 2
        if center_lon > 180:
            # Convert lons back to -180 - 180
            center_lon -= 360
        check_lons = [center_lon]
    check_points = []
    for clat in check_lats:
        for clon in check_lons:
            check_points.append([clat, clon])
    return check_points


def predict_satellite_overpass(
    tlefile,
    satellite_name,
    satellite_tle,
    area_def,
    start_datetime,
    observer_spacing=50,
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
    observer_spacing : float
        Spacing (degrees) between observer points in sector. If domain exceeds the
        specified spacing, multiple observer are automatically added across the sector.

    Returns
    -------
    dict
        dictionary holding next overpass information
    """
    tle = ephem.readtle(tlefile, satellite_tle["line1"], satellite_tle["line2"])
    ll_lon, ll_lat, ur_lon, ur_lat = area_def.area_extent_ll
    observers = create_sector_observers(
        ll_lon, ll_lat, ur_lon, ur_lat, spacing=observer_spacing
    )
    total_observers = len(observers)
    overpasses = {}
    LOG.info(
        "Running %s overpass predictor for %s. Total observers: %s",
        satellite_name,
        area_def.area_id,
        total_observers,
    )
    for i, observer in enumerate(observers):
        observer_lat, observer_lon = observer
        opass_info = calculate_overpass(
            tle, observer_lat, observer_lon, start_datetime, satellite_name
        )
        if isinstance(opass_info, type(None)):
            # Either something went wrong in the predictor, or found a
            # geostationary satellite that does not overpass the sector, ever!
            continue
        opass_key = "_".join(
            [
                satellite_name,
                area_def.area_id,
                opass_info["max altitude time"].strftime("%Y%m%dT%H%MZ"),
            ]
        )
        if opass_key not in overpasses:
            overpasses[opass_key] = opass_info
    return overpasses


def predict_overpass_area_def(
    tlefile, area_definition, satellite_list, start_datetime, observer_spacing=50
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
    observer_spacing : float
        Spacing (degrees) between observer points in sector. If domain exceeds the
        specified spacing, multiple observer are automatically added across the sector.

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
            observer_spacing=observer_spacing,
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
    observer_spacing=50,
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
    observer_spacing : float
        Spacing (degrees) between observer points in sector. If domain exceeds the
        specified spacing, multiple observer are automatically added across the sector.

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
            observer_spacing=observer_spacing,
        )
        sector_overpasses[yaml_sector] = overpasses
    return sector_overpasses
