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

''' Specifications for output filename formats for text windspeed product types. '''

import logging

from os.path import join as pathjoin, splitext as pathsplitext
from os.path import dirname as pathdirname, basename as pathbasename
from datetime import datetime, timedelta
from glob import glob
from os import unlink as osunlink

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.data_manipulations.merge import minrange
from geoips.interface_modules.filename_formats.text_winds_full_fname import assemble_windspeeds_text_full_fname

LOG = logging.getLogger(__name__)

filename_type = 'xarray_metadata_to_filename'


def text_winds_day_fname(xarray_obj,
                         extension='.txt',
                         basedir=pathjoin(gpaths['ANNOTATED_IMAGERY_PATH'], 'text_winds')):
    return assemble_windspeeds_text_full_fname(basedir=basedir,
                                               source_name=xarray_obj.source_name,
                                               platform_name=xarray_obj.platform_name,
                                               data_provider=xarray_obj.data_provider,
                                               product_datetime=xarray_obj.start_datetime,
                                               dt_format='%Y%m%d',
                                               extension=extension,
                                               creation_time=None)
