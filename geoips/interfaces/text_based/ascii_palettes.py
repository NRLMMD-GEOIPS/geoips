"""Ascii Palette Module implementing a class used in producing colormapped products."""

from importlib.resources import files
import logging
from matplotlib import colors
import numpy
from os.path import basename

from geoips.errors import AsciiPaletteError
from geoips.interfaces.base import BaseTextInterface, BaseTextPlugin

LOG = logging.getLogger(__name__)


# Defaults are set for arguments here as this can be called by other modules/classes
# besides AsciiPalettesPlugin
def from_ascii(
    fpath,
    cmap_name=None,
    reverse=False,
    cmap_type="ListedColormap",
    cmap_kwargs={},
):
    """Create a ListedColormap instance from an ASCII file of RGB values.

    Parameters
    ----------
    fpath: str
        - Full path to ascii RGB colortable file
    cmap_name: str, default=None
        - Identifying name of colormap - if None, default to basename(fpath)
    reverse: bool, default=False
        - If True, reverse the colormap
    cmap_type: str, default="ListedColormap"
        - The name of the Colormap-derived class from matplotlib.colors. Must be one of
          "ListedColormap" or "LinearSegmentedColormap" or a TypeError will be raised.
    cmap_kwargs: dict, default={}
        - Dictionary of keyword arguments to use in the construction of your colormap
          object, which are associated with your 'cmap_type'.

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

    if cmap_type == "ListedColormap":
        cmap_constructor = colors.ListedColormap
    elif cmap_type == "LinearSegmentedColormap":
        cmap_constructor = colors.LinearSegmentedColormap.from_list
    else:
        raise TypeError(
            f"Error: provided matplotlib.colors Colormap '{cmap_type}' is not a valid "
            f"colormap. Please choose one of "
            "['ListedColormap', 'LinearSegmentedColormap'] and provide arguments for "
            "those colormaps where applicable."
        )

    cmap = cmap_constructor(colors=carray, name=cmap_name, **cmap_kwargs)

    return cmap


class AsciiPalettesPlugin(BaseTextPlugin):
    """Class representing an Ascii Palette Used to Construct a GeoIPS Colormapper."""

    def __call__(
        self,
        reverse=False,
        cmap_name=None,
        cmap_type="ListedColormap",
        cmap_kwargs={},
    ):
        """Return a matplotlib-based colormap object to be used w/ GeoIPS colormappers.

        Parameters
        ----------
        cmap_name: str, default=None (basename(fname))
            - Identifying name of colormap - if None, default to basename(fname)
        reverse: bool, default=False
            - If True, reverse the colormap
        cmap_type: str, default="ListedColormap"
            - The name of the Colormap-derived class from matplotlib.colors. Must be one
              of "ListedColormap" or "LinearSegmentedColormap" or a TypeError will be
              raised.
        cmap_kwargs: dict, default={}
            - Dictionary of keyword arguments to use in the construction of your
              colormap object, which are associated with your 'cmap_type'.

        Returns
        -------
        cmap : matplotlib.colors Colormap-derived Object
            * Either a 'ListedColormap' or a 'LinearSegmentedColormap' derived from a
              text ascii palette.
        """
        path_to_ascii = str(
            files(self.plugin_entry["package"]) / self.plugin_entry["relpath"]
        )
        cmap = from_ascii(
            path_to_ascii,
            reverse=reverse,
            cmap_name=cmap_name,
            cmap_type=cmap_type,
            cmap_kwargs=cmap_kwargs,
        )
        return cmap


class AsciiPaletteInterface(BaseTextInterface):
    """Interface for the Ascii Palette (kid of Colormapper) to apply to the product."""

    name = "ascii_palettes"
    required_args = {"rgb": {}}
    required_kwargs = {"rgb": {}}
    plugin_class = AsciiPalettesPlugin


ascii_palettes = AsciiPaletteInterface()
