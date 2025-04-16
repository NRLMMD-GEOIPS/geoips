# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard GeoIPS static title production."""

# Python Standard Libraries
import logging

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
        # title_string = f'{title_line1}\n{title_line2}\n{title_line3}\n
        #                                                             {title_copyright}'
        title_string = f"{title_line1}\n{title_line2} {title_copyright}\n{title_line3}"
    else:
        # title_string = f'{title_line1}\n{title_line2}\n{title_copyright}'
        title_string = f"{title_line1}\n{title_line2} {title_copyright}"
    LOG.info("Not dynamic, using standard title_string: %s", title_string)

    return title_string
