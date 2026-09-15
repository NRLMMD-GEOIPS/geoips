# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "create" command.

Creates configuration, registry, and sector image files.
"""

import logging
import os
from os.path import exists, join

from geoips.commandline.geoips_command import (
    GeoipsCommand,
    GeoipsExecutableCommand,
)
from geoips.errors import PluginError
from geoips.filenames.base_paths import PATHS
from geoips.interfaces import sectors

LOG = logging.getLogger(__name__)


class GeoipsSectorPlot(GeoipsExecutableCommand):
    """Command for plotting a sector image based on the provided sector name.

    This used to be ran via 'create_sector_image', however we are trying to consolidate
    all independent console scripts to be used via the CLI. When this command is called
    an image of the provided sector will be created so we can view whether or not it
    matches the region of the globe we'd like to study.
    """

    name = "plot"
    command_classes = []

    def add_arguments(self):
        """Instantiate the arguments that are supported for the sector plot command.

        Currently the "geoips sector plot" command supports this format:
            - geoips sector plot <sector_name> --outdir <output_directory_path>
        Where:
            - <sector_name> is the name of any GeoIPS Sector Plugin that has an entry in
              any package's plugin registry.
            - --outdir is the full path to the directory in which you'd like to create
              the sector image.
        """
        self.parser.add_argument(
            "sector_name",
            type=str,
            help="Name of the sector plugin to create an image from.",
        )
        self.parser.add_argument(
            "--outdir",
            "-o",
            type=str,
            default=PATHS["GEOIPS_OUTDIRS"],
            help="The output directory to create your sector image in.",
        )
        self.parser.add_argument(
            "--overlay",
            default=False,
            action="store_true",
            help=(
                "Overlay this sector on the global_cylindrical grid. Useful for testing"
                "small sectors, where their domain might be difficult to interpret in "
                "a geospatial context."
            ),
        )
        self.parser.add_argument(
            "--gridlines",
            "-g",
            default=False,
            action="store_true",
            help="Add a latitude / longitude gridline overlay to your sector.",
        )
        self.parser.add_argument(
            "--labels",
            "-l",
            default=["left", "bottom"],
            choices=["left", "right", "top", "bottom"],
            nargs="*",
            help=(
                "A list of strings which set where gridline labels will be set on the "
                "sector. Specify no values to disable labels."
            ),
        )

    def __call__(self, args):
        """Create the provided sector image based off the arguments provided.

        This will retrieve the selected sector plugin from any GeoIPS Plugin package,
        then create an image of that sector. This is a good way to quickly test whether
        or not your sector plugin covers the area you expected with the correct
        resolution.

        Parameters
        ----------
        args: Argparse Namespace()
            - The list argument namespace to parse through
        """
        sector_name = args.sector_name
        outdir = args.outdir
        overlay = args.overlay
        gridlines = args.gridlines
        labels = args.labels
        noborder = False if len(labels) else True

        # If the path to outdir doesn't already exist, make that path
        if not exists(outdir):
            os.makedirs(outdir)
        # Create an image for the requested sector, including just the map and white
        # background.
        fname = join(outdir, f"{sector_name}.png")
        try:
            if "non_existent" in sector_name:
                # This occurs for a unit test that we are just checking the error output
                # for. No need to rebuild the plugin registry, which can be specified by
                # using rebuild_registries=False
                rebuild_registries = False
            else:
                # Otherwise, assume this is a new sector that is being developed, and
                # automate plugin registry creation if it does not already exist as an
                # entry in the registry.
                rebuild_registries = True
            sect = sectors.get_plugin(
                sector_name, rebuild_registries=rebuild_registries
            )
        except PluginError:
            raise self.parser.error(
                f"Sector '{sector_name}' is not a valid plugin.\nPlease use a plugin "
                "found under 'geoips list interface sectors' or create a new plugin "
                f"named '{sector_name}' and run 'pluginify create'."
            )
        print(f"Creating {fname}.")
        sect.create_test_plot(
            fname,
            overlay=overlay,
            gridlines=gridlines,
            gridline_labels=labels,
            noborder=noborder,
        )


class GeoipsSector(GeoipsCommand):
    """Top-Level command for instantiating sub-command sector routines."""

    name = "sector"

    command_classes = [
        GeoipsSectorPlot,
    ]
