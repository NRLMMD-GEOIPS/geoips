# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""matplotlib geographic map (basemap or cartopy) utilities."""

# Python Standard Libraries
import logging
from copy import deepcopy
import pyresample
import cartopy.feature as cfeature
from math import ceil
import numpy as np
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from geoips.interfaces import feature_annotators, gridline_annotators

LOG = logging.getLogger(__name__)


def ellps2axis(ellps_name):
    """
    Get semi-major and semi-minor axis from ellipsis definition.

    Parameters
    ----------
    ellps_name : str
        Standard name of ellipsis

    Returns
    -------
    avar : float
        semi-major axis
    bvar : float
        semi-minor axis
    """
    ellps = {
        "helmert": {"a": 6378200.0, "b": 6356818.1696278909},
        "intl": {"a": 6378388.0, "b": 6356911.9461279465},
        "merit": {"a": 6378137.0, "b": 6356752.2982159676},
        "wgs72": {"a": 6378135.0, "b": 6356750.5200160937},
        "sphere": {"a": 6370997.0, "b": 6370997.0},
        "clrk66": {"a": 6378206.4000000004, "b": 6356583.7999999998},
        "nwl9d": {"a": 6378145.0, "b": 6356759.7694886839},
        "lerch": {"a": 6378139.0, "b": 6356754.2915103417},
        "evrstss": {"a": 6377298.5559999999, "b": 6356097.5503008962},
        "evrst30": {"a": 6377276.3449999997, "b": 6356075.4131402401},
        "mprts": {"a": 6397300.0, "b": 6363806.2827225132},
        "krass": {"a": 6378245.0, "b": 6356863.0187730473},
        "walbeck": {"a": 6376896.0, "b": 6355834.8466999996},
        "kaula": {"a": 6378163.0, "b": 6356776.9920869097},
        "wgs66": {"a": 6378145.0, "b": 6356759.7694886839},
        "evrst56": {"a": 6377301.2429999998, "b": 6356100.2283681016},
        "new_intl": {"a": 6378157.5, "b": 6356772.2000000002},
        "airy": {"a": 6377563.3959999997, "b": 6356256.9100000001},
        "bessel": {"a": 6377397.1550000003, "b": 6356078.9628181886},
        "seasia": {"a": 6378155.0, "b": 6356773.3205000004},
        "aust_sa": {"a": 6378160.0, "b": 6356774.7191953054},
        "wgs84": {"a": 6378137.0, "b": 6356752.3142451793},
        "hough": {"a": 6378270.0, "b": 6356794.3434343431},
        "wgs60": {"a": 6378165.0, "b": 6356783.2869594367},
        "engelis": {"a": 6378136.0499999998, "b": 6356751.3227215428},
        "apl4.9": {"a": 6378137.0, "b": 6356751.796311819},
        "andrae": {"a": 6377104.4299999997, "b": 6355847.4152333336},
        "sgs85": {"a": 6378136.0, "b": 6356751.301568781},
        "delmbr": {"a": 6376428.0, "b": 6355957.9261637237},
        "fschr60m": {"a": 6378155.0, "b": 6356773.3204827355},
        "iau76": {"a": 6378140.0, "b": 6356755.2881575283},
        "plessis": {"a": 6376523.0, "b": 6355863.0},
        "cpm": {"a": 6375738.7000000002, "b": 6356666.221912113},
        "fschr68": {"a": 6378150.0, "b": 6356768.3372443849},
        "mod_airy": {"a": 6377340.1890000002, "b": 6356034.4460000005},
        "grs80": {"a": 6378137.0, "b": 6356752.3141403561},
        "bess_nam": {"a": 6377483.8650000002, "b": 6356165.3829663256},
        "fschr60": {"a": 6378166.0, "b": 6356784.2836071067},
        "clrk80": {"a": 6378249.1449999996, "b": 6356514.9658284895},
        "evrst69": {"a": 6377295.6639999999, "b": 6356094.6679152036},
        "grs67": {"a": 6378160.0, "b": 6356774.5160907144},
        "evrst48": {"a": 6377304.0630000001, "b": 6356103.0389931547},
    }
    try:
        ellps_axis = ellps[ellps_name.lower()]
        avar = ellps_axis["a"]
        bvar = ellps_axis["b"]
    except KeyError:
        raise ValueError(
            (
                "Could not determine semi-major and semi-minor axis "
                "of specified ellipsis %s"
            )
            % ellps_name
        )
    return avar, bvar


