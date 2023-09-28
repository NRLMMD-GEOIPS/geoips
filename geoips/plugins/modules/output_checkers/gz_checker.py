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

"""Test script for representative product comparisons."""

import logging
from os.path import splitext
from geoips.plugins.modules.output_checkers.utils import compare_outputs as co

LOG = logging.getLogger(__name__)

interface = "output_checkers"
family = "standard"
name = "gz_checker"


def correct_type(fname):
    """Check if fname is a gzip file.

    Parameters
    ----------
    fname : str
        Name of file to check.

    Returns
    -------
    bool
        True if it is a gz file, False otherwise.
    """
    if splitext(fname)[-1] in [".gz"]:
        return True
    return False


def call(compare_path, output_products, test_product_func=None):
    """Compare the "correct" imagery found the list of current output_products.

    Compares files produced in the current processing run with the list of
    "correct" files contained in "compare_path".

    Parameters
    ----------
    compare_path : str
        Path to directory of "correct" products - filenames must match output_products
    output_products : list of str
        List of strings of current output products,
        to compare with products in compare_path
    test_product_func : function, default=None
        Alternative function to be used for testing output product

          * Call signature must be:

              * output_product, compare_product, goodcomps, badcomps, compare_strings

          * Return must be:

              * goodcomps, badcomps, compare_strings

        * If None, use geoips.compare_outputs.test_product)

    Returns
    -------
    int
        Binary code: 0 if all comparisons were completed successfully.
    """
    retval = co.compare_outputs(compare_path, output_products, test_product_func)
    return retval
