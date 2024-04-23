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

"""Module for generating specific colormaps on the fly."""
# Installed Libraries
import logging
import ast
from matplotlib import cm
import numpy
from matplotlib import colors
from os.path import basename

from geoips.errors import AsciiPaletteError
from geoips.interfaces import ascii_palettes

LOG = logging.getLogger(__name__)


def get_color_palette(source, name):
    """Get the associated color-palette given a name and source name.

    Where 'color-palette' is a colormap defined from a given source. This source name
    can be one of ['matplotlib' / 'mpl', 'geoips', 'ascii'].

    If matplotlib is the source name, then retrieve the appropriate matplotlib named
    colormap.

    If the source name is geoips, retrieve the appropriate GeoIPS Colormapper-plugin,
    Colormap Attribute.

    If the source name is ascii, retrieve the appropriate Matplotlib Colormap generated
    from the ascii palette plugin.

    Parameters
    ----------
    source: str
        - The source name of the color palette one of:
          ['matplotlib' / 'mpl', 'ascii']
    name: str
        - The name of the color palette we'd like to retrieve.

    Returns
    -------
    cmap: Colormap
        - Will either be a Matplotlib Named Colormap or a Matplotlib Colormap Derived
          from the ascii palette plugin.
    """
    if source == "matplotlib" or source == "mpl":
        try:
            cmap = cm.get_cmap(name)
        except ValueError:
            raise ValueError(f"Colormap {name} not found in source {source}")
    elif source == "ascii":
        ascii_plugin = ascii_palettes.get_plugin(name)
        # Now get the colormap created from the defined ascii palette plugin
        cmap = ascii_plugin.colormap
    elif source == "geoips":
        raise ValueError(
            f"Source '{source}' is no longer supported. Please either use "
            "'matplotlib' / 'mpl', or 'ascii', or consider using a different GeoIPS "
            "Colormapper plugin."
        )
    else:
        raise ValueError(
            f"Uknown colormap source '{source}'; must be one of "
            "'matplotlib' / 'mpl', 'geoips', or 'ascii'"
        )
    return cmap


def set_matplotlib_colors_rgb():
    """
    Create matplotlib Colors parameters dictionary.

    For rgb imagery, we require no color information (it is entirely
    specified by the RGB(A) arrays).

    Returns
    -------
    mpl_colors_info : dict
        Specifies matplotlib Colors parameters for use in both plotting
        and colorbar generation. For RGBA arrays, all fields are "None".
    """
    mpl_colors_info = {
        "cmap": None,
        "norm": None,
        "cbar_ticks": None,
        "cbar_tick_labels": None,
        "cbar_label": None,
        "boundaries": None,
        "cbar_spacing": "proportional",
        "colorbar": False,
    }
    return mpl_colors_info


def set_matplotlib_colors_standard(
    data_range, cmap_name="Greys", cbar_label=None, create_colorbar=True
):
    """
    Set the matplotlib colors information.

    For use in colorbar and image production.

    Parameters
    ----------
    data_range : list
        the minimum and maximum value for the data range
        [min_val, max_val]
    cmap_name : str, default='Greys'
        Specify the standard matplotlib colormap
    cbar_label : str, optional
        If specified, use cbar_label string as colorbar label
    create_colorbar : bool, default=True
        Specify whether the image should contain a colorbar or not

    Returns
    -------
    mpl_colors_info : dict
        Specifies matplotlib Colors parameters for use in both plotting
        and colorbar generation.
        See geoips.image_utils.mpl_utils.create_colorbar for field
        descriptions.
    """
    min_val = data_range[0]
    max_val = data_range[1]
    from matplotlib import cm

    # cmap = cm.ScalarMappable(norm=colors.NoNorm(), cm.get_cmap(cmap_name))
    mpl_cmap = cm.get_cmap(cmap_name)

    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_val, vmax=max_val)
    mpl_ticks = [min_val, max_val]

    # Must be uniform or proportional, None not valid for Python 3
    cbar_spacing = "proportional"
    mpl_tick_labels = None
    mpl_boundaries = None

    mpl_colors_info = {
        "cmap": mpl_cmap,
        "norm": mpl_norm,
        "cbar_ticks": mpl_ticks,
        "cbar_tick_labels": mpl_tick_labels,
        "cbar_label": cbar_label,
        "boundaries": mpl_boundaries,
        "cbar_spacing": cbar_spacing,
        "colorbar": create_colorbar,
    }

    return mpl_colors_info


def set_mpl_colors_info_dict(
    cmap,
    norm,
    cbar_ticks,
    cbar_tick_labels=None,
    boundaries=None,
    cbar_label=None,
    cbar_spacing="proportional",
    create_colorbar=True,
    cbar_full_width=False,
):
    """
    Create the mpl_colors_info dictionary directly from passed arguments.

    Parameters
    ----------
    cmap : Colormap
        This is a valid matplotlib cm Colormap object that can be used for
        both plotting and colorbar creation.
    norm : Normalize
        This is a valid matplotlib Normalize object that can be used for
        both plotting and colorbar creation.
    cbar_ticks : list
        List of values where tick marks should be placed on colorbar
    cbar_tick_labels : list, optional
        List of tick label values
    boundaries : list, optional
        List of boundaries to use in matplotlib plotting and colorbar
        creation
    cbar_label, optional
        The label for the colorbar
    cbar_spacing : str, default='proportional'
        One of 'proportional' or 'uniform'
    create_colorbar : bool, default=True
        True if colorbar should be created with the set of color info, False otherwise
    cbar_full_width : bool, default=False
        True if colorbar should be full width of figure, center 50% if False

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of mpl_colors_info for use in plotting and colorbar
        creation.
    """
    mpl_colors_info = {}
    mpl_colors_info["cmap"] = cmap
    mpl_colors_info["norm"] = norm
    mpl_colors_info["cbar_ticks"] = cbar_ticks
    mpl_colors_info["cbar_tick_labels"] = cbar_tick_labels
    mpl_colors_info["cbar_label"] = cbar_label
    mpl_colors_info["boundaries"] = boundaries
    mpl_colors_info["cbar_spacing"] = cbar_spacing
    mpl_colors_info["colorbar"] = create_colorbar
    mpl_colors_info["cbar_full_width"] = cbar_full_width
    return mpl_colors_info