def is_crs(mapobj):
    """
    Determine if the map object we are using is a cartopy crs instance.

    Parameters
    ----------
    mapobj : map object
        Basemap or cartopy._PROJ4Projection object

    Returns
    -------
    crs : bool
        True if it is a CRS object, False otherwise.
    """
    crs = False
    if "cartopy" in str(mapobj.__class__):
        crs = True
    return crs


def parallels(area_def, grid_size):
    """
    Calculate the parallels (latitude) that fall within the input sector.

    Parameters
    ----------
    area_def : AreaDefinition
        pyresample AreaDefinition
    grid_size : float
        grid spacing in degrees

    Returns
    -------
    lat_ticks : list
        latitude locations for gridlines
    """
    if grid_size == "auto":
        grid_size = compute_lat_auto_spacing(area_def)

    gs = float(grid_size)

    lats = area_def.get_lonlats()[1]
    mlats = np.ma.masked_greater(lats, 90)
    min_parallel = ceil(float(mlats.min()) / gs) * gs
    max_parallel = ceil(float(mlats.max()) / gs) * gs
    lat_ticks = np.arange(min_parallel, max_parallel, gs)
    LOG.info("List of parallels: min/max %s, %s", lat_ticks[0], lat_ticks[-1])
    lat_ticks = [round(lat_tick, 1) for lat_tick in lat_ticks]
    return lat_ticks


def meridians(area_def, grid_size):
    """
    Calculate the meridians (longitude) that are within the input sector.

    Parameters
    ----------
    area_def : AreaDefinition
        pyresample AreaDefinition
    grid_size : float
        grid spacing in degrees

    Returns
    -------
    meridians_to_draw : list
        longitude locations for gridlines
    """
    if grid_size == "auto":
        grid_size = compute_lon_auto_spacing(area_def)

    gs = float(grid_size)

    corners = area_def.corners
    lons = [np.rad2deg(corn.lon) for corn in corners]
    if area_def.proj_dict["lat_0"] > 0:
        crn_idx = 0
        mc_idx = 1
    else:
        crn_idx = 3
        mc_idx = 2
    llcrnrlon = lons[crn_idx]
    urcrnrlon = lons[mc_idx]
    # Needed for full disk - need to generalize so it works for both.
    # mlons = np.ma.masked_greater(sector.area_definition.get_lonlats()[0],180)
    # corners = mlons.min(),mlons.max()
    # #lons = [np.rad2deg(corn.lon) for corn in corners]
    # llcrnrlon = corners[0]
    # urcrnrlon = corners[1]

    cent_lon = area_def.proj_dict["lon_0"]

    if urcrnrlon < cent_lon < llcrnrlon:
        urcrnrlon += 360
    elif urcrnrlon < llcrnrlon:
        llcrnrlon -= 360
    # Draw all the lines if over the poles
    if (area_def.proj_dict["lat_0"] == -90) or (area_def.proj_dict["lat_0"] == 90):
        llcrnrlon = -180
        urcrnrlon = 180

    min_meridian = ceil(float(llcrnrlon) / gs) * gs
    max_meridian = ceil(float(urcrnrlon) / gs) * gs
    meridians_to_draw = np.arange(min_meridian, max_meridian, gs)

    meridians_to_draw = pyresample.utils.wrap_longitudes(meridians_to_draw)
    LOG.info(
        "List of meridians: min/max %s, %s", meridians_to_draw[0], meridians_to_draw[-1]
    )
    meridians_to_draw = [round(lon_tick, 1) for lon_tick in meridians_to_draw]
    return meridians_to_draw


def check_gridline_annotator(gridline_annotator):
    """
    Check gridlines_info dictionary for that all required fields.

    Parameters
    ----------
    gridline_annotator : YamlPlugin
        A gridline annotator plugin instance.

    Raises
    ------
    ValueError
        If required field is missing
    """
    required_fields = {
        "spacing": ["latitude", "longitude"],
        "labels": ["top", "bottom", "left", "right"],
        "lines": ["color", "linestyle", "linewidth"],
    }

    if gridline_annotator is None:
        gridline_annotator = gridline_annotators.get_plugin("default")

    for key, subkeys in required_fields.items():
        if key not in gridline_annotator["spec"]:
            raise ValueError(
                "Missing gridlines_info entry {0}, required_fields {1}".format(
                    key, required_fields
                )
            )
        if key in ["xpadding" or "ypadding"]:
            # We skip here since we don't require 'xpadding' or 'ypadding'. These are
            # optional attributes that you can apply to the gridline_annotator if
            # wanted.
            continue
        for subkey in subkeys:
            if subkey not in gridline_annotator["spec"][key]:
                LOG.info(gridline_annotator)
                raise ValueError(
                    "Missing gridline_annotator property "
                    f"{key}.{subkey}, required_fields {required_fields}"
                )
    return gridline_annotator


