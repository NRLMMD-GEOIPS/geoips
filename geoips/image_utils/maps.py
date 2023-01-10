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

"""matplotlib geographic map (basemap or cartopy) utilities."""

# Python Standard Libraries
import logging

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


def area_def2mapobj(area_def):
    """
    Convert to map object.

    Convert pyresample AreaDefinition object to a cartopy CRS or Basemap
    object. Default to basemap.

    Parameters
    ----------
    area_def : AreaDefinition
        pyresample AreaDefinition object

    Returns
    -------
    mapobj : CRS map object
        Either Basemap instance (if Basemap is installed), or cartopy
        CRS object.
    """
    try:
        # old pyresample.area_def2basemap appears to fail over the dateline.
        # Created our own for now
        # boundary resolution must be one of 'c','l','i','h' or 'f'
        mapobj = area_def2basemap(
            area_def, fix_aspect=False, suppress_ticks=True, resolution="i"
        )
    except ImportError:
        LOG.info("Basemap not installed, using cartopy")
        mapobj = area_def.to_cartopy_crs()
    return mapobj


def area_def2basemap(area_def, **kwargs):
    """
    Get Basemap object from AreaDefinition.

    Parameters
    ----------
    area_def : object
        geometry.AreaDefinition object

    Returns
    -------
    bmap : Basemap object
    """
    from mpl_toolkits.basemap import Basemap

    try:
        avar, bvar = ellps2axis(area_def.proj_dict["ellps"])
        rsphere = (avar, bvar)
    except KeyError:
        try:
            avar = float(area_def.proj_dict["a"])
            try:
                bvar = float(area_def.proj_dict["b"])
                rsphere = (avar, bvar)
            except KeyError:
                rsphere = avar
        except KeyError:
            # Default to WGS84 ellipsoid
            avar, bvar = ellps2axis("wgs84")
            rsphere = (avar, bvar)

    # Add projection specific basemap args to args passed to function
    basemap_args = kwargs
    basemap_args["rsphere"] = rsphere

    if area_def.proj_dict["proj"] in ("ortho", "geos", "nsper"):
        llcrnrx, llcrnry, urcrnrx, urcrnry = area_def.area_extent
        basemap_args["llcrnrx"] = llcrnrx
        basemap_args["llcrnry"] = llcrnry
        basemap_args["urcrnrx"] = urcrnrx
        basemap_args["urcrnry"] = urcrnry
    else:
        llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat = area_def.area_extent_ll
        # If ur < ll, then we need to swap
        if urcrnrlon < llcrnrlon:
            if area_def.x_size * area_def.pixel_size_x < 20000000:
                basemap_args["llcrnrlon"] = llcrnrlon % 360
                basemap_args["urcrnrlon"] = urcrnrlon % 360
        else:
            basemap_args["llcrnrlon"] = llcrnrlon
            basemap_args["urcrnrlon"] = urcrnrlon
        basemap_args["llcrnrlat"] = llcrnrlat
        basemap_args["urcrnrlat"] = urcrnrlat

    if area_def.proj_dict["proj"] == "eqc":
        basemap_args["projection"] = "cyl"
    else:
        basemap_args["projection"] = area_def.proj_dict["proj"]

    # Try adding potentially remaining args
    for key in ("lon_0", "lat_0", "lon_1", "lat_1", "lon_2", "lat_2", "lat_ts"):
        try:
            basemap_args[key] = float(area_def.proj_dict[key])
        except KeyError:
            pass

    return Basemap(**basemap_args)


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
    from math import ceil
    from numpy import arange
    from numpy.ma import masked_greater

    lats = area_def.get_lonlats()[1]
    mlats = masked_greater(lats, 90)
    min_parallel = ceil(float(mlats.min()) / grid_size) * grid_size
    max_parallel = ceil(float(mlats.max()) / grid_size) * grid_size
    lat_ticks = arange(min_parallel, max_parallel, grid_size)
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
    import numpy

    corners = area_def.corners
    lons = [numpy.rad2deg(corn.lon) for corn in corners]
    llcrnrlon = lons[3]
    urcrnrlon = lons[1]

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

    from math import ceil

    min_meridian = ceil(float(llcrnrlon) / grid_size) * grid_size
    max_meridian = ceil(float(urcrnrlon) / grid_size) * grid_size
    meridians_to_draw = numpy.arange(min_meridian, max_meridian, grid_size)
    import pyresample

    meridians_to_draw = pyresample.utils.wrap_longitudes(meridians_to_draw)
    LOG.info(
        "List of meridians: min/max %s, %s", meridians_to_draw[0], meridians_to_draw[-1]
    )
    meridians_to_draw = [round(lon_tick, 1) for lon_tick in meridians_to_draw]
    return meridians_to_draw


