# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard GeoIPS formatted titles for tropical cyclone products."""

# Python Standard Libraries
import logging

# GeoIPS Libraries
from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

interface = "title_formatters"
family = "standard"
name = "tc_standard"


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
    """Create standard GeoIPS formatted title for tropical cyclone products."""
    if title_copyright is None:
        title_copyright = gpaths["GEOIPS_COPYRIGHT"]

    LOG.info("Setting dynamic title")

    # Make sure we reflect the actual start_datetime in the filename
    # geoimg_obj.set_geoimg_attrs(start_dt=xarray_obj.start_datetime)
    if "interpolated_time" in area_def.sector_info:
        sector_time = area_def.sector_info["interpolated_time"]
    else:
        sector_time = area_def.sector_info["synoptic_time"]

    title_line1 = "{0}{1:02d} {2} at {3}".format(
        area_def.sector_info["storm_basin"],
        int(area_def.sector_info["storm_num"]),
        area_def.sector_info["storm_name"],
        sector_time.strftime("%Y-%m-%d %H:%M:%S"),
    )

    # data_time = xarray_obj.start_datetime +
    #                            (xarray_obj.end_datetime - xarray_obj.start_datetime)/2
    data_time = xarray_obj.start_datetime
    # pandas dataframes seem to handle time objects much better than xarray.
    title_line2 = "{0} {1} at {2}".format(
        product_datatype_title,
        product_name_title,
        data_time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    if bg_xarray is not None:
        # bg_data_time = bg_xarray.start_datetime +
        #                          (bg_xarray.end_datetime - bg_xarray.start_datetime)/2
        bg_data_time = bg_xarray.start_datetime
        title_line3 = "{0} {1} at {2}".format(
            bg_datatype_title,
            bg_product_name_title,
            bg_data_time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        # title_string = f'{title_line1}\n{title_line2}\n{title_line3}\n
        #                                                             {title_copyright}'
        title_string = f"{title_line1}, {title_copyright}\n{title_line2}\n{title_line3}"
    else:
        # title_string = f'{title_line1}\n{title_line2}\n{title_copyright}'
        title_string = f"{title_line1}, {title_copyright}\n{title_line2}"

    LOG.info("title_string: %s", title_string)

    return title_string
