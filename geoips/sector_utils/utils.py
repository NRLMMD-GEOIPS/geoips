# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utilities for working with dynamic sector specifications."""

import logging

from pyresample import load_area

from geoips.sector_utils.tc_tracks import set_tc_area_def
from geoips.interfaces import sectors
from geoips.errors import PluginError

LOG = logging.getLogger(__name__)

SECTOR_INFO_ATTRS = {
    "tc": [
        "pressure",
        "vmax",
        "clat",
        "clon",
        "synoptic_time",
        "aid_type",
        "storm_num",
        "storm_name",
        "storm_basin",
        "storm_year",
        "deck_line",
        "source_file",
        "final_storm_name",
    ],
    "pyrocb": ["min_lat", "min_lon", "max_lat", "max_lon", "box_resolution_km"],
    "volcano": [
        "summit_elevation",
        "plume_height",
        "wind_speed",
        "wind_dir",
        "clat",
        "clon",
    ],
    "atmosriver": ["min_lat", "min_lon", "max_lat", "max_lon", "box_resolution_km"],
    "stitched": [
        "continent",
        "country",
        "area",
        "subarea",
        "state",
        "city",
        "primary_area_definition",
    ],
    "static": ["continent", "country", "area", "subarea", "state", "city"],
}


def set_text_area_def(xarray_obj, area_def):
    """Set the area definition for text files.

    This uses raw sectored data, not interpolated.

    Parameters
    ----------
    xarray_obj : xarray.Dataset
        xarray dataset
    area_def : pyresample.AreaDefinition
        original area definition

    Returns
    -------
    pyresample.AreaDefinition
        pyresample AreaDefinition pertaining to the region for generating text file
    """
    text_area_def = area_def
    num_lines = xarray_obj.wind_speed_kts.where(
        xarray_obj.wind_speed_kts > 0, drop=True
    ).shape[0]
    num_samples = xarray_obj.wind_speed_kts.where(
        xarray_obj.wind_speed_kts > 0, drop=True
    ).shape[1]
    # Uses default pixel width/height
    text_area_def = set_tc_area_def(
        area_def.sector_info,
        num_lines=num_lines,
        num_samples=num_samples,
        pixel_width=None,
        pixel_height=None,
    )
    text_area_def.pixel_size_x = "native"
    text_area_def.pixel_size_y = "native"

    return text_area_def


def check_center_coverage(
    xarray_obj,
    area_def,
    varlist,
    covg_varname=None,
    covg_varlist=None,
    width_degrees=8,
    height_degrees=8,
    verbose=False,
    hours_before_sector_time=18,
    hours_after_sector_time=6,
):
    """Check if there is any data covering the center of the sector.

    Do not provide any longitude padding for coverage check sectoring -
    we want to see if there is any data within the exact center box,
    not within +- 3 degrees of the center box.
    """
    covg_area_def = set_tc_coverage_check_area_def(
        area_def, width_degrees=width_degrees, height_degrees=height_degrees
    )

    from geoips.xarray_utils.data import sector_xarray_dataset

    covg_xarray = sector_xarray_dataset(
        xarray_obj,
        covg_area_def,
        varlist,
        lon_pad=0,
        verbose=verbose,
        hours_before_sector_time=hours_before_sector_time,
        hours_after_sector_time=hours_after_sector_time,
    )

    from geoips.data_manipulations.info import percent_unmasked

    # If no covg_xarray returned, return False
    if covg_xarray is None:
        return False, covg_xarray

    # If we passed in a list of coverage variables, loop through each one - if
    # any are > 0, return True
    if covg_varlist is not None:
        for curr_covg_varname in covg_varlist:
            if percent_unmasked(covg_xarray[curr_covg_varname].to_masked_array()) > 0:
                return True, covg_xarray

    # If we only want a single coverage variable, return False if that variable is 0
    if covg_varname is not None:
        if percent_unmasked(covg_xarray[covg_varname].to_masked_array()) == 0:
            return False, covg_xarray

    # Otherwise, return True
    return True, covg_xarray


