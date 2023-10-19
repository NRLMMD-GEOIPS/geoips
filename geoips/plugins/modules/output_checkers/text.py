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

import subprocess
import logging
from os.path import splitext

LOG = logging.getLogger(__name__)

interface = "output_checkers"
family = "standard"
name = "text"


def clear_text(match_path, close_path, bad_path):
    """Clear output text files so they can be written again."""
    open(match_path, "w").close()
    open(close_path, "w").close()
    open(bad_path, "w").close()


def yield_test_files():
    """Return a series of varied text files."""
    from os import environ
    import numpy as np
    from shutil import copy

    savedir = str(environ["GEOIPS_PACKAGES_DIR"]) + "/test_data/test_text/pytest/"
    comp_path = savedir + "compare.txt"
    match_path = savedir + "matched.txt"
    close_path = savedir + "close_mismatch.txt"
    bad_path = savedir + "bad_mismatch.txt"
    clear_text(match_path, close_path, bad_path)
    copy(comp_path, match_path)
    with open(comp_path, mode="r") as comp_txt:
        close_mismatch = open(close_path, "w")
        bad_mismatch = open(bad_path, "w")
        for line in comp_txt.readlines():
            for version in range(2):
                rand = np.random.rand()
                if version == 0:  # Close but mismatched
                    if rand > 0.05:
                        close_mismatch.write(line)
                else:  # Mismatched -- not close
                    if rand > 0.25:
                        bad_mismatch.write(line)
        close_mismatch.close()
        bad_mismatch.close()
    return comp_path, [match_path, close_path, bad_path]


def perform_test_comparisons(plugin, compare_path, output_paths):
    """Test the comparison of two text files with the Text Output Checker."""
    for path_idx in range(len(output_paths)):
        retval = plugin.module.outputs_match(
            plugin,
            output_paths[path_idx],
            compare_path,
        )
        if path_idx == 0:
            assert retval is True
        else:
            assert retval is False


def correct_file_format(fname):
    """Check if fname is a text file.

    Parameters
    ----------
    fname : str
        Name of file to check.

    Returns
    -------
    bool
        True if it is a text file, False otherwise.
    """
    if splitext(fname)[-1] in ["", ".txt", ".text", ".yaml"]:
        with open(fname) as f:
            line = f.readline()
        if isinstance(line, str):
            return True
    return False


def outputs_match(plugin, output_product, compare_product):
    """Check if two text files match.

    Parameters
    ----------
    plugin: OutputCheckerPlugin
        The corresponding geotiff OutputCheckerPlugin that has access to needed methods
    output_product : str
        Full path to current output product
    compare_product : str
        Full path to "good" comparison product

    Returns
    -------
    bool
        Return True if products match, False if they differ
    """
    ret = subprocess.run(
        ["diff", output_product, compare_product],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    LOG.debug(ret.stdout)
    if ret.returncode == 0:
        LOG.info("    *****************************")
        LOG.info("    *** GOOD Text files match ***")
        LOG.info("    *****************************")
        return True

    out_difftxt = plugin.get_out_diff_fname(compare_product, output_product)
    with open(out_difftxt, "w") as fobj:
        subprocess.call(["diff", output_product, compare_product], stdout=fobj)
    LOG.interactive("    *******************************************")
    LOG.interactive("    *** BAD Text files do NOT match exactly ***")
    LOG.interactive("    ***   output_product: %s ***", output_product)
    LOG.interactive("    ***   compare_product: %s ***", compare_product)
    LOG.interactive("    ***   out_difftxt: %s ***", out_difftxt)
    LOG.interactive("    *******************************************")
    return False


def call(plugin, compare_path, output_products):
    """Compare the "correct" text found the list of current output_products.

    Compares files produced in the current processing run with the list of
    "correct" files contained in "compare_path".

    Parameters
    ----------
    plugin: OutputCheckerPlugin
        The corresponding text OutputCheckerPlugin that has access to needed methods
    compare_path : str
        Path to directory of "correct" products - filenames must match output_products
    output_products : list of str
        List of strings of current output products,
        to compare with products in compare_path

    Returns
    -------
    int
        Binary code: 0 if all comparisons were completed successfully.
    """
    retval = plugin.compare_outputs(
        compare_path,
        output_products,
    )
    return retval