def set_gridlines_info_dict(gridlines_info, area_def):
    """
    Set plotting gridlines.

    Set the final values for gridlines plotting params, pulling from
    argument and defaults.

    Parameters
    ----------
    gridlines_info : dict
        Dictionary of parameters for plotting gridlines. The following
        fields are available.  If a field is not included in the
        dictionary, the field is added to the return dictionary and the
        default is used.
    area_def : AreaDefinition
        pyresample AreaDefinition

    Returns
    -------
    use_gridlines_info : dict
        gridlines_info dictionary, with fields as specified above.

    Notes
    -----
    Defaults specified as::

        gridlines_info['grid_lat_spacing']      default auto calculated 5 lat grid lines
        gridlines_info['grid_lon_spacing']      default auto calculated 5 lon grid lines
        gridlines_info['grid_lat_xoffset']      default None (0.01 * image height)
        gridlines_info['grid_lon_xoffset']      default None (0.01 * image width)
        gridlines_info['grid_lat_yoffset']      default None (0.01 * image height)
        gridlines_info['grid_lon_yoffset']      default None (0.01 * image width)
        gridlines_info['grid_lat_fontsize']     default None (plot fontsize)
        gridlines_info['grid_lon_fontsize']     default None (plot fontsize)
        gridlines_info['left_label']            default True
        gridlines_info['right_label']           default False
        gridlines_info['top_label']             default True
        gridlines_info['bottom_label']          default False
        gridlines_info['grid_lat_linewidth']    default 1
        gridlines_info['grid_lon_linewidth']    default 1
        gridlines_info['grid_lat_color']        default 'black'
        gridlines_info['grid_lon_color']        default 'black'
        gridlines_info['grid_lat_dashes']       default [4, 2]
        gridlines_info['grid_lon_dashes']       default [4, 2]
    """
    use_gridlines_info = {}

    if (
        gridlines_info is None
        or "grid_lat_spacing" not in gridlines_info.keys()
        or "grid_lon_spacing" not in gridlines_info.keys()
        or gridlines_info["grid_lon_spacing"] == "auto"
        or gridlines_info["grid_lat_spacing"] == "auto"
    ):
        minlat = area_def.area_extent_ll[1]
        maxlat = area_def.area_extent_ll[3]
        minlon = pyresample.utils.wrap_longitudes(area_def.area_extent_ll[0])
        maxlon = pyresample.utils.wrap_longitudes(area_def.area_extent_ll[2])
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
        use_gridlines_info["grid_lat_spacing"] = lat_spacing
        use_gridlines_info["grid_lon_spacing"] = lon_spacing

    use_gridlines_info["left_label"] = True
    use_gridlines_info["right_label"] = False
    use_gridlines_info["top_label"] = True
    use_gridlines_info["bottom_label"] = False
    use_gridlines_info["grid_lat_linewidth"] = 1
    use_gridlines_info["grid_lon_linewidth"] = 1
    use_gridlines_info["grid_lat_color"] = "black"
    use_gridlines_info["grid_lon_color"] = "black"
    use_gridlines_info["grid_lat_xoffset"] = None
    use_gridlines_info["grid_lon_xoffset"] = None
    use_gridlines_info["grid_lat_yoffset"] = None
    use_gridlines_info["grid_lon_yoffset"] = None
    use_gridlines_info["grid_lat_fontsize"] = None
    use_gridlines_info["grid_lon_fontsize"] = None
    use_gridlines_info["grid_lat_dashes"] = [4, 2]
    use_gridlines_info["grid_lon_dashes"] = [4, 2]

    if gridlines_info is not None:
        for gkey in gridlines_info.keys():
            if gridlines_info[gkey] is not None:
                use_gridlines_info[gkey] = gridlines_info[gkey]

    return use_gridlines_info


def compute_lat_auto_spacing(area_def):
    """Compute automatic spacing for latitude lines based on area definition."""
    minlat = area_def.area_extent_ll[1]
    maxlat = area_def.area_extent_ll[3]
    lat_extent = maxlat - minlat

    if lat_extent > 5:
        lat_spacing = int(lat_extent / 5)
    elif lat_extent > 2.5:
        lat_spacing = 1
    elif lat_extent == 0:
        lat_spacing = 2
    else:
        lat_spacing = lat_extent / 5.0
    # LOG.info(f"LAT spacing: {lat_spacing}")
    return lat_spacing