def check_gridlines_info_dict(gridlines_info):
    """
    Check gridlines_info dictionary for that all required fields.

    Parameters
    ----------
    gridlines_info : dict
        dictionary to check for required fields. For complete list of
        fields, and appropriate defaults, see
        geoips.image_utils.maps.get_gridlines_info_dict

    Raises
    ------
    ValueError
        If required field is missing
    """
    required_fields = [
        "grid_lat_spacing",
        "grid_lon_spacing",
        "grid_lat_fontsize",
        "grid_lon_fontsize",
        "grid_lat_xoffset",
        "grid_lon_xoffset",
        "grid_lat_yoffset",
        "grid_lon_yoffset",
        "left_label",
        "right_label",
        "top_label",
        "bottom_label",
        "grid_lat_linewidth",
        "grid_lon_linewidth",
        "grid_lat_color",
        "grid_lon_color",
        "grid_lat_dashes",
        "grid_lon_dashes",
    ]
    for key in required_fields:
        if key not in gridlines_info:
            raise ValueError(
                "Missing gridlines_info entry {0}, required_fields {1}".format(
                    key, required_fields
                )
            )


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


def check_boundaries_info_dict(boundaries_info):
    """
    Check boundaries_info dictionary for required fields.

    Parameters
    ----------
    boundaries_info : dict
        dictionary to check for required fields.

    Raises
    ------
    ValueError
        if any field is missing

    See Also
    --------
    geoips.image_utils.maps.get_boundaries_info_dict
        For complete list of fields, and appropriate defaults
    """
    required_fields = [
        "request_coastlines",
        "coastlines_color",
        "coastlines_linewidth",
        "request_rivers",
        "rivers_color",
        "rivers_linewidth",
        "request_states",
        "states_color",
        "states_linewidth",
        "request_countries",
        "countries_color",
        "countries_linewidth",
    ]
    for key in required_fields:
        if key not in boundaries_info:
            raise ValueError(
                "Missing boundaries_info entry {0}, required_fields {1}".format(
                    key, required_fields
                )
            )


def set_boundaries_info_dict(boundaries_info):
    """
    Set the boundary information.

    Set the final values for coastlines, states, countries plotting params,
    pulling from argument and defaults.

    Parameters
    ----------
    boundaries_info : dict
        Dictionary of parameters for plotting gridlines.
        The following fields are available.  If a field is not included in the
        dictionary, the field is added to the return dictionary and the default
        is used (see defaults in Notes below).

    Returns
    -------
    use_boundaries_info : dict
        boundaries_info dictionary, with fields as specified above.

    Notes
    -----
    Defaults specified as::

        boundaries_info['request_coastlines']       default True
        boundaries_info['request_countries']        default True
        boundaries_info['request_states']           default True
        boundaries_info['request_rivers']           default True

        boundaries_info['coastlines_linewidth']     default 2
        boundaries_info['countries_linewidth']      default 1
        boundaries_info['states_linewidth']         default 0.5
        boundaries_info['rivers_linewidth']         default 0

        boundaries_info['coastlines_color']         default 'red'
        boundaries_info['countries_color']          default 'red'
        boundaries_info['states_color']             default 'red'
        boundaries_info['rivers_color']             default 'red'
    """
    use_boundaries_info = {}
    use_boundaries_info["request_coastlines"] = True
    use_boundaries_info["request_countries"] = True
    use_boundaries_info["request_states"] = True
    use_boundaries_info["request_rivers"] = True

    use_boundaries_info["coastlines_linewidth"] = 2
    use_boundaries_info["countries_linewidth"] = 1
    use_boundaries_info["states_linewidth"] = 0.5
    use_boundaries_info["rivers_linewidth"] = 0

    use_boundaries_info["coastlines_color"] = "red"
    use_boundaries_info["countries_color"] = "red"
    use_boundaries_info["states_color"] = "red"
    use_boundaries_info["rivers_color"] = "red"

    # Grab any values that were passed
    if boundaries_info is not None:
        for bkey in boundaries_info.keys():
            if boundaries_info[bkey] is not None:
                use_boundaries_info[bkey] = boundaries_info[bkey]

    return use_boundaries_info


