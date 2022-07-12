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

from geoips.interface_modules.output_formats.imagery_windbarbs import output_clean_windbarbs, format_windbarb_data

LOG = logging.getLogger(__name__)

output_type = 'image'


def imagery_windbarbs_clean(area_def,
                            xarray_obj,
                            product_name,
                            output_fnames,
                            product_name_title=None,
                            mpl_colors_info=None,
                            existing_image=None,
                            remove_duplicate_minrange=None):

    formatted_data_dict = format_windbarb_data(xarray_obj, product_name)

    success_outputs = output_clean_windbarbs(area_def,
                                             output_fnames,
                                             mpl_colors_info,
                                             xarray_obj.start_datetime,
                                             formatted_data_dict)

    return success_outputs
