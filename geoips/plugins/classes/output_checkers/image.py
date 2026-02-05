# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test script for representative product comparisons."""

import logging
from PIL import Image
import numpy as np
from os import makedirs
from os.path import exists, join, splitext

from geoips.base_class_plugins.output_checkers import BaseOutputCheckerPlugin
from geoips.filenames.base_paths import PATHS as gpaths
from geoips.geoips_utils import get_numpy_seeded_random_generator

LOG = logging.getLogger(__name__)


class ImageOutputCheckerPlugin(BaseOutputCheckerPlugin):
    """Image Output Checker Plugin Class.

    Inherits from BaseOutputCheckerPlugin, which contains shared functionality among
    output_checker plugins. Responsible for comparing two image files
    (produced, expected) within a given threshold.
    """

    interface = "output_checkers"
    family = "standard"
    name = "image"

    def get_test_files(self, test_data_dir):
        """Return a series of compare vs output image paths for testing purposes."""
        savedir = join(test_data_dir, "scratch", "unit_tests", "test_images/")
        if not exists(savedir):
            makedirs(savedir)

        thresholds = ["lenient", "medium", "strict"]
        # thresholds is used for naming files.
        # Relates to thresholds [0.1, 0.05, 0.0]
        compare_files = []
        test_files = []

        predictable_random = get_numpy_seeded_random_generator()

        for threshold in thresholds:
            for i in range(3):
                comp_arr = predictable_random.rand(100, 100, 3)
                test_arr = np.copy(comp_arr)
                if i == 1:
                    rand = predictable_random.randint(0, 100)
                    test_arr[rand][:] = predictable_random.rand(3)
                elif i == 2:
                    test_arr = predictable_random.rand(100, 100, 3)
                comp_img = Image.fromarray((comp_arr * 255).astype(np.uint8))
                test_img = Image.fromarray((test_arr * 255).astype(np.uint8))
                comp_file = join(savedir, f"comp_img_{threshold}{str(i)}.png")
                test_file = join(savedir, f"test_img_{threshold}{str(i)}.png")
                comp_img.save(comp_file)
                test_img.save(test_file)
                compare_files.append(comp_file)
                test_files.append(test_file)
        return compare_files, test_files

    def perform_test_comparisons(self, compare_files, test_files):
        """Test the comparison of two images with the Image Output Checker.

        Parameters
        ----------
        compare_file : str
            Path to the comparison (baseline) file.
        test_files : list[str]
            List of test file paths [matched, close_mismatch, bad_mismatch].

        Raises
        ------
        AssertionError
            If any comparison result doesn't match expected outcome.
        """
        threshold_floats = [0.1, 0.05, 0.0]
        for threshold in threshold_floats:
            for path_idx in range(len(compare_files)):
                retval = self.outputs_match(
                    test_files[path_idx],
                    compare_files[path_idx],
                    threshold,
                )
                if path_idx % 3 == 0:
                    assert retval is True
                else:
                    assert retval is False

    def correct_file_format(self, fname):
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
        if splitext(fname)[-1] in [".png", ".jpg", ".jpeg"]:
            return True
        return False

    def outputs_match(
        self,
        output_product,
        compare_product,
        threshold=gpaths["OUTPUT_CHECKER_THRESHOLD_IMAGE"],
    ):
        """Use PIL and numpy to compare two images.

        Parameters
        ----------
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
        exact_out_diffimg_fname = self.get_out_diff_fname(
            compare_product, output_product, flag="exact_"
        )
        out_diffimg_fname = self.get_out_diff_fname(compare_product, output_product)

        try:
            from pixelmatch.contrib.PIL import pixelmatch
        except ImportError as e:
            raise ImportError(
                "Comparing images using GeoIPS requires a python library called "
                "pixelmatch (link: https://pypi.org/project/pixelmatch/)."
                "You can install it directly or install the test extra"
                " eg. pip install geoips[test]"
            ) from e

        from geoips.commandline.log_setup import log_with_emphasis

        LOG.info("**Comparing output_product vs. compare product")
        # Open existing images.
        out_img = Image.open(output_product)
        comp_img = Image.open(compare_product)
        diff_img = Image.new(mode="RGB", size=comp_img.size)
        exact_diff_img = Image.new(mode="RGB", size=comp_img.size)
        # Compute the pixel diff between the two images.
        if np.array(comp_img).shape == np.array(out_img).shape:
            diff_arr = np.abs(np.array(comp_img) - np.array(out_img))
        # If shapes of arrays do not match, pixel diff can not be performed.
        # Print the names of the two images and associated shapes, and return False.
        else:
            log_with_emphasis(
                LOG.interactive,
                "BAD Images NOT match exactly, different sizes",
            )
            message = f"output_product: {np.array(out_img).shape} {output_product}"
            log_with_emphasis(LOG.interactive, message)
            message = f"compare_product: {np.array(comp_img).shape} {compare_product}"
            log_with_emphasis(LOG.interactive, message)
            return False
        # Don't bother doing pixelmatch if the arrays are identical.
        # Make sure the min/max values are both 0 in the diff image.
        # If there happen to be any NaNs in the diff_arr, this test will fail, because
        # diff_arr.min/max return nan if there are any NaNs in the array.
        # For the record, I don't think PIL Image would have nan values, but
        # this should be safe (since NaNs will result in moving onto the pixelmatch
        # tests).
        if diff_arr.min() == 0 and diff_arr.max() == 0:
            # If the images match exactly, just output to GOOD comparison log to info
            # level (only bad comparisons to interactive level)
            log_with_emphasis(
                LOG.info,
                "GOOD Images match exactly",
            )
            return True

        # Determine the number of pixels that are mismatched
        LOG.info("Using pixelmatch threshold %s", threshold)
        thresholded_retval = pixelmatch(
            out_img, comp_img, diff_img, includeAA=True, alpha=0.33, threshold=threshold
        )
        exact_retval = pixelmatch(
            out_img, comp_img, exact_diff_img, includeAA=True, alpha=0.33, threshold=0
        )
        # Write out the exact image difference.
        LOG.info("**Saving exact difference image")
        exact_diff_img.save(exact_out_diffimg_fname)
        # Write out the threshold-applied image difference.
        LOG.info("**Saving threshold-applied difference image")
        diff_img.save(out_diffimg_fname)
        LOG.info("**Done running compare")

        bad_inds = np.where(diff_arr != 0)
        num_mismatched_exactly = len(diff_arr[bad_inds])
        num_mismatched_by_threshold = thresholded_retval
        num_total_pixels = diff_img.size[0] * diff_img.size[1]
        bad_threshold_pct = num_mismatched_by_threshold / num_total_pixels
        bad_exact_pct = num_mismatched_exactly / num_total_pixels

        # If the images do not match exactly, print the output image, comparison image,
        # and exact diff image to log, for easy viewing.  Return False.

        # NOTE: We should discuss what values we'd like to set, or be dynamic for
        # testing bad_threshold_pct and bad_exact_pct. This is just a first value and
        # will likely change once we've decided what percentage of failures we'll allow.
        if bad_threshold_pct > (threshold / 1000):
            log_with_emphasis(
                LOG.interactive,
                "BAD Images do NOT match within tolerance",
                f"np.where(diff_arr != 0): {bad_inds}",
                f"diff_arr[bad_inds]: {diff_arr[bad_inds]}",
                f"{thresholded_retval} mismatched pixels "
                f"exceeding pixelmatch threshold {threshold}",
                f"{exact_retval} mismatched pixels exceeding pixelmatch threshold 0"
                f"{len(diff_arr[bad_inds])} mismatched exact of {num_total_pixels} "
                f"pixels percentage diff exact {bad_exact_pct}",
                f"percentage diff thresholded {bad_threshold_pct}",
                f"output_product: {output_product}",
                f"compare_product: {compare_product}",
                f"exact diff image: {exact_out_diffimg_fname}",
                f"thresholded diff image: {out_diffimg_fname}",
            )
            return False
        else:
            log_with_emphasis(
                LOG.interactive,
                "GOOD Images match within tolerance",
                f"{len(diff_arr[bad_inds])} mismatched exact of {num_total_pixels} "
                f"pixels {thresholded_retval} mismatched pixels "
                f"exceeding pixelmatch threshold {threshold}",
            )
            log_with_emphasis(
                LOG.info,
                "GOOD Images match within tolerance",
                f"np.where(diff_arr != 0): {bad_inds}",
                f"diff_arr[bad_inds]: {diff_arr[bad_inds]}",
                f"{thresholded_retval} mismatched pixels "
                f"exceeding pixelmatch threshold {threshold}",
                f"{exact_retval} mismatched pixels exceeding pixelmatch threshold 0",
                f"{len(diff_arr[bad_inds])} mismatched exact of {num_total_pixels} "
                f"pixels percentage diff exact {bad_exact_pct}",
                f"percentage diff thresholded {bad_threshold_pct}",
                f"output_product: {output_product}",
                f"compare_product: {compare_product}",
                f"exact diff image: {exact_out_diffimg_fname}",
                f"thresholded diff image: {out_diffimg_fname}",
            )

        return True

    def call(
        self,
        compare_path,
        output_products,
        threshold=gpaths["OUTPUT_CHECKER_THRESHOLD_IMAGE"],
    ):
        """Compare the "correct" imagery found the list of current output_products.

        Compares files produced in the current processing run with the list of
        "correct" files contained in "compare_path".

        Parameters
        ----------
        compare_path : str
            Path to directory of "correct" products - filenames must match
            output_products
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
        retval = self.compare_outputs(
            compare_path,
            output_products,
            threshold=threshold,
        )
        return retval


PLUGIN_CLASS = ImageOutputCheckerPlugin