def copy_sector_info(src_area_def, dest_area_def):
    """Copy sector info from src_area_def to dest_area_def."""
    if hasattr(src_area_def, "sector_info"):
        dest_area_def.sector_info = src_area_def.sector_info
    if hasattr(src_area_def, "sector_type"):
        dest_area_def.sector_type = src_area_def.sector_type
    if hasattr(src_area_def, "sector_start_datetime"):
        dest_area_def.sector_start_datetime = src_area_def.sector_start_datetime
    if hasattr(src_area_def, "sector_end_datetime"):
        dest_area_def.sector_end_datetime = src_area_def.sector_end_datetime
    return dest_area_def


def set_tc_coverage_check_area_def(area_def, width_degrees=8, height_degrees=8):
    """Set the area definition for checking coverage for TC overpasses.

    Take a small box around the center of the storm to evaluate coverage,
    rather than the entire image.

    Parameters
    ----------
    area_def : pyresample.AreaDefinition
        original area definition

    Returns
    -------
    pyresample.AreaDefinition
        pyresample AreaDefinition pertaining to the region for plotting
    """
    covg_area_def = area_def
    DEG_TO_KM = 111.321
    # Take a 8deg x 8deg box centered over the storm location for
    # coverage check, 1km pixels
    width_km = DEG_TO_KM * width_degrees
    height_km = DEG_TO_KM * height_degrees
    LOG.info("  Changing area definition for checking TC coverage")

    from geoips.plugins.modules.sector_spec_generators import center_coordinates

    covg_area_def = center_coordinates.call(
        area_id=area_def.area_id,
        long_description=area_def.description,
        clat=area_def.sector_info["clat"],
        clon=area_def.sector_info["clon"],
        projection="eqc",
        num_lines=int(height_km),
        num_samples=int(width_km),
        pixel_width=1000.0,
        pixel_height=1000.0,
    )
    covg_area_def = copy_sector_info(area_def, covg_area_def)

    LOG.info("  Coverage area definition: %s", covg_area_def.description)
    LOG.info(
        "  Coverage sector info: clat: %s clon: %s",
        covg_area_def.sector_info["clat"],
        covg_area_def.sector_info["clon"],
    )

    return covg_area_def


def get_max_lat(lats):
    """Get maximum latitude from array of latitudes.

    Parameters
    ----------
    lats : numpy.ndarray
        numpy MaskedArray of latitudes

    Returns
    -------
    float
        Maximum latitude, between -90 and 90
    """
    return float(lats.max())


def get_min_lat(lats):
    """Get minimum latitude from array of latitudes.

    Parameters
    ----------
    lats : numpy.ndarray
        numpy MaskedArray of latitudes

    Returns
    -------
    float
        Minimum latitude, between -90 and 90
    """
    return float(lats.min())


def get_min_lon(lons):
    """Get minimum longitude from array of longitudes, handling date line.

    Parameters
    ----------
    lons : numpy.ndarray
        numpy MaskedArray of longitudes

    Returns
    -------
    float
        Minimum longitude, between -180 and 180
    """
    if lons.max() > 179.5 and lons.min() < -179.5:
        import numpy

        lons = numpy.ma.where(lons < 0, lons + 360, lons)
    minlon = lons.min()
    if minlon > 180:
        minlon -= 360
    return float(minlon)


def get_max_lon(lons):
    """Get maximum longitude from array of longitudes, handling date line.

    Parameters
    ----------
    lons : numpy.ndarray
        numpy MaskedArray of longitudes

    Returns
    -------
    float
        Maximum longitude, between -180 and 180
    """
    if lons.max() > 179.5 and lons.max() < -179.5:
        import numpy

        lons = numpy.ma.where(lons < 0, lons + 360, lons)
    maxlon = lons.max()
    if maxlon > 180:
        maxlon -= 360
    return float(maxlon)


def get_lat_center(lats):
    """Return the center longitude point from lats array."""
    center_lat = lats.min() + (lats.max() - lats.min()) / 2.0
    return center_lat


def get_lon_center(lons):
    """Return the center longitude point from lons array."""
    import numpy

    if lons.max() > 179.5 and lons.min() < -179.5:
        lons = numpy.ma.where(lons < 0, lons + 360, lons)

    center_lon = lons.min() + (lons.max() - lons.min()) / 2.0

    if center_lon > 180:
        center_lon -= 360

    return center_lon


