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

'''Standard TC filename production'''

# Python Standard Libraries
import logging

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

filename_type = 'standard'


def geotiff_fname(area_def, xarray_obj, product_name, coverage, output_type='tif', output_type_dir=None,
                  product_dir=None, product_subdir=None, source_dir=None, basedir=gpaths['ANNOTATED_IMAGERY_PATH']):

    from geoips.dev.filename import get_filenamer
    from geoips.sector_utils.utils import is_sector_type
    if is_sector_type(area_def, 'tc'):
        fname_func = get_filenamer('tc_fname')
        basedir = gpaths['TCWWW']
    else:
        fname_func = get_filenamer('geoips_fname')
    geotiff_fname = fname_func(area_def,
                               xarray_obj,
                               product_name,
                               coverage=coverage,
                               output_type=output_type,
                               output_type_dir=output_type_dir,
                               product_dir=product_dir,
                               product_subdir=product_subdir,
                               source_dir=source_dir,
                               basedir=basedir)

    return geotiff_fname

