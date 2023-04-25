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

"""Utility for estimating the area extent, used in pyresample area definitions."""

import argparse
import numpy as np
from string import Template

EARTH_RADIUS_METERS = 6371228.0


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two latitude and longitude points.

    Uses the haversine formula.

    Parameters
    ----------
    lat1, lon1, lat2, lon2 : float
        Pair of latitude and longitude coordinates in degrees

    Returns
    -------
    float
        Distance in meters between two coordinates
    """
    # Haversine formula:
    # a = sin^2( delta_phiΔφ/2) + cos(phi_1) * cos(phi_2) * sin^2(Δdelta_lambdaλ/2)
    # c = 2 * atan2( sqrt(a), sqrt(1-a) )
    # d = R * c

    # Convert lats and lons to radians
    phi_1 = np.deg2rad(lat1)
    phi_2 = np.deg2rad(lat2)
    d_phi = np.deg2rad(lat2 - lat1)
    d_lambda = np.deg2rad(lon2 - lon1)

    # Calculate haversine distance
    a = (
        np.sin(d_phi / 2.0) ** 2
        + np.cos(phi_1) * np.cos(phi_2) * np.sin(d_lambda / 2.0) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    d = EARTH_RADIUS_METERS * c
    return d


def convert_west2east(longitude):
    """Convert Longitude from degrees West to degrees East, if applicable.

    Parameters
    ----------
    longitude : float
        Longitude (degrees West or East)

    Returns
    -------
    float
        Longitude in degrees East
    """
    if longitude < 0:
        lon_east = longitude + 360
    else:
        lon_east = longitude
    return lon_east


def center_longitude(min_longitude, max_longitude):
    """Determine the center longitude based off longitude in either degW or degE.

    Parameters
    ----------
    min_longitude, max_longitude : float
        Min and Max Longitude (degrees West or East)

    Returns
    -------
    float
        Center longitude in degrees West or East
    """
    min_lonE = convert_west2east(min_longitude)
    max_lonE = convert_west2east(max_longitude)
    if min_lonE > max_lonE:
        # Prime meridian edge case (e.g. -5W - 5E)
        center_lon = (min_longitude + max_longitude) / 2.0
    else:
        center_lon = (min_lonE + max_lonE) / 2.0
    if center_lon > 180:
        center_lon -= 360
    return center_lon


def estimate_area_extent(min_lat, min_lon, max_lat, max_lon, resolution):
    """Estimate the area extent for use in the YAML area definition.

    Parameters
    ----------
    min_lat, min_lon, max_lat, max_lon : float
        Min/Max lat/lon values in degrees
    resolution : float
        Resolution in meters

    Returns
    -------
    dict
        Dictionary holding:

        * lower_left_xy - list of projection x/y coordinates of
          lower left corner of lower left pixel
        * upper_right_xy - list of projection x/y coordinates of
          upper right corner of upper right pixel
        * height - number of grid rows
        * width - number of grid columns
        * lat_0 - Center latitude in degrees
        * lon_0 - Center longitude in degrees
    """
    if min_lat == max_lat:
        raise ValueError("MIN_LAT and MAX_LAT must be different")
    if min_lon == max_lon:
        raise ValueError("MIN_LON and MAX_LON must be different")
    # Convert all longitude points to degrees east
    min_lonE = convert_west2east(min_lon)
    max_lonE = convert_west2east(max_lon)
    center_lat = (min_lat + max_lat) / 2.0
    center_lon = center_longitude(min_lon, max_lon)
    lat_distance = haversine_distance(min_lat, center_lon, max_lat, center_lon)
    # The haversine formula will find the shortest distance between two points
    # If we want the sector larger than 180 degrees in longitude, we need
    # some special handling for the distance calculation
    if (max_lonE - min_lonE) > 180:
        dist1 = haversine_distance(center_lat, min_lonE, center_lat, min_lonE + 180)
        dist2 = haversine_distance(center_lat, min_lonE + 180, center_lat, max_lonE)
        lon_distance = dist1 + dist2
    else:
        lon_distance = haversine_distance(center_lat, min_lon, center_lat, max_lon)
    extent_lat = int(lat_distance / 2.0)
    extent_lon = int(lon_distance / 2.0)
    height = int(lat_distance / resolution)
    width = int(lon_distance / resolution)
    lower_left_xy = [-1 * extent_lon, -1 * extent_lat]
    upper_right_xy = [extent_lon, extent_lat]
    return {
        "lower_left_xy": lower_left_xy,
        "upper_right_xy": upper_right_xy,
        "height": height,
        "width": width,
        "lat_0": center_lat,
        "lon_0": center_lon,
    }


AREA_DEF_TEMPLATE = """
# Copy and paste the following into a yaml sector file.
# Replace @SECTOR_NAME@ and @SECTOR_DESCRIPTION@ with appropriate information.
# Update sector_info as needed as well

@SECTOR_NAME@:
  description: @SECTOR_DESCRIPTION@
  projection:
      a: $EARTH_RADIUS_METERS
      lat_0: $lat_0
      lon_0: $lon_0
      proj: eqc
      units: m
  resolution:
  - $resolution
  - $resolution
  sector_info:
      continent: x
      country: x
      area: x
      subarea: x
      state: x
      city: x
  sector_family: static
  shape:
      height: $height
      width: $width
  area_extent:
      lower_left_xy: $lower_left_xy
      upper_right_xy: $upper_right_xy
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_lat", type=float, required=True)
    parser.add_argument("--max_lon", type=float, required=True)
    parser.add_argument("--min_lat", type=float, required=True)
    parser.add_argument("--min_lon", type=float, required=True)
    parser.add_argument("--resolution", "-r", type=int, required=True)

    ARGS = parser.parse_args()

    estimated_extent = estimate_area_extent(
        ARGS.min_lat, ARGS.min_lon, ARGS.max_lat, ARGS.max_lon, ARGS.resolution
    )
    lat_0 = estimated_extent["lat_0"]
    lon_0 = estimated_extent["lon_0"]
    height, width = estimated_extent["height"], estimated_extent["width"]
    lower_left_xy = estimated_extent["lower_left_xy"]
    upper_right_xy = estimated_extent["upper_right_xy"]

    populated_template = Template(AREA_DEF_TEMPLATE).substitute(
        {
            "EARTH_RADIUS_METERS": EARTH_RADIUS_METERS,
            "lat_0": lat_0,
            "lon_0": lon_0,
            "resolution": ARGS.resolution,
            "height": height,
            "width": width,
            "lower_left_xy": lower_left_xy,
            "upper_right_xy": upper_right_xy,
        }
    )
    print(populated_template)