def compute_lon_auto_spacing(area_def):
    """Compute automatic spacing for longitude lines based on area definition."""
    minlon = pyresample.utils.wrap_longitudes(area_def.area_extent_ll[0])
    maxlon = pyresample.utils.wrap_longitudes(area_def.area_extent_ll[2])

    if minlon > maxlon and maxlon < 0:
        maxlon = maxlon + 360
    lon_extent = maxlon - minlon

    if lon_extent > 5:
        lon_spacing = int(lon_extent / 5)
    elif lon_extent > 2.5:
        lon_spacing = 1
    else:
        lon_spacing = lon_extent / 5.0
    # LOG.info(f"LON spacing: {lon_spacing}")
    return lon_spacing


def check_feature_annotator(feature_annotator):
    """Check that the provided feature_annotator plugin has all required fields.

    Parameters
    ----------
    feature_annotator : YamlPlugin
        A feature annotator plugin.

    Raises
    ------
    ValueError
        if any field is missing

    See Also
    --------
    geoips.image_utils.maps.get_feature_annotator
        For complete list of fields, and appropriate defaults
    """
    if feature_annotator is None:
        feature_annotator = feature_annotators.get_plugin("default").model_dump()
    spec = feature_annotator["spec"]

    feature_types = ["coastline", "borders", "rivers", "states"]
    for feature_name in feature_types:
        if feature_name not in spec:
            raise ValueError(
                f"Missing '{feature_name}' property in feature_annotator "
                f"named '{feature_annotator['name']}'"
            )
        if "enabled" not in spec[feature_name]:
            raise ValueError(
                f"Missing 'enabled' property of '{feature_name}' in feature_annotator "
                f"named '{feature_annotator['name']}'"
            )
        if spec[feature_name]["enabled"]:
            props = ["edgecolor", "linewidth"]
            for prop in props:
                if prop not in spec[feature_name]:
                    raise ValueError(
                        f"Missing '{prop}' property of "
                        f"'{feature_name}' in feature_annotator, "
                        f"named '{feature_annotator['name']}'."
                    )
    return feature_annotator


# def set_boundaries_info_dict(boundaries_info):
#     """Set the boundary information.
#
#     Set the final values for coastlines, states, countries plotting params,
#     pulling from argument and defaults.
#
#     Parameters
#     ----------
#     boundaries_info : dict
#         Dictionary of parameters for plotting gridlines.
#         The following fields are available.  If a field is not included in the
#         dictionary, the field is added to the return dictionary and the default
#         is used (see defaults in Notes below).
#
#     Returns
#     -------
#     use_boundaries_info : dict
#         boundaries_info dictionary, with fields as specified above.
#
#     Notes
#     -----
#     Defaults specified as::
#
#         boundaries_info['request_coastlines']       default True
#         boundaries_info['request_countries']        default True
#         boundaries_info['request_states']           default True
#         boundaries_info['request_rivers']           default True
#
#         boundaries_info['coastlines_linewidth']     default 2
#         boundaries_info['countries_linewidth']      default 1
#         boundaries_info['states_linewidth']         default 0.5
#         boundaries_info['rivers_linewidth']         default 0
#
#         boundaries_info['coastlines_color']         default 'red'
#         boundaries_info['countries_color']          default 'red'
#         boundaries_info['states_color']             default 'red'
#         boundaries_info['rivers_color']             default 'red'
#     """
#     use_boundaries_info = {}
#     use_boundaries_info["request_coastlines"] = True
#     use_boundaries_info["request_countries"] = True
#     use_boundaries_info["request_states"] = True
#     use_boundaries_info["request_rivers"] = True
#
#     use_boundaries_info["coastlines_linewidth"] = 2
#     use_boundaries_info["countries_linewidth"] = 1
#     use_boundaries_info["states_linewidth"] = 0.5
#     use_boundaries_info["rivers_linewidth"] = 0
#
#     use_boundaries_info["coastlines_color"] = "red"
#     use_boundaries_info["countries_color"] = "red"
#     use_boundaries_info["states_color"] = "red"
#     use_boundaries_info["rivers_color"] = "red"
#
#     # Grab any values that were passed
#     if boundaries_info is not None:
#         for bkey in boundaries_info.keys():
#             if boundaries_info[bkey] is not None:
#                 use_boundaries_info[bkey] = boundaries_info[bkey]
#
#     return use_boundaries_info


