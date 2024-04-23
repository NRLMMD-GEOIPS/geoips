"""Generate dict of colormap info based on ascii-palette plugins."""

from geoips.interfaces import ascii_palettes

interface = "colormappers"
family = "matplotlib"
name = "ascii_based"

def call(
    cmap_name="tpw_cimss",
    data_range=None,
    create_colorbar=True,
    cbar_label=None,
    cbar_ticks=None,
    cbar_tick_labels=None,
    cbar_spacing="proportional",
    cbar_full_width=False,
    colorbar_kwargs=None,
    set_ticks_kwargs=None,
    set_label_kwargs=None,
):
    """Set the matplotlib colors information for matplotlib linear norm cmaps.

    This information used in both colorbar and image production throughout
    GeoIPS image output specifications.

    Parameters
    ----------
    cmap_name : str, default="tpw_cimss"
        * Specify the name of the resulting ascii palette plugin.
    data_range : list, default=None
        * [min_val, max_val],
            matplotlib.colors.Normalize(vmin=min_val, vmax=max_val)
        * If data_range not specified, vmin and vmax both None.
    cbar_label : str, default=None
        * Positional parameter passed to cbar.set_label
        * If specified, use cbar_label string as colorbar label.
    create_colorbar : bool, default=True
        * Specify whether the image should contain a colorbar or not.
    cbar_ticks : list, default=None
        * Positional parameter passed to cbar.set_ticks
        * Specify explicit list of ticks to include for colorbar.
        * None indicates ticks at int(min) and int(max) values
    cbar_tick_labels : list, default=None
        * "labels" argument to pass to cbar.set_ticks.
        * can also specify directly within "set_ticks_kwargs"
    cbar_spacing : string, default="proportional"
        * "spacing" argument to pass to fig.colorbar
        * can also specify directly within "colorbar_kwargs"
    cbar_full_width : bool, default=True
        * Extend the colorbar across the full width of the image.
    colorbar_kwargs : dict, default=None
        * keyword arguments to pass through directly to "fig.colorbar"
    set_ticks_kwargs : dict, default=None
        * keyword arguments to pass through directly to "cbar.set_ticks"
    set_label_kwargs : dict, default=None
        * keyword arguments to pass through directly to "cbar.set_label"

    Returns
    -------
    mpl_colors_info : dict
        * Specifies matplotlib Colors parameters for use in both plotting and
            colorbar generation

    See Also
    --------
    :ref:`api`
        See geoips.image_utils.mpl_utils.create_colorbar for field descriptions.
    """
    palette_plug = ascii_palettes.get_plugin(cmap_name)
    opt_args = {
        "data_range": data_range,
        "cbar_label": cbar_label,
        "create_colorbar": create_colorbar,
        "cbar_ticks": cbar_ticks,
        "cbar_tick_labels": cbar_tick_labels,
        "cbar_spacing": cbar_spacing,
        "cbar_full_width": cbar_full_width,
        "colorbar_kwargs": colorbar_kwargs,
        "set_ticks_kwargs": set_ticks_kwargs,
        "set_label_kwargs": set_label_kwargs,
    }
    return palette_plug(**opt_args)
