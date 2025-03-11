# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module for generating specific colormaps on the fly."""
# Installed Libraries
import logging
import ast

LOG = logging.getLogger(__name__)


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
    from matplotlib import pyplot as plt

    # cmap = cm.ScalarMappable(norm=colors.NoNorm(), cm.get_cmap(cmap_name))
    mpl_cmap = plt.get_cmap(cmap_name)

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


def from_ascii(fname, cmap_name=None, reverse=False):
    """Create a ListedColormap instance from an ASCII file of RGB values.

    Parameters
    ----------
    fname : str
        Full path to ascii RGB colortable file
    cmap_name : str, default=None (basename(fname))
        Identifying name of colormap - if None, default to basename(fname)
    reverse : bool, default=False
        If True, reverse the colormap

    Returns
    -------
    cmap : ListedColormap object
        If cmap_name not specified, the colormap name will be the os.path.basename
        of the file.

    Notes
    -----
     * Lines preceded by '#' are ignored.
     * 0-255 or 0-1.0 RGB values (0-255 values are normalized to 0-1.0
       for matplotlib usage)
     * One white space delimited RGB value per line
    """
    # Read data from ascii file into an NLines by 3 float array, skipping
    # lines preceded by "#"
    lines = []
    with open(fname) as palette:
        for line in palette.readlines():
            if line.strip()[0] != "#":
                lines += [line]

    import numpy

    carray = numpy.zeros([len(lines), len(lines[0].strip().split())])
    # carray = numpy.zeros([len(lines), 3])
    for num, line in enumerate(lines):
        carray[num, :] = [float(val) for val in line.strip().split()]

    # Normalize from 0-255 to 0.0-1.0
    if carray.max() > 1.0:
        carray /= 255.0

    # Test to be sure all color array values are between 0.0 and 1.0
    if not (carray.min() >= 0.0 and carray.max() <= 1.0):
        raise ValueError("All values in carray must be between 0.0 and 1.0.")

    if reverse is True:
        carray = numpy.flipud(carray)

    from matplotlib import colors
    from os.path import basename as pathbasename

    if cmap_name is not None:
        cmap_name = pathbasename(fname)
    cmap = colors.ListedColormap(carray, name=cmap_name)
    return cmap


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
