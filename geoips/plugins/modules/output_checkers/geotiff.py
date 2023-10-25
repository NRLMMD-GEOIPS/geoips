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
name = "geotiff"


def random_modification(input_path, output_path, max_modification=0.1):
    """Randomly modify the file from input path, and output it to output_path."""
    from osgeo import gdal
    from osgeo import gdalconst
    from numpy.random import rand

    # Open the input GeoTIFF file
    src_ds = gdal.Open(input_path, gdalconst.GA_ReadOnly)
    driver = gdal.GetDriverByName("GTiff")
    dst_ds = driver.CreateCopy(output_path, src_ds, 0)

    # Randomly modify the temporary copy
    band = dst_ds.GetRasterBand(1)
    data = band.ReadAsArray().astype("float64")
    data += (rand() - 0.5) * max_modification * 2
    band.WriteArray(data)

    # Close the dataset
    dst_ds = None


def get_test_files():
    """Return a Series of GeoTIFF paths, of which are randomly modified from compare."""
    from os import makedirs
    from os.path import exists, join
    import shutil
    from importlib.resources import files

    # Ensure the output directory exists
    savedir = str(files("geoips") / "../../test_data/test_geotiffs/pytest") + "/"
    if not exists(savedir):
        makedirs(savedir)

    compare_path = savedir + "compare.tif"
    # Prepare paths for matched, close_mismatch, and bad_mismatch
    matched_path = join(savedir, "matched.tif")
    close_mismatch_path = join(savedir, "close_mismatch.tif")
    bad_mismatch_path = join(savedir, "bad_mismatch.tif")

    # Copy the original compare file to the output directory
    shutil.copy(compare_path, matched_path)

    # Create a close mismatch by applying a small random modification
    random_modification(compare_path, close_mismatch_path, max_modification=0.05)

    # Create a bad mismatch by applying a larger random modification
    random_modification(compare_path, bad_mismatch_path, max_modification=0.25)

    # Return the paths to the files
    return compare_path, [matched_path, close_mismatch_path, bad_mismatch_path]


def perform_test_comparisons(plugin, compare_path, output_paths):
    """Test the comparison of two GeoTIFF files with the GeoTIFF Output Checker."""
    from os import remove

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
    for path in output_paths:
        remove(path)


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
        LOG.interactive("    *****************************************")
        LOG.interactive("    *** BAD geotiffs do NOT match exactly ***")
        LOG.interactive("    ***   output_product: %s ***", output_product)
        LOG.interactive("    ***   compare_product: %s ***", compare_product)
        LOG.interactive("    *****************************************")
        return False

    LOG.info("    ***************************")
    LOG.info("    *** GOOD geotiffs match ***")
    LOG.info("    ***************************")
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
