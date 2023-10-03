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
from os.path import splitext, exists
import subprocess

LOG = logging.getLogger(__name__)

interface = "output_checkers"
family = "standard"
name = "gz_checker"


def gunzip_product(fname):
    """Gunzip file fname.

    Parameters
    ----------
    fname : str
        File to gunzip.

    Returns
    -------
    str
        Filename after gunzipping
    """
    LOG.info("**** Gunzipping product for comparisons - will gzip after comparing")
    LOG.info("gunzip %s", fname)
    subprocess.call(["gunzip", fname])
    return splitext(fname)[0]


def gzip_product(fname):
    """Gzip file fname.

    Parameters
    ----------
    fname : str
        File to gzip.

    Returns
    -------
    str
        Filename after gzipping
    """
    LOG.info("**** Gzipping product - leave things as we found them")
    LOG.info("gzip %s", fname)
    subprocess.call(["gzip", fname])
    return splitext(fname)[0]


def print_gunzip_to_file(fobj, gunzip_fname):
    """Write the command to gunzip the passed "gunzip_fname" to file.

    Writes to the currently open file object, if required.
    """
    if exists(f"{gunzip_fname}.gz") and not exists(f"{gunzip_fname}"):
        fobj.write(f"gunzip -v {gunzip_fname}.gz\n")


def print_gzip_to_file(fobj, gzip_fname):
    """Write the command to gzip the passed "gzip_fname" to file.

    Writes to the currently open file object, if required.
    """
    if exists(f"{gzip_fname}.gz") and not exists(f"{gzip_fname}"):
        fobj.write(f"gzip -v {gzip_fname}\n")


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


def call(self, compare_path, output_products, test_product_func=None):
    """Compare the "correct" gzs found the list of current output_products.

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
    retval = self.compare_outputs(compare_path, output_products, test_product_func)
    return retval