def get_trackfile_area_defs(
    trackfiles,
    trackfile_parser,
    trackfile_sectorlist=None,
    tc_spec_template=None,
    aid_type=None,
    start_datetime=None,
    end_datetime=None,
):
    """Get all TC area definitions for the current xarray object, and requested sectors.

    Parameters
    ----------
    trackfiles : list
        List of trackfiles to convert into area_defs
    trackfile_parser : str
        Parser to use from plugins.modules.sector_metadata_generators on trackfiles
    trackfile_sectorlist list of str, default=None
        * list of sector names to process, of format: tc2020io01amphan.
        * If None, or 'all' contained in list, process all matching TC sectors.
    aid_type : str, default=None
        If specified, string to look for in "aid_type" TC deck file field for
        inclusion

    Returns
    -------
    list of pyresample.AreaDefinition
        List of pyresample AreaDefinition objects
    """
    area_defs = []
    final_area_defs = []
    from geoips.sector_utils.tc_tracks import trackfile_to_area_defs

    for trackfile in trackfiles:
        adef, allowed_aid_types = trackfile_to_area_defs(
            trackfile,
            trackfile_parser=trackfile_parser,
            tc_spec_template=tc_spec_template,
        )
        area_defs += adef
    if trackfile_sectorlist is not None and "all" not in trackfile_sectorlist:
        for area_def in area_defs:
            if "storm_id" not in area_def.sector_info:
                LOG.warning("FAILED storm_id not defined in sector_info")
                raise ValueError(
                    "FAILED storm_id not defined in sector_info. Ensure storm_id "
                    "defined in trackfile parser."
                )
            elif area_def.sector_info["storm_id"] in trackfile_sectorlist:
                final_area_defs += [area_def]
            else:
                LOG.info(
                    "area_def storm_id %s area_id %s not in trackfile_sectorlist %s, "
                    "not including",
                    area_def.sector_info["storm_id"],
                    area_def.area_id,
                    str(trackfile_sectorlist),
                )
    else:
        final_area_defs = area_defs

    ret_area_defs = final_area_defs
    if start_datetime is not None and end_datetime is not None:
        ret_area_defs = []
        for area_def in final_area_defs:
            if (
                area_def.sector_start_datetime > start_datetime
                and area_def.sector_start_datetime < end_datetime
            ):
                ret_area_defs += [area_def]

    # Make sure there are no duplicates
    ret_area_defs = remove_duplicate_storm_positions_and_unsupported_aid_types(
        ret_area_defs, allowed_aid_types
    )

    return ret_area_defs


def get_static_area_defs_for_xarray(xarray_obj, sectorlist):
    """Get all STATIC area definitions for the current xarray object.

    Filter based on requested sectors.

    Parameters
    ----------
    xarray_obj : xarray.Dataset
        xarray Dataset to which we are assigning area_defs
    sectorlist : list of str
        list of sector names

    Returns
    -------
    list of pyresample.AreaDefinition
        List of pyresample AreaDefinition objects
    """
    area_defs = []
    if (
        xarray_obj is not None
        and "area_definition" in xarray_obj.attrs.keys()
        and xarray_obj.area_definition is not None
    ):
        if xarray_obj.area_definition.area_id in sectorlist:
            LOG.info(
                "%s area_id in sectorlist and in xarray_obj.area_definition, adding "
                "area_def",
                xarray_obj.area_definition.area_id,
            )
            area_defs = [xarray_obj.area_definition]
        else:
            LOG.info(
                "%s area_id NOT in sectorlist and set on xarray_obj.area_definition, "
                "SKIPPING area_def",
                xarray_obj.area_definition.area_id,
            )
    elif sectorlist is not None:
        area_defs = get_sectors_from_yamls(sectorlist)

    ret_area_defs = []
    for area_def in area_defs:
        if area_def.description not in [
            curr_area_def.description for curr_area_def in ret_area_defs
        ]:
            LOG.info("Including area_def %s in return list", area_def.description)
            ret_area_defs += [area_def]
        else:
            LOG.info(
                "area_def %s already in return list, not including",
                area_def.description,
            )

    return ret_area_defs


