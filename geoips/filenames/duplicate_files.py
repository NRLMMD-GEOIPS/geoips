# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

import logging

LOG = logging.getLogger(__name__)


def remove_duplicates(fnames, remove_files=False):
    removed_files = []
    saved_files = []
    from geoips.sector_utils.utils import is_sector_type
    from geoips.interfaces import filename_formatters
    from importlib import import_module
    for fname in fnames:
        filename_format = fnames[fname]['filename_format']
        fnamer = filename_formatters.get(fnames[fname]['filename_format'])
        if hasattr(import_module(fnamer.__module__), f'{filename_format}_remove_duplicates'):
            fnamer_remove_dups = getattr(import_module(fnamer.__module__), f'{filename_format}_remove_duplicates')
            curr_removed_files, curr_saved_files = fnamer_remove_dups(fname, remove_files=remove_files)
            removed_files += curr_removed_files
            saved_files += curr_saved_files
    else:
        LOG.warning(f'SKIPPING DUPLICATE REMOVAL no {filename_format}_remove_duplicates defined')

    return removed_files, saved_files


