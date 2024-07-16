# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test script for representative product comparisons."""

import subprocess
import logging
from os.path import splitext

from geoips.commandline.log_setup import log_with_emphasis

LOG = logging.getLogger(__name__)

interface = "output_checkers"
family = "standard"
name = "geotiff"


def get_test_files_long(test_data_dir):
    """Return a Series of GeoTIFF paths, randomly modified from compare."""
    import rasterio
    import shutil
    from os import makedirs
    from os.path import exists, join
    from importlib.resources import files
    import numpy as np

    savedir = join(test_data_dir, "scratch", "unit_tests", "test_geotiffs")
    if not exists(savedir):
        makedirs(savedir)

    tif_name = "20200405_000000_SH252020_ahi_himawari-8_WV_100kts_100p00_1p0.tif"
    tif_path = str(files("geoips") / "../tests/outputs/ahi.tc.WV.geotiff" / tif_name)
    shutil.copy(tif_path, join(savedir, "compare.tif"))
    # Prepare paths for matched, close_mismatch, and bad_mismatch
    compare_file = join(savedir, "compare.tif")
    matched_file = join(savedir, "matched.tif")
    close_mismatch_file = join(savedir, "close_mismatch.tif")
    bad_mismatch_file = join(savedir, "bad_mismatch.tif")
    # Load the original GeoTIFF file
    with rasterio.open(compare_file) as src:
        compare_data = src.read()
        profile = src.profile

    # Save the original as 'compare'
    with rasterio.open(compare_file, "w", **profile) as dst:
        dst.write(compare_data)

    # Make a 'matched' version (identical to compare)
    with rasterio.open(matched_file, "w", **profile) as dst:
        dst.write(compare_data)

    # Make a 'close_mismatch' version (slightly modified)
    close_mismatch_data = compare_data + np.random.normal(
        scale=0.05, size=compare_data.shape
    )
    with rasterio.open(close_mismatch_file, "w", **profile) as dst:
        dst.write(close_mismatch_data)

    # Make a 'bad_mismatch' version (strongly modified)
    bad_mismatch_data = compare_data + np.random.normal(
        scale=0.25, size=compare_data.shape
    )
    with rasterio.open(bad_mismatch_file, "w", **profile) as dst:
        dst.write(bad_mismatch_data)

    return compare_file, [matched_file, close_mismatch_file, bad_mismatch_file]


def perform_test_comparisons_long(plugin, compare_file, test_files):
    """Test the comparison of two GeoTIFF files with the GeoTIFF Output Checker."""
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
    """Determine if fname is a geotiff file.

    Parameters
    ----------
    fname : str
        Name of file to check.

    Returns
    -------
    bool
        True if it is a geotiff file, False otherwise.
    """
    if splitext(fname)[-1] in [".tif"]:
        return True
    return False


def outputs_match(plugin, output_product, compare_product):
    """Use diff system command to compare currently produced image to correct image.

    Parameters
    ----------
    plugin: OutputCheckerPlugin
        The correspdonding geotiff output_checker - not used but needed in signature
    output_product : str
        Full path to current output product
    compare_product : str
        Full path to comparison product

    Returns
    -------
    bool
        Return True if images match, False if they differ
    """
    # out_diffimg = get_out_diff_fname(compare_product, output_product)

    call_list = ["diff", output_product, compare_product]
    LOG.info("Running %s", " ".join(call_list))
    retval = subprocess.call(call_list)

    # subimg_retval = subprocess.call(call_list)
    if retval != 0:
        log_with_emphasis(
            LOG.interactive,
            "BAD geotiffs do NOT match exactly",
            f"output_product: {output_product}",
            f"compare_product: {compare_product}",
        )
        return False

    log_with_emphasis(LOG.info, "GOOD geotiffs match")
    return True


def call(plugin, compare_path, output_products):
    """Compare the "correct" geotiffs found the list of current output_products.

    Compares files produced in the current processing run with the list of
    "correct" files contained in "compare_path".

    Parameters
    ----------
    plugin: OutputCheckerPlugin
        The corresponding geotiff OutputCheckerPlugin that has access to needed methods
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