def draw_features(mapobj, curr_ax, feature_annotator, zorder=None):
    """Draw cartopy features.

    Draw features on specified cartopy map instance, based
    on specs found in the feature_annotator plugin.

    Parameters
    ----------
    mapobj : map object
        CRS object for plotting map features
    curr_ax : matplotlib.axes._axes.Axes
        matplotlib Axes object for plotting map features
    feature_annotator : dict
        Dictionary of parameters for plotting map features
    zorder : int, optional
        The matplotlib zorder

    See Also
    --------
    geoips.image_utils.maps.check_feature_annotator
          for required dictionary entries and defaults.
    """
    LOG.info("Drawing coastlines, countries, states, rivers")
    feature_annotator = check_feature_annotator(feature_annotator)

    # NOTE passing zorder=None is NOT the same as not passing zorder.
    # Ensure if zorder is passed, it is propagated to cartopy.
    extra_args = {}
    if zorder is not None:
        extra_args = {"zorder": zorder}

    LOG.info("    Plotting with cartopy")

    for name, feature in feature_annotator["spec"].items():
        feat = deepcopy(feature)
        # Need to make sure this isn't 'background' as this isn't a feature that can be
        # added to an axis. This is just the background color of where those features
        # will or will not be added
        if name != "background" and feat.pop("enabled"):
            curr_ax.add_feature(getattr(cfeature, name.upper()), **feat, **extra_args)


def draw_gridlines(mapobj, area_def, curr_ax, gridline_annotator, zorder=None):
    """Draw gridlines on map object.

    Draw gridlines on a cartopy map object, as specified by a
    gridline_annotator plugin instance

    Parameters
    ----------
    mapobj : map object
        CRS object for plotting gridlines
    area_def : AreaDefinition
        pyresample AreaDefinition object
    curr_ax : matplotlib.axes._axes.Axes
        matplotlib Axes object for plotting gridlines
    gridline_annotator : YamlPlugin
        A gridline_annotator plugin instance
    zorder : int, optional
        The matplotlib zorder value

    See Also
    --------
    geoips.image_utils.maps.get_gridlines_info_dict
        For complete list of fields, and appropriate default
    """
    LOG.info("Drawing gridlines")
    gridline_annotator = check_gridline_annotator(gridline_annotator)

    # NOTE passing zorder=None is NOT the same as not passing zorder.
    # Ensure if zorder is passed, it is propagated to cartopy.
    extra_args = {}
    if zorder is not None:
        extra_args = {"zorder": zorder}

    LOG.info("    Plotting with cartopy")

    spec = gridline_annotator["spec"]
    labels = spec["labels"]

    if "xpadding" in labels.keys():
        extra_args["xpadding"] = labels["xpadding"]
    if "ypadding" in labels.keys():
        extra_args["ypadding"] = labels["ypadding"]

    # Note: linestyle is specified by a tuple: (offset, (pixels_on,
    # pixels_off, pxon, pxoff)), etc
    lines = deepcopy(spec["lines"])
    lines["linestyle"] = (0, tuple(lines["linestyle"]))
    glnr = curr_ax.gridlines(draw_labels=True, **lines, **extra_args)

    # Default to False, unless set in argument
    glnr.top_labels = labels["top"]
    glnr.bottom_labels = labels["bottom"]
    glnr.left_labels = labels["left"]
    glnr.right_labels = labels["right"]

    spacing = spec["spacing"]
    lat_ticks = parallels(area_def, spacing["latitude"])
    lon_ticks = meridians(area_def, spacing["longitude"])

    LOG.debug(f"Lon Ticks: {lon_ticks}")
    glnr.xlocator = mticker.FixedLocator(lon_ticks)
    LOG.debug(f"Lat Ticks: {lat_ticks}")
    glnr.ylocator = mticker.FixedLocator(lat_ticks)

    glnr.xformatter = LONGITUDE_FORMATTER
    glnr.yformatter = LATITUDE_FORMATTER
    glnr.xlabel_style = {"rotation": 0}
    glnr.ylabel_style = {"rotation": 0}

    for style_arg in gridline_annotators.label_kwargs.keys():
        # If a (x/y)label_style kwarg is present in the gridline annotator's label
        # object, than make sure to apply that argument now. Ie. color of the label,
        # it's offset, etc. See geoips.schema.gridline_annotators.cartopy:labels for
        # more information.
        if style_arg in labels.keys():
            glnr.xlabel_style[style_arg] = labels[style_arg]
            glnr.ylabel_style[style_arg] = labels[style_arg]