def get_tc_area_defs_for_xarray(
    xarray_obj,
    tcdb_sector_list=None,
    tc_spec_template=None,
    trackfile_parser=None,
    hours_before_sector_time=18,
    hours_after_sector_time=6,
    aid_type=None,
):
    """Get all TC area definitions for the current xarray object, and requested sectors.

    Parameters
    ----------
    xarray_obj : xarray.Dataset
        xarray Dataset to which we are assigning area_defs
    tcdb_sector_list : list of str, default=None
        * list of sector names to process, of format: tc2020io01amphan.
        * If None, or 'all' contained in list, process all matching TC sectors.
    actual_datetime : datetime.datetime, default=None
        Optional datetime to match for dynamic sectors
    var_for_coverage : str
        Default None, optional variable to sector to check exact time
    hours_before_sector_time : float, default=18
        hours to look before sector time
    hours_after_sector_time : float, default=6
        hours to look after sector time
    aid_type : str, default=None
        string to look for in "aid_type" TC deck file field for inclusion

    Returns
    -------
    list of pyresample AreaDefinition
        List of pyresample AreaDefinition objects required for passed xarray
    """
    if (
        "area_definition" in xarray_obj.attrs.keys()
        and xarray_obj.area_definition is not None
    ):
        return [xarray_obj.area_definition]

    area_defs = []
    from datetime import timedelta
    from geoips.sector_utils.tc_tracks_database import get_all_storms_from_db

    curr_area_defs, allowed_aid_types = get_all_storms_from_db(
        xarray_obj.start_datetime - timedelta(hours=hours_before_sector_time),
        xarray_obj.end_datetime + timedelta(hours=hours_after_sector_time),
        tc_spec_template=tc_spec_template,
        trackfile_parser=trackfile_parser,
    )
    if tcdb_sector_list is not None and "all" not in tcdb_sector_list:
        for area_def in curr_area_defs:
            if "storm_id" not in area_def.sector_info:
                LOG.warning("FAILED storm_id not defined in sector_info")
                raise ValueError(
                    "FAILED storm_id not defined in sector_info. Ensure storm_id "
                    "defined in trackfile parser."
                )
            elif area_def.sector_info["storm_id"] in tcdb_sector_list:
                area_defs += [area_def]
            else:
                LOG.info(
                    "area_def storm_id %s area_id %s not in tcdb_sector_list %s, "
                    "not including",
                    area_def.sector_info["storm_id"],
                    area_def.area_id,
                    str(tcdb_sector_list),
                )
    else:
        area_defs = curr_area_defs

    # Make sure there are no duplicates
    ret_area_defs = remove_duplicate_storm_positions_and_unsupported_aid_types(
        area_defs, allowed_aid_types
    )
    return ret_area_defs


def is_requested_aid_type(area_def, allowed_aid_types=None):
    """Return True if passed area_def is of requested aid_type."""
    if (
        allowed_aid_types is not None
        and "aid_type" in area_def.sector_info
        and not any(area_def.sector_info["aid_type"] == x for x in allowed_aid_types)
    ):
        return False
    return True


def storm_locations_match(area_def, other_area_def):
    """Return True if passed pyresample AreaDefinitions are the same location.

    Match if center lat, center lon, storm year, storm basin, and synoptic time
    all match.
    """
    if (
        area_def.sector_info["clat"] == other_area_def.sector_info["clat"]
        and area_def.sector_info["clon"] == other_area_def.sector_info["clon"]
        and area_def.sector_info["storm_year"]
        == other_area_def.sector_info["storm_year"]
        and area_def.sector_info["storm_basin"]
        == other_area_def.sector_info["storm_basin"]
        and area_def.sector_info["synoptic_time"]
        == other_area_def.sector_info["synoptic_time"]
    ):
        return True
    return False


