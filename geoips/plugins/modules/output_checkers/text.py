# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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


def copy_files(text_path, savedir, file_ext):
    """Copy text file internal in GeoIPS to output directory."""
    from shutil import copy
    from os.path import join

    copy(text_path, join(savedir, "compare." + file_ext))
    copy(text_path, join(savedir, "matched." + file_ext))
    copy(text_path, join(savedir, "close_mismatch." + file_ext))
    copy(text_path, join(savedir, "bad_mismatch." + file_ext))


def get_test_files(test_data_dir):
    """Return a series of varied text files."""
    import numpy as np
    from shutil import copy
    from os import makedirs
    from os.path import exists, join
    from importlib.resources import files

    savedir = join(test_data_dir, "scratch", "unit_tests", "test_text")
    if not exists(savedir):
        makedirs(savedir)
    text_path = str(files("geoips") / "plugins/txt/ascii_palettes/tpw_cimss.txt")
    copy_files(text_path, savedir, "txt")
    comp_path = join(savedir, "compare.txt")
    match_path = join(savedir, "matched.txt")
    close_path = join(savedir, "close_mismatch.txt")
    bad_path = join(savedir, "bad_mismatch.txt")
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


def perform_test_comparisons(plugin, compare_file, test_files):
    """Test the comparison of two text files with the Text Output Checker."""
    for path_idx in range(len(test_files)):
        retval = plugin.module.outputs_match(
            plugin,
            test_files[path_idx],
            compare_file,
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
    from geoips.commandline.log_setup import log_with_emphasis

    ret = subprocess.run(
        ["diff", output_product, compare_product],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    LOG.debug(ret.stdout)
    if ret.returncode == 0:
        log_with_emphasis(LOG.info, "GOOD Text files match")
        return True

    out_difftxt = plugin.get_out_diff_fname(compare_product, output_product)
    with open(out_difftxt, "w") as fobj:
        subprocess.call(["diff", output_product, compare_product], stdout=fobj)
    log_with_emphasis(
        LOG.interactive,
        "BAD Text files do NOT match exactly",
        f"output_product: {output_product}",
        f"compare_product: {compare_product}",
        f"out_difftxt: {out_difftxt}",
    )
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
