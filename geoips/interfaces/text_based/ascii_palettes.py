"""Ascii Palette Module implementing a class used in producing colormapped products."""

from importlib.resources import files
import logging
from matplotlib import colors
import numpy
from os.path import basename
from types import SimpleNamespace

from geoips.errors import AsciiPaletteError
from geoips.interfaces.base import BaseTextInterface, BaseTextPlugin

LOG = logging.getLogger(__name__)


class AsciiPalettesPlugin(BaseTextPlugin):
    """Class representing an Ascii Palette Used to Construct a GeoIPS Colormapper."""

    def __init__(self, plugin_name):
        """Initialize the ascii palette class from a text-based ascii palette plugin.

        Parameters
        ----------
        plugin_name: str
            - The name of the text-based ascii palette contained in the Plugin Registry.
        """
        self.plugin_entry = AsciiPaletteInterface().text_registry["ascii_palettes"][
            plugin_name
        ]
        self.name = plugin_name
        for key in self.plugin_entry.keys():
            setattr(self, key, self.plugin_entry[key])

    @property
    def colormap(self):
        """Ascii Palette derived from 'self.plugin_entry'.

        Returns
        -------
        cmap: Matplotlob.colors.ListedColormap
            - The colormap derived from the ascii palette
        """
        if not hasattr(self, "_colormap"):
            path_to_ascii = str(
                files(self.plugin_entry["package"]) / self.plugin_entry["relpath"]
            )
            self._colormap = self.from_ascii(path_to_ascii)
        return self._colormap

    def from_ascii(self, fpath, cmap_name=None, reverse=False):
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
        with open(fpath) as palette:
            for line in palette.readlines():
                if line.strip()[0] != "#":
                    lines += [line]

        if len(lines) == 0:
            # missing the ascii palette completely, raise an error reporting this.
            raise AsciiPaletteError(
                f"Missing Ascii Palette in {fpath}.\n Please define the ascii palette "
                "before continuing."
            )
        carray = numpy.zeros([len(lines), 3])
        for num, line in enumerate(lines):
            color_nums = line.strip().split()
            if len(color_nums) != 3:
                raise AsciiPaletteError(
                    f"One or more lines of the ascii palette in {fpath} are missing "
                    "one or more values of the 'rgb' triplet. Please fix."
                )
            try:
                carray[num, :] = [float(val) for val in line.strip().split()]
            except ValueError as e:
                raise AsciiPaletteError(
                    f"Invalid ascii palette found in {fpath}. See resulting error: {e}."
                )

        # Normalize from 0-255 to 0.0-1.0
        if carray.max() > 1.0:
            carray /= 255.0

        # Test to be sure all color array values are between 0.0 and 1.0
        if not (carray.min() >= 0.0 and carray.max() <= 1.0):
            raise AsciiPaletteError("All values in carray must be between 0.0 and 1.0.")

        if reverse is True:
            carray = numpy.flipud(carray)

        if cmap_name is not None:
            cmap_name = basename(fpath)
        cmap = colors.ListedColormap(carray, name=cmap_name)
        return cmap

    def __call__(self, **kwargs):
        """Set the matplotlib colors information for matplotlib linear norm cmaps.

        This information used in both colorbar and image production throughout
        GeoIPS image output specifications.

        Parameters
        ----------
        kwargs: dict of arguments, optionally including what is shown below.
            * data_range : list, default=None
                * [min_val, max_val],
                matplotlib.colors.Normalize(vmin=min_val, vmax=max_val)
                * If data_range not specified, vmin and vmax both None.
            * cbar_label : str, default=None
                * Positional parameter passed to cbar.set_label
                * If specified, use cbar_label string as colorbar label.
            * create_colorbar : bool, default=True
                * Specify whether the image should contain a colorbar or not.
            * cbar_ticks : list, default=None
                * Positional parameter passed to cbar.set_ticks
                * Specify explicit list of ticks to include for colorbar.
                * None indicates ticks at int(min) and int(max) values
            * cbar_tick_labels : list, default=None
                * "labels" argument to pass to cbar.set_ticks.
                * can also specify directly within "set_ticks_kwargs"
            * cbar_spacing : string, default="proportional"
                * "spacing" argument to pass to fig.colorbar
                * can also specify directly within "colorbar_kwargs"
            * cbar_full_width : bool, default=True
                * Extend the colorbar across the full width of the image.
            * colorbar_kwargs : dict, default=None
                * keyword arguments to pass through directly to "fig.colorbar"
            * set_ticks_kwargs : dict, default=None
                * keyword arguments to pass through directly to "cbar.set_ticks"
            * set_label_kwargs : dict, default=None
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
        min_val = None
        max_val = None
        kwargs = SimpleNamespace(kwargs)
        if kwargs.data_range is not None:
            min_val = kwargs.data_range[0]
            max_val = kwargs.data_range[1]

        mpl_cmap = self.colormap

        LOG.info("Setting norm")

        mpl_norm = colors.Normalize(vmin=min_val, vmax=max_val)
        if kwargs.cbar_ticks:
            mpl_ticks = kwargs.cbar_ticks
        elif min_val is not None:
            mpl_ticks = [int(min_val), int(max_val)]
        else:
            mpl_ticks = None

        if kwargs.cbar_tick_labels is None:
            mpl_tick_labels = mpl_ticks

        # Must be uniform or proportional, None not valid for Python 3
        mpl_boundaries = None

        mpl_colors_info = {
            "cmap": mpl_cmap,
            "norm": mpl_norm,
            "boundaries": mpl_boundaries,
            "colorbar": kwargs.create_colorbar,
            "cbar_ticks": mpl_ticks,
            "cbar_tick_labels": mpl_tick_labels,
            "cbar_label": kwargs.cbar_label,
            "cbar_spacing": kwargs.cbar_spacing,
            "cbar_full_width": kwargs.cbar_full_width,
            "colorbar_kwargs": kwargs.colorbar_kwargs,
            "set_ticks_kwargs": kwargs.set_ticks_kwargs,
            "set_label_kwargs": kwargs.set_label_kwargs,
        }

        return mpl_colors_info


class AsciiPaletteInterface(BaseTextInterface):
    """Interface for the Ascii Palette (kid of Colormapper) to apply to the product."""

    name = "ascii_palettes"
    required_args = {"standard": {}}
    required_kwargs = {"standard": {}}

    @property
    def plugin_class(self):
        """Class used to create the corresponding ascii-palette plugins."""
        return AsciiPalettesPlugin


ascii_palettes = AsciiPaletteInterface()
