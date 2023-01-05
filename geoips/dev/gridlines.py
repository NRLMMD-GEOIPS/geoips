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

"""Gridlines interface will be deprecated v2.0.

Wrapper functions for geoips gridlines plotting parameter specifications

This functionality will be replaced with a class-based implementation v2.0,
and deprecated at that time.
"""
import logging

LOG = logging.getLogger(__name__)

from geoips.geoips_utils import find_config


### Gridline parameter dictionaries ###
def is_valid_gridlines(gridlines_name):
    """Interface will be deprecated v2.0.

    Check that requested gridlines parameter dictionary is properly formatted.

    The dictionary of gridlines parameters determines how the gridlines
    appear on the output cartopy imagery.

    Dictionary of gridlines parameters currently specified by:

    * ``yaml_configs.plotting_params.gridlines.<gridlines_name>``

    Parameters
    ----------
    gridlines_name : str
        Name of requested gridlines parameter set
        (ie, 'tc_pmw', 'tc_visir', etc)

    Returns
    -------
    bool
        * True if 'gridlines_name' is a properly formatted dictionary of
          gridlines parameters.
        * False if gridlines parameter dictionary:

            * does not contain supported 'gridlines_dict_type',
            * does not contain all 'required' fields,
            * contains non-supported 'optional' fields

    Notes
    -----
    Gridline dictionary types currently one of::

        'standard' :
            dictionary fields: {'gridlines_dict_type': 'standard',
                                'left_label': <bool>,
                                'right_label': <bool>,
                                'top_label': <bool>,
                                'bottom_label': <bool>,
                                'grid_lat_linewidth': <float>,
                                'grid_lon_linewidth': <float>,
                                'grid_lat_color': <str>,
                                'grid_lon_color': <str>,
                                'grid_lat_spacing': <float>,
                                'grid_lon_spacing': <float>,
                                'grid_lat_dashes': <list>,
                                'grid_lon_dashes': <list>}
    """
    required_keys = {
        "standard": [
            "gridlines_dict_type",
            "left_label",
            "right_label",
            "top_label",
            "bottom_label",
            "grid_lat_linewidth",
            "grid_lon_linewidth",
            "grid_lat_color",
            "grid_lon_color",
            "grid_lat_spacing",
            "grid_lon_spacing",
            "grid_lat_dashes",
            "grid_lon_dashes",
        ]
    }

    optional_keys = {
        "standard": [
            "grid_lat_xoffset",
            "grid_lon_xoffset",
            "grid_lat_yoffset",
            "grid_lon_yoffset",
            "grid_lat_fontsize",
            "grid_lon_fontsize",
        ]
    }

    gridlines_dict = get_gridlines(gridlines_name)
    # if gridlines_dict is None:
    #     LOG.error("INVALID PRODUCT '%s': gridlines parameter dictionary did not exist",
    #               gridlines_name)
    #     return False

    if "gridlines_dict_type" not in gridlines_dict:
        LOG.error(
            f"INVALID GRIDLINE '{gridlines_name}': 'gridlines_dict_type' must be defined within gridlines parameter dictionary"
        )
        return False
    if gridlines_dict["gridlines_dict_type"] not in required_keys.keys():
        LOG.error(
            f"INVALID GRIDLINE '{gridlines_name}': 'gridlines_dict_type' in gridlines parameter dictionary must be one of '{list(required_keys.keys())}'"
        )
        return False

    gridlines_dict_type = gridlines_dict["gridlines_dict_type"]

    # If we don't have all of the required keys, return False
    if not set(required_keys[gridlines_dict_type]).issubset(set(gridlines_dict)):
        LOG.error(
            f"""INVALID GRIDLINE "{gridlines_name}": gridlines parameter dictionary must contain the following fields:
                  "{list(required_keys.keys())}" """
        )
        return False

    # If we have non-allowed keys, return False
    if not set(gridlines_dict).issubset(
        required_keys[gridlines_dict_type] + optional_keys[gridlines_dict_type]
    ):
        LOG.error(
            f'''INVALID GRIDLINE "{gridlines_name}": Unknown fields in gridlines parameter dictionary:
                  "{set(gridlines_dict).difference(required_keys[gridlines_dict_type]+optional_keys[gridlines_dict_type])}"'''
        )
        return False

    # If we get here, then the gridlines parameter dictionary format is valid.
    return True


def get_gridlines(gridlines_name):
    """Interface will be deprecated v2.0.

    Get dictionary of requested gridlines parameters.

    See: geoips.dev.gridlines.is_valid_gridlines
        for full list of supported gridlines dictionary formats

    Parameters
    ----------
    gridlines_name : str
        Name of requested gridlines (ie, 'tc_pmw', 'visir_pmw', etc)

    Returns
    -------
    dict
        Dictionary of desired gridlines specifications
    """
    if gridlines_name is None:
        return None
    gridlines_fname = find_config(
        subpackage_name="yaml_configs/plotting_params/gridlines",
        config_basename=gridlines_name,
    )
    import yaml

    with open(gridlines_fname, "r") as fobj:
        gridlines_dict = yaml.safe_load(fobj)
    if gridlines_name not in gridlines_dict:
        raise ValueError(
            f"gridlines file {gridlines_fname} must contain gridlines name {gridlines_name} as key"
        )
    return gridlines_dict[gridlines_name]


