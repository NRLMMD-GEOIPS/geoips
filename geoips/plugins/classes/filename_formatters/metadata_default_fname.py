# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Default TC metadata filename formatter."""

from geoips.interfaces.class_based.filename_formatters import (
    BaseFilenameFormatterPlugin,
)

# metadata_yaml_filename = tc_fname_metadata(area_def, xarray_obj,
#                                            product_filename, metadata_dir,
#                                            metadata_type='sector_information',
#                                            basedir=basedir)

# Python Standard Libraries
from os.path import join as pathjoin
from os.path import basename
import logging

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.plugins.classes.filename_formatters.utils.tc_file_naming import (
    tc_storm_basedir,
)

LOG = logging.getLogger(__name__)


class MetadataDefaultFnameFilenameFormatterPlugin(BaseFilenameFormatterPlugin):
    """Metadata Default Fname Filename formatter plugin class."""

    interface = "filename_formatters"
    family = "standard_metadata"
    name = "metadata_default_fname"

    def call(
        self,
        area_def,
        xarray_obj,
        product_filename,
        metadata_dir="metadata",
        metadata_type="sector_information",
        basedir=gpaths["TCWWW"],
    ):
        """Generate TC metadata filenames.

        This uses attributes on both the xarray and area_def in order to produce
        the YAML metadata output specifically for TC sectors.  Not valid for
        other sector types.

        This uses the "tc_storm_basedir" utility to ensure a consistent path
        to the storm directory (so products and metadata end up in the same
        location)
        """
        from geoips.sector_utils.utils import is_sector_type

        if not is_sector_type(area_def, "tc"):
            return None

        allowed_metadata_types = [
            "sector_information",
            "archer_information",
            "storm_information",
        ]

        if metadata_type not in allowed_metadata_types:
            raise TypeError(
                f"Unknown metadata type {metadata_type}, allowed "
                f"{allowed_metadata_types}"
            )

        metadata_type = "sector_information"
        metadata_datetime = xarray_obj.start_datetime

        metadata_yaml_dirname = pathjoin(
            tc_storm_basedir(basedir, sector_info=area_def.sector_info),
            metadata_dir,
            metadata_type,
            metadata_datetime.strftime("%Y%m%d"),
        )
        metadata_yaml_basename = basename(product_filename) + ".yaml"

        return pathjoin(metadata_yaml_dirname, metadata_yaml_basename)


PLUGIN_CLASS = MetadataDefaultFnameFilenameFormatterPlugin