def draw_boundaries(mapobj, curr_ax, boundaries_info, zorder=None):
    """
    Draw basemap or cartopy boundaries.

    Draw boundaries on specified map instance (basemap or cartopy), based
    on specs found in boundaries_info

    Parameters
    ----------
    mapobj : map object
        Basemap or CRS object for plotting boundaries
    curr_ax : matplotlib.axes._axes.Axes
        matplotlib Axes object for plotting boundaries
    zorder : int, optional
        The matplotlib zorder
    boundaries_info : dict
        Dictionary of parameters for plotting map boundaries.

    See Also
    --------
    geoips.image_utils.maps.check_boundaries_info_dict
          for required dictionary entries and defaults.
    """
    LOG.info("Drawing coastlines, countries, states, rivers")
    check_boundaries_info_dict(boundaries_info)

    # NOTE passing zorder=None is NOT the same as not passing zorder.
    # Ensure if zorder is passed, it is propagated to cartopy.
    extra_args = {}
    if zorder is not None:
        extra_args = {"zorder": zorder}

    if is_crs(mapobj):
        LOG.info("    Plotting with cartopy")
        import cartopy.feature as cfeature

        if boundaries_info["request_coastlines"]:
            curr_ax.add_feature(
                cfeature.COASTLINE,
                edgecolor=boundaries_info["coastlines_color"],
                linewidth=boundaries_info["coastlines_linewidth"],
                **extra_args,
            )
        if boundaries_info["request_countries"]:
            curr_ax.add_feature(
                cfeature.BORDERS,
                edgecolor=boundaries_info["countries_color"],
                linewidth=boundaries_info["countries_linewidth"],
                **extra_args,
            )
        if boundaries_info["request_states"]:
            curr_ax.add_feature(
                cfeature.STATES,
                edgecolor=boundaries_info["states_color"],
                linewidth=boundaries_info["states_linewidth"],
                **extra_args,
            )
        if boundaries_info["request_rivers"]:
            curr_ax.add_feature(
                cfeature.RIVERS,
                edgecolor=boundaries_info["rivers_color"],
                linewidth=boundaries_info["rivers_linewidth"],
                **extra_args,
            )
    else:
        LOG.info("    Plotting with basemap")
        if boundaries_info["request_coastlines"]:
            mapobj.drawcoastlines(
                ax=curr_ax,
                linewidth=boundaries_info["coastlines_linewidth"],
                color=boundaries_info["coastlines_color"],
            )
        if boundaries_info["request_countries"]:
            mapobj.drawcountries(
                ax=curr_ax,
                linewidth=boundaries_info["countries_linewidth"],
                color=boundaries_info["countries_color"],
            )
        if boundaries_info["request_states"]:
            mapobj.drawstates(
                ax=curr_ax,
                linewidth=boundaries_info["states_linewidth"],
                color=boundaries_info["states_color"],
            )
        if boundaries_info["request_rivers"]:
            mapobj.drawrivers(
                ax=curr_ax,
                linewidth=boundaries_info["rivers_linewidth"],
                color=boundaries_info["rivers_color"],
            )