def set_lonlat_spacing(gridlines_info, area_def):
    """Interface will be deprecated v2.0."""
    if (
        gridlines_info is None
        or "grid_lat_spacing" not in gridlines_info.keys()
        or "grid_lon_spacing" not in gridlines_info.keys()
        or gridlines_info["grid_lon_spacing"] == "auto"
        or gridlines_info["grid_lat_spacing"] == "auto"
    ):
        from pyresample import utils

        minlat = area_def.area_extent_ll[1]
        maxlat = area_def.area_extent_ll[3]
        minlon = utils.wrap_longitudes(area_def.area_extent_ll[0])
        maxlon = utils.wrap_longitudes(area_def.area_extent_ll[2])
        if minlon > maxlon and maxlon < 0:
            maxlon = maxlon + 360
        lon_extent = maxlon - minlon
        lat_extent = maxlat - minlat

        if lon_extent > 5:
            lon_spacing = int(lon_extent / 5)
        elif lon_extent > 2.5:
            lon_spacing = 1
        else:
            lon_spacing = lon_extent / 5.0

        if lat_extent > 5:
            lat_spacing = int(lat_extent / 5)
        elif lat_extent > 2.5:
            lat_spacing = 1
        else:
            lat_spacing = lat_extent / 5.0

        LOG.info("lon_extent: %s, lon_spacing: %s", lon_extent, lon_spacing)
        gridlines_info["grid_lat_spacing"] = lat_spacing
        gridlines_info["grid_lon_spacing"] = lon_spacing

    return gridlines_info


def get_gridlines_type(gridlines_name):
    """Interface will be deprecated v2.0.

    Retrieve gridlines_dict_type of the requested gridlines, found in:
      geoips.dev.gridlines.get_gridlines(gridlines_name)['gridlines_dict_type']

    See: geoips.dev.gridlines.is_valid_gridlines
        for full list of supported gridlines dict types.

    Parameters
    ----------
    gridlines_name : str
        Name of requested gridlines (ie, 'tc_pmw', 'visir_pmw', etc)

    Returns
    -------
    str
        gridlines dict type, found in
        geoips.dev.gridlines.get_gridlines(gridlines_name)['gridlines_dict_type']
    """
    gridlines_dict = get_gridlines(gridlines_name)
    return gridlines_dict["gridlines_dict_type"]


def list_gridlines_by_type():
    """Interface will be deprecated v2.0.

    List all available gridlines settings within the
    current GeoIPS instantiation, on a per-gridlines_dict_type basis.

    gridlines dict "type" determines exact required format of the gridlines
    parameter dictionary.

    See geoips.dev.gridlines.is_valid_gridlines?
        for a list of available gridlines types and associated
        dictionary formats.
    See geoips.dev.gridlines.get_gridlines(gridlines_name)
        to retrieve the gridlines parameter dictionary
        for a given gridlines

    Returns
    -------
    dict
        Dictionary with all gridlines dict types as keys,
        and lists of associated gridlines names (str) as values.
    """
    from os.path import basename, splitext
    from geoips.geoips_utils import list_gridlines_params_dict_yamls

    all_files = list_gridlines_params_dict_yamls()
    all_gridlines = {}
    for fname in all_files:
        gridlines_name = splitext(basename(fname))[0]
        if not is_valid_gridlines(gridlines_name):
            continue
        gridlines_dict_type = get_gridlines_type(gridlines_name)
        if gridlines_dict_type not in all_gridlines:
            all_gridlines[gridlines_dict_type] = [gridlines_name]
        else:
            if gridlines_name not in all_gridlines[gridlines_dict_type]:
                all_gridlines[gridlines_dict_type] += [gridlines_name]

    return all_gridlines


def test_gridlines_interface():
    """Interface will be deprecated v2.0.

    Finds and opens every gridlines params dict available within the
    current geoips instantiation

    See geoips.dev.gridlines.is_valid_gridlines?
        for a list of available gridlines params dict types and
        associated call signatures / return values.
    See geoips.dev.gridlines.get_gridlines(gridlines_params_dict_name)
        to retrieve the requested gridlines params dict

    Returns
    -------
    list
        List of all successfully opened geoips gridlines params dicts
    """
    curr_names = list_gridlines_by_type()
    out_dict = {
        "by_type": curr_names,
        "validity_check": {},
        "dict_type": {},
        "dict": {},
    }
    for curr_type in curr_names:
        for curr_name in curr_names[curr_type]:
            out_dict["validity_check"][curr_name] = is_valid_gridlines(curr_name)
            out_dict["dict"][curr_name] = get_gridlines(curr_name)
            out_dict["dict_type"][curr_name] = get_gridlines_type(curr_name)

    return out_dict
