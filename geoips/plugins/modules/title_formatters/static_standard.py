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

"""Standard GeoIPS static title production."""

# Python Standard Libraries
import logging

from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

interface = "title_formatters"
family = "standard"
name = "static_standard"


def call(
    area_def,
    xarray_obj,
    product_name_title,
    product_datatype_title=None,
    bg_xarray=None,
    bg_product_name_title=None,
    bg_datatype_title=None,
    title_copyright=None,
):
    """Generate standard GeoIPS formatted title."""
    title_line1 = "{0} {1}".format(product_datatype_title, product_name_title)
    title_line2 = "{0}".format(xarray_obj.start_datetime.strftime("%Y/%m/%d %H:%M:%SZ"))
    if bg_xarray is not None:
        title_line3 = "{0} {1} at {2}".format(
            bg_datatype_title,
            bg_product_name_title,
            bg_xarray.start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        )
        # title_string = f'{title_line1}\n{title_line2}\n{title_line3}\n{title_copyright}'
        title_string = f"{title_line1}\n{title_line2} {title_copyright}\n{title_line3}"
    else:
        # title_string = f'{title_line1}\n{title_line2}\n{title_copyright}'
        title_string = f"{title_line1}\n{title_line2} {title_copyright}"
    LOG.info("Not dynamic, using standard title_string: %s", title_string)

    return title_string