def draw_gridlines(mapobj, area_def, curr_ax, gridlines_info, zorder=None):
    """
    Draw gridlines on map object.

    Draw gridlines on either cartopy or Basemap map object, as specified
    by gridlines_info

    Parameters
    ----------
    mapobj : map object
        Basemap or CRS object for plotting boundaries
    area_def : AreaDefinition
        pyresample AreaDefinition object
    curr_ax : matplotlib.axes._axes.Axes
        matplotlib Axes object for plotting boundaries
    gridlines_info : dict
        dictionary to check for required fields.
    zorder : int, optional
        The matplotlib zorder value

    See Also
    --------
    geoips.image_utils.maps.get_gridlines_info_dict
        For complete list of fields, and appropriate default
    """
    LOG.info("Drawing gridlines")
    check_gridlines_info_dict(gridlines_info)

    # NOTE passing zorder=None is NOT the same as not passing zorder.
    # Ensure if zorder is passed, it is propagated to cartopy.
    extra_args = {}
    if zorder is not None:
        extra_args = {"zorder": zorder}

    if is_crs(mapobj):
        LOG.info("    Plotting with cartopy")
        # import cartopy.crs as ccrs
        # import cartopy.mpl.ticker as cticker
        import matplotlib.ticker as mticker
        from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

        # Note: linestyle is specified by a tuple: (offset, (pixels_on,
        # pixels_off, pxon, pxoff)), etc
        linestyle_lat = (0, tuple(gridlines_info["grid_lat_dashes"]))
        # linestyle_lon = (0, tuple(grid_lon_dashes))
        glnr = curr_ax.gridlines(
            color=gridlines_info["grid_lat_color"],
            draw_labels=True,
            linewidth=gridlines_info["grid_lat_linewidth"],
            linestyle=linestyle_lat,
            **extra_args,
        )

        # Default to False, unless set in argument
        glnr.top_labels = False
        glnr.bottom_labels = False
        glnr.left_labels = False
        glnr.right_labels = False

        if gridlines_info["top_label"]:
            LOG.debug("Adding top labels")
            glnr.top_labels = True
        if gridlines_info["bottom_label"]:
            LOG.debug("Adding bottom labels")
            glnr.bottom_labels = True
        if gridlines_info["left_label"]:
            LOG.debug("Adding left labels")
            glnr.left_labels = True
        if gridlines_info["right_label"]:
            LOG.debug("Adding right labels")
            glnr.right_labels = True

        lat_ticks = parallels(area_def, gridlines_info["grid_lat_spacing"])
        lon_ticks = meridians(area_def, gridlines_info["grid_lon_spacing"])
        LOG.debug(f"Lon Ticks: {lon_ticks}")
        glnr.xlocator = mticker.FixedLocator(lon_ticks)
        LOG.debug(f"Lat Ticks: {lat_ticks}")
        glnr.ylocator = mticker.FixedLocator(lat_ticks)
        # gl.xformatter = cticker.LongitudeFormatter()
        # gl.yformatter = cticker.LatitudeFormatter()
        glnr.xformatter = LONGITUDE_FORMATTER
        glnr.yformatter = LATITUDE_FORMATTER
        glnr.xlabel_style = {"rotation": 0}
        glnr.ylabel_style = {"rotation": 0}

        # ax.set_xticks(lon_ticks, crs=mapobj)
        # ax.set_xticklabels(lon_ticks)
        # ax.set_yticks(lat_ticks, crs=mapobj)
        # ax.set_yticklabels(lat_ticks)
        # ax.yaxis.tick_right()

        # lon_formatter = cticker.LongitudeFormatter()
        # lat_formatter = cticker.LatitudeFormatter()
        # ax.xaxis.set_major_formatter(lon_formatter)
        # ax.yaxis.set_major_formatter(lat_formatter)
        # ax.grid(linewidth=grid_lat_linewidth, color=grid_lat_color,
        #         linestyle=linestyle_lat,
        #         crs=mapobj)

    else:
        LOG.info("    Plotting with basemap")
        mapobj.drawparallels(
            parallels(area_def, gridlines_info["grid_lat_spacing"]),
            ax=curr_ax,
            linewidth=gridlines_info["grid_lat_linewidth"],
            dashes=gridlines_info["grid_lat_dashes"],
            labels=[gridlines_info["left_label"], gridlines_info["right_label"], 0, 0],
            color=gridlines_info["grid_lat_color"],
            xoffset=gridlines_info["grid_lat_xoffset"],
            yoffset=gridlines_info["grid_lat_yoffset"],
            fontsize=gridlines_info["grid_lat_fontsize"],
        )
        mapobj.drawmeridians(
            meridians(area_def, gridlines_info["grid_lon_spacing"]),
            ax=curr_ax,
            linewidth=gridlines_info["grid_lon_linewidth"],
            dashes=gridlines_info["grid_lon_dashes"],
            labels=[0, 0, gridlines_info["top_label"], gridlines_info["bottom_label"]],
            color=gridlines_info["grid_lon_color"],
            yoffset=gridlines_info["grid_lon_yoffset"],
            xoffset=gridlines_info["grid_lon_xoffset"],
            fontsize=gridlines_info["grid_lon_fontsize"],
        )
