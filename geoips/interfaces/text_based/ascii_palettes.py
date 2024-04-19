"""Ascii Palette Module implementing a class used in producing colormapped products."""

from importlib import util
from importlib.resources import files
from matplotlib import colors
import numpy
from os.path import basename

from geoips.interfaces.base import BaseTextInterface


class AsciiPaletteColormap:
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
        self.plugin_entry["colormap"] = self.colormap

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

        carray = numpy.zeros([len(lines), 3])
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

        if cmap_name is not None:
            cmap_name = basename(fpath)
        cmap = colors.ListedColormap(carray, name=cmap_name)
        return cmap


class AsciiPaletteInterface(BaseTextInterface):
    """Interface for the Ascii Palette (kid of Colormapper) to apply to the product."""

    name = "ascii_palettes"
    required_args = {"standard": {}}
    required_kwargs = {"standard": {}}
    plugin_class = AsciiPaletteColormap

    @property
    def ascii_colormap_module(self):
        """Module containing the call function we use to apply our ascii palette."""
        if not hasattr(self, "_ascii_colormap_module"):
            module_path = "geoips.plugins.modules.colormappers.ascii_to_colormapper"
            abspath = str(
                files("geoips") / "plugins/modules/colormappers/ascii_to_colormapper.py"
            )
            spec = util.spec_from_file_location(module_path, abspath)
            self._ascii_colormap_module = util.module_from_spec(spec)
            spec.loader.exec_module(self._ascii_colormap_module)
        return self._ascii_colormap_module


ascii_palettes = AsciiPaletteInterface()
