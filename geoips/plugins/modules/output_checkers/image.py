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

LOG = logging.getLogger(__name__)

interface = "output_checkers"
family = "standard"
name = "image"


def yield_test_files():
    """Return a series of compare vs output image paths for testing purposes."""
    from PIL import Image
    import numpy as np
    from os import environ

    savedir = str(environ["GEOIPS_PACKAGES_DIR"]) + "/test_data/test_images/pytest/"
    thresholds = ["lenient", "medium", "strict"]
    compare_paths = []
    output_paths = []
    for threshold in thresholds:
        for i in range(3):
            comp_arr = np.random.rand(100, 100, 3)
            output_arr = np.copy(comp_arr)
            if i == 1:
                rand = np.random.randint(0, 100)
                output_arr[rand][:] = np.random.rand(3)
            elif i == 2:
                output_arr = np.random.rand(100, 100, 3)
            comp_img = Image.fromarray((comp_arr * 255).astype(np.uint8))
            output_img = Image.fromarray((output_arr * 255).astype(np.uint8))
            comp_path = savedir + "comp_img_" + threshold + str(i) + ".png"
            output_path = savedir + "output_img_" + threshold + str(i) + ".png"
            comp_img.save(comp_path)
            output_img.save(output_path)
            compare_paths.append(comp_path)
            output_paths.append(output_path)
    return compare_paths, output_paths


def perform_test_comparisons(plugin, compare_paths, output_paths):
    """Test the comparison of two images with the Image Output Checker."""
    threshold_floats = [0.1, 0.05, 0.0]
    for threshold in threshold_floats:
        for path_idx in range(len(compare_paths)):
            outputs_match(
                plugin,
                output_paths[path_idx],
                compare_paths[path_idx],
                threshold,
            )


def correct_file_format(fname):
    """Determine if fname is an image file.

    Parameters
    ----------
    fname : str
        Name of file to check.

    Returns
    -------
    bool
        True if it is an image file, False otherwise.
    """
    if splitext(fname)[-1] in [".png", ".jpg", ".jpeg", ".jif"]:
        return True
    return False


def outputs_match(plugin, output_product, compare_product, threshold=0.05):
    """Use PIL and numpy to compare two images.

    Parameters
    ----------
    plugin: OutputCheckerPlugin
        The corresponding geotiff OutputCheckerPlugin that has access to needed methods
    output_product : str
        Current output product
    compare_product : str
        Path to comparison product
    threshold: float, default=0.05
        Threshold for the image comparison. Argument to pixelmatch.
        Between 0 and 1, with 0 the most strict comparison, and 1 the most lenient.

    Returns
    -------
    bool
        Return True if images match, False if they differ
    """
    exact_out_diffimg = plugin.get_out_diff_fname(
        compare_product, output_product, flag="exact_"
    )
    from PIL import Image
    import numpy as np
    from pixelmatch.contrib.PIL import pixelmatch

    LOG.info("**Comparing output_product vs. compare product")
    # Open existing images.
    out_img = Image.open(output_product)
    comp_img = Image.open(compare_product)
    diff_img = Image.new(mode="RGB", size=comp_img.size)
    # Compute the pixel diff between the two images.
    if np.array(comp_img).shape == np.array(out_img).shape:
        diff_arr = np.abs(np.array(comp_img) - np.array(out_img))
    # If shapes of arrays do not match, pixel diff can not be performed.
    # Print the names of the two images and associated shapes, and return False.
    else:
        LOG.interactive("    ***************************************")
        LOG.interactive("    *** BAD Images NOT match exactly, different sizes ***")
        LOG.interactive(
            "    ***   output_product: %s %s ***",
            np.array(out_img).shape,
            output_product,
        )
        LOG.interactive(
            "    ***   compare_product: %s %s ***",
            np.array(comp_img).shape,
            compare_product,
        )
        LOG.interactive("    ***************************************")
        return False
    # Determine the number of pixels that are mismatched
    LOG.info("Using threshold %s", threshold)
    thresholded_retval = pixelmatch(
        out_img, comp_img, diff_img, includeAA=True, alpha=0.33, threshold=threshold
    )
    # Currently, return 0 ONLY if the images are exactly matched.  Eventually
    # we may update this to allow returning 0 for "close enough" matches.
    if np.all(diff_arr == 0) and thresholded_retval == 0:
        fullimg_retval = 0
    else:
        fullimg_retval = 1
    # Write out the exact image difference.
    LOG.info("**Saving exact difference image")
    diff_img.save(exact_out_diffimg)
    LOG.info("**Done running compare")

    # If the images do not match exactly, print the output image, comparison image,
    # and exact diff image to log, for easy viewing.  Return False.
    if thresholded_retval != 0:
        bad_inds = np.where(diff_arr != 0)
        LOG.interactive("    ***************************************")
        LOG.interactive("    *** BAD Images do NOT match within tolerance ***")
        LOG.interactive("    *** ***")
        LOG.interactive(
            "    *** %s mismatched pixels exceeding threshold %s ***",
            thresholded_retval,
            threshold,
        )
        LOG.interactive("    *** %s mismatched exact ***", len(diff_arr[bad_inds]))
        LOG.interactive("    *** np.where(diff_arr != 0): %s ***", bad_inds)
        LOG.interactive("    *** diff_arr[bad_inds]: %s ***", diff_arr[bad_inds])
        LOG.interactive("    *** ***")
        LOG.interactive("    ***   output_product: %s ***", output_product)
        LOG.interactive("    ***   compare_product: %s ***", compare_product)
        LOG.interactive("    ***   exact dif image: %s ***", exact_out_diffimg)
        LOG.interactive("    ***************************************")
        return False

    # If the images match exactly, just output to GOOD comparison log to info level
    # (only bad comparisons to interactive level)
    if fullimg_retval != 0:
        if thresholded_retval == 0:
            bad_inds = np.where(diff_arr != 0)
        LOG.interactive("    ******************************************")
        LOG.interactive("    *** GOOD Images match within tolerance ***")
        LOG.interactive(
            "    *** %s mismatched pixels from exact comparison ***",
            len(diff_arr[bad_inds]),
        )
        LOG.interactive("    ******************************************")
    else:
        LOG.info("    *********************************")
        LOG.info("    *** GOOD Images match exactly ***")
        LOG.info("    *********************************")

    return True


def call(plugin, compare_path, output_products, threshold=0.05):
    """Compare the "correct" imagery found the list of current output_products.

    Compares files produced in the current processing run with the list of
    "correct" files contained in "compare_path".

    Parameters
    ----------
    plugin: OutputCheckerPlugin
        The corresponding image OutputCheckerPlugin that has access to needed methods
    compare_path : str
        Path to directory of "correct" products - filenames must match output_products
    output_products : list of str
        List of strings of current output products,
        to compare with products in compare_path
    threshold: float, default=0.05
        Threshold for the image comparison. Argument to pixelmatch.
        Between 0 and 1, with 0 the most strict comparison, and 1 the most lenient.

    Returns
    -------
    int
        Binary code: 0 if all comparisons were completed successfully.
    """
    retval = plugin.compare_outputs(
        compare_path,
        output_products,
        threshold=threshold,
    )
    return retval
