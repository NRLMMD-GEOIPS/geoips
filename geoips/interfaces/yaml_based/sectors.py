# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector interface module."""

from importlib.resources import files

from cartopy import feature as cfeature
import numpy as np
from pyresample import kd_tree, load_area
import xarray as xr

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.interfaces.base import BaseYamlPlugin, BaseYamlInterface
from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
from geoips.utils.types.datatree_ditto import DataTreeDitto


class SectorPluginBase(BaseYamlPlugin):
    """The base class for all sector plugins.

    This class provides the functionality specific to sector plugin classes. It should
    not be instantiated directly. To access sector plugins, use
    `geoips.interfaces.sectors`.
    """

    data_tree = True

    def call(self, data=None, **kwargs):
        r"""Return a DataTree with the sector's area-definition metadata.

        Parameters
        ----------
        data : xr.DataTree or None
            Upstream DataTree (unused for sectors).
        \\*\\*kwargs
            Step arguments (unused).

        Returns
        -------
        xr.DataTree
            A ``DataTreeDitto`` whose ``ds.attrs`` carry ``area_id``,
            ``area_extent``, ``shape``, and ``projection`` for downstream
            consumers (e.g. interpolator, filename formatter). Per the
            DataTree spec, this metadata lives in the step node's ``attrs``
            (there is no separate ``/metadata`` node).
        """
        ad = self.area_definition
        ds = xr.Dataset(
            attrs={
                "area_definition": ad,
                "area_id": getattr(ad, "area_id", self.name),
                "area_extent": getattr(ad, "area_extent", None),
                "shape": getattr(ad, "shape", None),
                "width": getattr(ad, "width", None),
                "height": getattr(ad, "height", None),
                "proj_dict": str(getattr(ad, "proj_dict", {})),
                "plugin_kind": "sector",
                "output_key": "area_def",
            }
        )
        return DataTreeDitto(ds, name=self.name)

    def __call__(self, data=None, **kwargs):
        """See ``call``."""
        return self.call(data=data, **kwargs)

    @property
    def area_definition(self):
        """Return the pyresample AreaDefinition for the sector."""
        # if self.family.startswith(("area_definition", "generated")):
        if self.family.startswith("area_definition"):
            abspath = str(files(self.package) / self.relpath)
            ad = load_area(abspath, "spec")
        # elif self.family.startswith("center"):
        #     ad = center_to_area_definition(self)
        # elif self.family.startswith("corners"):
        #     ad = corners_to_area_definition(self)
        return ad

    def create_test_plot(
        self,
        fname,
        return_fig_ax_map=False,
        overlay=False,
        gridlines=False,
        gridline_labels=[],
        noborder=True,
    ):
        """Create a test PNG image for this sector.

        Parameters
        ----------
        fname: str
            - The full path to the output image.
        return_fix_ax_map: bool, default=False
            - Whether or not we should save the image to disk or return the figure,
              axes, and mapobj variables in memory
        overlay: bool, default=False
            - If true, overlay this sector on the global grid and make it slightly
              transparent. Useful for projecting tiny sectors on the global grid to get
              a sense of where they'll end up and what they'll look like.
        gridlines: bool, default=False
            - If true, add latitude longitude gridlines to the sector image.
        gridline_labels: list[constants], default=[]
            - A list of constants (strings) that refer to which gridline labels to turn
              on.
        noborder: bool, default=True
            - If true, no border will be added to the axes instance. Otherwise, add
              a simple border (useful for gridline labels).
        """
        if overlay:
            global_sector = sectors.get_plugin("global_cylindrical")
            global_area_def = global_sector.area_definition
            fig, ax, mapobj = create_figure_and_main_ax_and_mapobj(
                global_area_def.shape[1],
                global_area_def.shape[0],
                global_area_def,
                noborder=noborder,
                gridlines=gridlines,
                gridline_labels=gridline_labels,
            )

            # Create a dummy 2D numpy array of data for self.area_definition
            data_overlay = np.ones(self.area_definition.shape) * 10  # or real data

            # Reproject data_overlay to the global grid
            resampled_data = kd_tree.resample_nearest(
                self.area_definition,
                data_overlay,
                global_area_def,
                radius_of_influence=14000,  # Not sure what to set here. I chose 14km
                fill_value=np.nan,
            )

            # Normalize to 0–1 range; this additionally masks out pixels we don't want
            # to color.
            norm = np.nan_to_num(resampled_data)
            norm = (norm - norm.min()) / (norm.max() - norm.min() + 1e-6)

            data_overlay = np.zeros(resampled_data.shape + (4,), dtype=np.float32)
            # This produces a Vivid Green Color
            data_overlay[..., 0] = 0.282
            data_overlay[..., 1] = 1.0
            data_overlay[..., 2] = 0
            data_overlay[..., 3] = norm * 0.5

            # Plot overlay data (with transparency) on the global grid
            ax.imshow(
                data_overlay,
                transform=mapobj,
                extent=(
                    global_area_def.area_extent[0],
                    global_area_def.area_extent[2],
                    global_area_def.area_extent[1],
                    global_area_def.area_extent[3],
                ),
                origin="upper",
            )

        else:
            fig, ax, mapobj = create_figure_and_main_ax_and_mapobj(
                self.area_definition.shape[1],
                self.area_definition.shape[0],
                self.area_definition,
                noborder=noborder,
                gridlines=gridlines,
                gridline_labels=gridline_labels,
            )
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        if fname is not None:
            fig.savefig(fname)
        if return_fig_ax_map:
            return fig, ax, mapobj


class SectorsInterface(BaseYamlInterface):
    """Interface for sector plugins."""

    name = "sectors"
    plugin_class = SectorPluginBase
    use_pydantic = gpaths["GEOIPS_USE_PYDANTIC"]
    # if sectors.get_plugin(<name>) is found to be a dynamic sector. Otherwise, a static
    # sector plugin model (I.e. SectorPluginModel) will be used for all other sector
    # types.


sectors = SectorsInterface()
