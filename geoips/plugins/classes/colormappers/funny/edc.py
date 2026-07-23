"""Module containing colormap for Explosive Diarrhea Colormap (EDC)."""  # NOQA

import logging

from geoips.image_utils.colormap_utils import create_linear_segmented_colormap
from geoips.interfaces.class_based.colormappers import BaseColormapperPlugin

LOG = logging.getLogger(__name__)


class ExplosiveDiarrheaColormapperPlugin(BaseColormapperPlugin):
    """Explosive Diarrhea Colormapper Plugin.

    Makes use of USA Today's colormap tracking cyclophora outbreak alongside the
    bristol stool chart.
    """

    interface = "colormappers"
    family = "matplotlib"
    name = "edc"

    def call(self, data_range=[-15, 15]):
        """Explosive Diarrhea Colormap.

        Parameters
        ----------
        data_range : list of float, default=[-100.0, 40.0]
            Min and max value for colormap.
            Ensure the data range matches the range of the algorithm specified
            for use with this colormap

        Returns
        -------
        mpl_colors_info : dict
            Dictionary of matplotlib plotting parameters, to ensure consistent image
            output
        """
        min_val = data_range[0]
        max_val = data_range[1]

        transition_vals = [
            (min_val, min_val / 2),
            (min_val / 2, 0),
            (0, max_val / 2),
            (max_val / 2, max_val),
        ]

        # Define the colors corresponding to the colorbar
        transition_colors = [
            (
                (226 / 255, 211 / 255, 164 / 255),  # white-brown: -15
                (207 / 255, 179 / 255, 134 / 255),  # light-brown: -10
            ),
            (
                (207 / 255, 179 / 255, 134 / 255),  # light-brown: -10
                (188 / 255, 147 / 255, 106 / 255),  # medium-brown: -5
            ),
            (
                (188 / 255, 147 / 255, 106 / 255),  # medium-brown: -5
                (170 / 255, 116 / 255, 77 / 255),  # brown: 0
            ),
            (
                (170 / 255, 116 / 255, 77 / 255),  # brown: 0
                (127 / 255, 70 / 255, 39 / 255),  # dark-brown: 5
            ),
        ]

        # special selection of label
        ticks = [
            min_val,
            (min_val / 3) * 2,
            min_val / 3,
            0,
            max_val / 3,
            (max_val / 3) * 2,
            max_val,
        ]
        tick_labels = [
            "Pebbly Hard Lumps",
            "Hard & Lumpy Sausage",
            "Smooth, Cracked Sausage",
            "Smooth, Soft & Snakelike",
            "Soft Blobs",
            "Fluffy, Mushy Pieces",
            "Watery, No Solid Pieces",
        ]

        LOG.info("Setting cmap")
        # Create a custom colormap
        mpl_cmap = create_linear_segmented_colormap(
            "explosive_diarrhea", min_val, max_val, transition_vals, transition_colors
        )

        LOG.info("Setting norm")
        from matplotlib.colors import Normalize

        mpl_norm = Normalize(vmin=min_val, vmax=max_val)

        cbar_label = "Explosive Diarrhea (Liquidity)"

        # Must be uniform or proportional, None not valid for Python 3
        cbar_spacing = "proportional"
        mpl_boundaries = None

        mpl_colors_info = {
            "cmap": mpl_cmap,
            "norm": mpl_norm,
            "cbar_ticks": ticks,
            "cbar_tick_labels": tick_labels,
            "cbar_label": cbar_label,
            "boundaries": mpl_boundaries,
            "cbar_spacing": cbar_spacing,
            "colorbar": True,
            "cbar_full_width": True,
            "reverse_colorbar": True,
            "set_ticks_kwargs": {"size": 12.5},
        }

        return mpl_colors_info


PLUGIN_CLASS = ExplosiveDiarrheaColormapperPlugin
