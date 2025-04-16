# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Default TC metadata filename formatter."""

# metadata_yaml_filename = tc_fname_metadata(area_def, xarray_obj,
#                                            product_filename, metadata_dir,
#                                            metadata_type='sector_information',
#                                            basedir=basedir)

# Python Standard Libraries
from os.path import join as pathjoin
from os.path import basename
import logging

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.plugins.modules.filename_formatters.utils.tc_file_naming import (
    tc_storm_basedir,
)

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "standard_metadata"
name = "metadata_default_fname"


def call(
    area_def,
    xarray_obj,
    product_filename,
    metadata_dir="metadata",
    metadata_type="sector_information",
    basedir=gpaths["TCWWW"],
    output_dict=None,
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
            f"Unknown metadata type {metadata_type}, allowed {allowed_metadata_types}"
        )

    tc_year = int(area_def.sector_info["storm_year"])
    tc_basin = area_def.sector_info["storm_basin"]
    tc_stormnum = int(area_def.sector_info["storm_num"])
    metadata_type = "sector_information"
    metadata_datetime = xarray_obj.start_datetime

    metadata_yaml_dirname = pathjoin(
        tc_storm_basedir(
            basedir,
            tc_year,
            tc_basin,
            tc_stormnum,
            output_dict=output_dict,
            sector_info=area_def.sector_info,
        ),
        metadata_dir,
        metadata_type,
        metadata_datetime.strftime("%Y%m%d"),
    )
    metadata_yaml_basename = basename(product_filename) + ".yaml"

    return pathjoin(metadata_yaml_dirname, metadata_yaml_basename)