def remove_duplicate_storm_positions_and_unsupported_aid_types(
    area_defs, allowed_aid_types=None
):
    """Remove duplicate storm positions from passed list of area_defs.

    Uses "is_requested_aid_type" and "storm_locations_match" utilities.
    """
    ret_area_defs = []
    for area_def in area_defs:
        if not is_requested_aid_type(area_def, allowed_aid_types):
            LOG.debug(
                "area_def %s aid_type %s not requested, not including",
                area_def.description,
                area_def.sector_info["aid_type"],
            )
            continue
        elif area_def.description in [
            curr_area_def.description for curr_area_def in ret_area_defs
        ]:
            LOG.info(
                "area_def %s already in return list, not including",
                area_def.description,
            )
            continue
        else:
            kept_one = False
            for other_area_def in area_defs:
                if (
                    area_def.sector_info["final_storm_name"].lower() == "invest"
                    and other_area_def.sector_info["final_storm_name"].lower()
                    != "invest"
                    and storm_locations_match(area_def, other_area_def)
                    and is_requested_aid_type(other_area_def, allowed_aid_types)
                ):
                    kept_one = True
                    LOG.info(
                        "Including area_def %s in return list, NOT including %s",
                        other_area_def.description,
                        area_def.description,
                    )
                    ret_area_defs += [other_area_def]
                if "storm_id" not in area_def.sector_info:
                    LOG.warning("FAILED storm_id not defined in sector_info")
                    raise ValueError(
                        "FAILED storm_id not defined in sector_info. Ensure storm_id "
                        "defined in trackfile parser."
                    )
                elif (
                    "invest_storm_id" in other_area_def.sector_info
                    and other_area_def.sector_info["invest_storm_id"]
                    == area_def.sector_info["storm_id"]
                ):
                    kept_one = True
                    LOG.info(
                        "Including area_def %s in return list, NOT including %s, "
                        "invest_storm_id defined",
                        other_area_def.area_id,
                        area_def.sector_info["storm_id"],
                    )
                    ret_area_defs += [other_area_def]

            if not kept_one and "aid_type" in area_def.sector_info:
                ret_area_defs += [area_def]
                LOG.debug(
                    "Including area_def %s in return list, track type %s",
                    area_def.description,
                    area_def.sector_info["aid_type"],
                )
            elif not kept_one:
                ret_area_defs += [area_def]
                LOG.info("Including area_def %s in return list", area_def.description)

    return ret_area_defs


def filter_area_defs_actual_time(area_defs, actual_datetime):
    """Filter list of area_defs to only include the passed actual_datetime."""
    ret_area_def_ids = {}
    for area_def in area_defs:
        storm_id = area_def.sector_info.get("storm_id")
        if storm_id and storm_id not in ret_area_def_ids:
            ret_area_def_ids[storm_id] = area_def
        elif is_dynamic_sector(area_def) and actual_datetime is not None:
            if abs(actual_datetime - area_def.sector_start_datetime) < abs(
                actual_datetime - ret_area_def_ids[storm_id].sector_start_datetime
            ):
                LOG.debug(
                    "AREA_DEF LIST REPLACING %s with area_def %s",
                    ret_area_def_ids[storm_id].area_id,
                    area_def.area_id,
                )
                ret_area_def_ids[storm_id] = area_def
        else:
            LOG.warning(
                "AREA_DEF LIST REPLACING Multiple identical sectors - using latest %s",
                area_def.area_id,
            )
            ret_area_def_ids[storm_id] = area_def

    return ret_area_def_ids.values()


# def filter_area_defs_sector(area_defs, xarray_obj, var_for_coverage):
#     from geoips.xarray_utils.data import sector_xarrays
#     ret_area_def_ids = {}
#     ret_area_def_sects = {}
#     for area_def in area_defs:
#         if area_def.area_id not in ret_area_def_ids:
#             sects = sector_xarrays([xarray_obj],
#                                    area_def,
#                                    varlist=[var_for_coverage],
#                                    verbose=False)
#             if not sects:
#                 LOG.info('AREA_DEF LIST NO COVERAGE not adding sector')
#             else:
#                 LOG.info('AREA_DEF LIST ADDING area_def %s', area_def.description)
#                 ret_area_def_ids[area_def.area_id] = area_def
#                 ret_area_def_sects[area_def.area_id] = sects[0]
#         elif is_dynamic_sector(area_def):
#             old_sect = ret_area_def_sects[area_def.area_id]
#             old_area_def = ret_area_def_ids[area_def.area_id]
#             sects = sector_xarrays([xarray_obj],
#                                    area_def,
#                                    varlist=[var_for_coverage],
#                                    verbose=False)
#             if sects and abs(sects[0].start_datetime - area_def.sector_start_datetime)
#                   < abs(old_sect.start_datetime - old_area_def.sector_start_datetime):
#
#                 LOG.info('AREA_DEF LIST REPLACING %s with area_def %s',
#                          ret_area_def_ids[area_def.area_id].name,
#                          area_def.description)
#                 ret_area_def_ids[area_def.area_id] = area_def
#                 ret_area_def_sects[area_def.area_id] = sects[0]
#
#         else:
#             LOG.warning('AREA_DEF LIST REPLACING Multiple identical sectors - using
#                         latest %s', area_def.description)
#             ret_area_def_ids[area_def.area_id] = area_def
#
#     return ret_area_def_ids.values()


