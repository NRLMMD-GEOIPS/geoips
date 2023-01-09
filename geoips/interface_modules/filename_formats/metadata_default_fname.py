# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Default TC metadata filename production"""
# metadata_yaml_filename = tc_fname_metadata(area_def, xarray_obj, product_filename, metadata_dir,
#                                            metadata_type='sector_information', basedir=basedir)

# Python Standard Libraries
from os.path import join as pathjoin
from os.path import basename
import logging

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.interface_modules.filename_formats.utils.tc_file_naming import (
    tc_storm_basedir,
)

LOG = logging.getLogger(__name__)

filename_type = "standard_metadata"


def metadata_default_fname(
    area_def,
    xarray_obj,
    product_filename,
    metadata_dir="metadata",
    metadata_type="sector_information",
    basedir=gpaths["TCWWW"],
    output_dict=None,
):
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