def create_linear_segmented_colormap(
    cmapname, min_val, max_val, transition_vals, transition_colors
):
    """
    Create a LinearSegmentedColormap instance.

    Parameters
    ----------
    cmapname : str
        Name to attach to the matplotlib.color ColorMap object
    min_val : float
        Overall minimum value for the colormap
        Range must be normalized between 0 and 1
    max_val : float
        Overall maximum value for the colormap
        Range must be normalized between 0 and 1
    transition_vals : array-like
        A list of value ranges specified as tuples for generating a
        specific range of colors ie [(0, 10), (10, 30), (30, 60)]
    transition_colors : array-like
        A list of color ranges specified as tuples for generating a
        specific range of colors corresponding to the transition_vals
        (see Notes below)

    Returns
    -------
    cm : LinearSegmentedColormap
        matplotlib colormap object

    Notes
    -----
    Transition colors specified as::

            [('yellow', 'orange'),
             ('pink', 'red'),
             ('violet', 'purple')]

    Where::

        TRANSITIONPOINT1 = 0.0
        TRANSITIONPOINT4 = 1.0
        cmdict = { 'red' :  ((TRANSITIONPOINT1, IGNORED, 1to2STARTCOLOR),
                         (TRANSITIONPOINT2, 1to2ENDCOLOR, 2to3STARTCOLOR),
                         (TRANSITIONPOINT3, 2to3ENDCOLOR, 3to4STARTCOLOR),
                         (TRANSITIONPOINT4, 3to4ENDCOLOR, IGNORED)),
               'green' :  ((TRANSITIONPOINT1, IGNORED, 1to2STARTCOLOR),
                         (TRANSITIONPOINT2, 1to2ENDCOLOR, 2to3STARTCOLOR),
                         (TRANSITIONPOINT3, 2to3ENDCOLOR, 3to4STARTCOLOR),
                         (TRANSITIONPOINT4, 3to4ENDCOLOR, IGNORED)),

               'blue' :  ((TRANSITIONPOINT1, IGNORED, 1to2STARTCOLOR),
                         (TRANSITIONPOINT2, 1to2ENDCOLOR, 2to3STARTCOLOR),
                         (TRANSITIONPOINT3, 2to3ENDCOLOR, 3to4STARTCOLOR),
                         (TRANSITIONPOINT4, 3to4ENDCOLOR, IGNORED)),
            }
    """
    from matplotlib.colors import ColorConverter, LinearSegmentedColormap

    # Sort transitions on start_val
    bluetuple = ()
    greentuple = ()
    redtuple = ()
    start_color = None
    end_color = None
    old_end_color = [0, 0, 0]
    for transition_val, transition_color in zip(transition_vals, transition_colors):
        start_val = transition_val[0]
        end_val = transition_val[1]
        tstart_color = transition_color[0]
        tend_color = transition_color[1]
        # Must start with 0.0 !
        transition_point = (start_val - min_val) / float((max_val - min_val))
        cc = ColorConverter()
        # Convert start/end color to string, tuple, whatever matplotlib can use.
        try:
            start_color = cc.to_rgb(str(tstart_color))
        except ValueError:
            # Allow for tuples as well as string representations
            start_color = cc.to_rgb(ast.literal_eval(str(tstart_color)))
        try:
            end_color = cc.to_rgb(str(tend_color))
        except ValueError:
            end_color = cc.to_rgb(ast.literal_eval(str(tend_color)))
        bluetuple += ((transition_point, old_end_color[2], start_color[2]),)
        redtuple += ((transition_point, old_end_color[0], start_color[0]),)
        greentuple += ((transition_point, old_end_color[1], start_color[1]),)
        LOG.info(
            "    Transition point: "
            + str(transition_point)
            + ": "
            + str(start_val)
            + " to "
            + str(end_val)
        )
        LOG.info(
            "        Start color: %-10s %-40s", str(tstart_color), str(start_color)
        )
        LOG.info("        End color:   %-10s %-40s", str(tend_color), str(end_color))
        old_end_color = end_color
    # Must finish with 1.0 !
    transition_point = (end_val - min_val) / float((max_val - min_val))
    bluetuple += ((transition_point, old_end_color[2], start_color[2]),)
    redtuple += ((transition_point, old_end_color[0], start_color[0]),)
    greentuple += ((transition_point, old_end_color[1], start_color[1]),)

    cmdict = {"red": redtuple, "green": greentuple, "blue": bluetuple}

    cm = LinearSegmentedColormap(cmapname, cmdict)

    return cm