def get_sectors_from_yamls(sector_list):
    """Get AreaDefinition objects with custom "sector_info" dictionary.

    Based on YAML area definition contained in "sectorfnames" files.

    Parameters
    ----------
    sector_list : list of str
        list of strings of desired sector names to retrieve from YAML files

    Returns
    -------
    list
        List of pyresample AreaDefinition objects, with arbitrary additional YAML
        entries added as attributes to each area def (this is to allow specifying
        "sector_info" metadata dictionary within the YAML file)
    """
    from importlib.resources import files

    area_defs = []
    for sector_name in sector_list:
        try:
            sector_plugin = sectors.get_plugin(sector_name)
        except PluginError as resp:
            raise PluginError(
                f"{resp}:\nError getting sector {sector_name} from "
                f"\nsector_list {sector_list}. "
                f"\nCheck plugin directories for sector plugin named "
                f"{sector_name}"
            )
        abspath = str(files(sector_plugin.package) / sector_plugin.relpath)
        area_def = load_area(abspath, "spec")
        area_def.__setattr__("sector_info", sector_plugin["metadata"])
        area_def.__setattr__("sector_type", sector_plugin["family"])
        area_defs += [area_def]
    return area_defs


def create_areadefinition_from_yaml(yamlfile, sector):
    """Take a YAML with misc metadata and create a pyresample areadefinition.

    Misc. metadata will be parsed from the YAML file and manually added to the
    areadefinition

    Parameters
    ----------
    yamlfile : str
        full path to YAML area definition file
    sector : str
        name of sector

    Returns
    -------
    pyresample.AreaDefinition
        pyresample AreaDefinition based on YAML specification.
    """
    import pyresample
    import yaml

    with open(yamlfile, "r") as f:
        sectorfile_yaml = yaml.safe_load(f)
    sector_info = sectorfile_yaml["spec"]
    area_id = sector
    description = sector_info.pop("description")
    projection = sector_info.pop("projection")
    resolution = sector_info.pop("resolution")
    shape = sector_info.pop("shape")
    area_extent = sector_info.pop("area_extent")
    # Create the pyresample area definition
    shape_list = [shape["height"], shape["width"]]
    extent_list = []
    extent_list.extend(area_extent["lower_left_xy"])
    extent_list.extend(area_extent["upper_right_xy"])
    area_def = pyresample.create_area_def(
        area_id=area_id,
        description=description,
        projection=projection,
        resolution=resolution,
        shape=shape_list,
        area_extent=extent_list,
    )
    # Manually add the metadata to area_def
    for key in sector_info.keys():
        area_def.__setattr__(key, sector_info[key])
    return area_def


def is_sector_type(area_def, sector_type_str):
    """Determine if the type of area_def sector is as specified in passed sector_type.

    Parameters
    ----------
    area_def : pyresample.AreaDefinition
        pyresample AreaDefinition object specifying region of interest
    sector_type_str : str
        * String specifying the type of sector, must match 'sector_type'
          attribute on AreaDefinition object
        * currently one of 'tc', 'pyrocb', 'volcano', 'atmosriver' 'static'

    Returns
    -------
    bool
        True if area_def.sector_type == 'sector_type', False otherwise
    """
    if not area_def:
        LOG.info("area_def not defined, not of type %s", sector_type_str)
        return False
    if not hasattr(area_def, "sector_type"):
        LOG.info("area_def.sector_type not defined, not of type %s", sector_type_str)
        return False

    if area_def.sector_type == sector_type_str:
        # Need to decide if this is necessary.
        # for attr in SECTOR_INFO_ATTRS[sector_type_str]:
        #     if attr not in area_def.sector_info.keys():
        #         LOG.warning('attr %s not in area_def.sector_info.keys(), not of type
        #                     %s', attr, sector_type_str)
        #         return False
        return True
    return False


def is_dynamic_sector(area_def):
    """Determine if the AreaDefinition object is a dynamic region of interest.

    Parameters
    ----------
    area_def : pyresample.AreaDefinition
        pyresample AreaDefinition object specifying region of interest

    Returns
    -------
    bool
        * True if area_def.sector_start_datetime exists and is not None,
        * False otherwise
    """
    if not area_def:
        return False
    if not hasattr(area_def, "sector_start_datetime"):
        return False
    if not area_def.sector_start_datetime:
        return False
    if area_def.sector_start_datetime is not None:
        return True
    return False
