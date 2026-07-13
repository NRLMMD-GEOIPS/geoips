# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test script for representative product comparisons."""

import logging
from PIL import Image
import numpy as np
from os import makedirs
from os.path import exists, join, splitext

from geoips.interfaces.class_based.output_checkers import BaseOutputCheckerPlugin
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
        threshold=gpaths["GEOIPS_TEST_OUTPUT_CHECKER_THRESHOLD_IMAGE"],
    ):
        """Use PIL, numpy, and pixelmatch to compare two images.

        Exact matches pass immediately. Non-exact matches always log comparison
        statistics, but only fail if the pixelmatch thresholded mismatch fraction
        exceeds the configured tolerance.
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
                "pixelmatch (link: https://pypi.org/project/pixelmatch/). "
                "You can install it directly or install the test extra, eg. "
                "pip install geoips[test]"
            ) from e

        from geoips.commandline.log_setup import log_with_emphasis

        LOG.info("**Comparing output_product vs. compare product")

        out_img = Image.open(output_product).convert("RGBA")
        comp_img = Image.open(compare_product).convert("RGBA")

        out_arr = np.asarray(out_img)
        comp_arr = np.asarray(comp_img)

        if out_arr.shape != comp_arr.shape:
            log_with_emphasis(
                LOG.interactive,
                "BAD Images do NOT match, different sizes",
                f"output_product: {out_arr.shape} {output_product}",
                f"compare_product: {comp_arr.shape} {compare_product}",
            )
            return False

        # PNG arrays are typically uint8. Cast before subtracting to avoid
        # wraparound, eg. uint8(0) - uint8(255) == uint8(1).
        out_i16 = out_arr.astype(np.int16)
        comp_i16 = comp_arr.astype(np.int16)
        diff_arr = np.abs(comp_i16 - out_i16)

        if diff_arr.max() == 0:
            log_with_emphasis(LOG.info, "GOOD Images match exactly")
            return True

        # RGB-only diagnostics. Alpha is ignored for these summary stats because
        # the rendered RGB image is usually the scientifically relevant output.
        rgb_diff = diff_arr[..., :3]

        num_total_pixels = rgb_diff.shape[0] * rgb_diff.shape[1]

        exact_mismatched_pixels = np.any(rgb_diff != 0, axis=-1)
        num_mismatched_exactly = int(np.count_nonzero(exact_mismatched_pixels))
        exact_mismatch_fraction = num_mismatched_exactly / num_total_pixels

        channel_diff_cutoff = 2
        changed_pixels = np.any(rgb_diff > channel_diff_cutoff, axis=-1)
        num_changed_pixels = int(np.count_nonzero(changed_pixels))
        changed_pixel_fraction = num_changed_pixels / num_total_pixels

        max_abs_diff = int(rgb_diff.max())
        mean_abs_diff = float(rgb_diff.mean())

        # Generate diagnostic diff images.
        diff_img = Image.new(mode=out_img.mode, size=comp_img.size)
        exact_diff_img = Image.new(mode=out_img.mode, size=comp_img.size)

        LOG.info("Using pixelmatch threshold %s", threshold)

        thresholded_retval = pixelmatch(
            out_img,
            comp_img,
            diff_img,
            includeAA=True,
            alpha=0.33,
            threshold=threshold,
        )
        exact_retval = pixelmatch(
            out_img,
            comp_img,
            exact_diff_img,
            includeAA=True,
            alpha=0.33,
            threshold=0,
        )

        LOG.info("**Saving exact difference image")
        exact_diff_img.save(exact_out_diffimg_fname)

        LOG.info("**Saving threshold-applied difference image")
        diff_img.save(out_diffimg_fname)

        LOG.info("**Done running compare")

        thresholded_pixel_fraction = thresholded_retval / num_total_pixels

        # threshold=0.05 means:
        # - pixelmatch sensitivity threshold of 0.05
        # - allow up to 0.05% of pixels to exceed that pixelmatch threshold
        allowed_thresholded_pixel_fraction = threshold / 100.0

        failure_reasons = []

        if thresholded_pixel_fraction > allowed_thresholded_pixel_fraction:
            failure_reasons.append(
                "Pixelmatch thresholded pixel fraction exceeded tolerance "
                f"({thresholded_pixel_fraction:.6%} > "
                f"{allowed_thresholded_pixel_fraction:.6%})"
            )

        passes = len(failure_reasons) == 0

        log_func = LOG.info if passes else LOG.interactive
        status = (
            "GOOD Images differ but are within tolerance"
            if passes
            else "BAD Images do NOT match within tolerance"
        )

        log_lines = [status]

        if failure_reasons:
            log_lines.append("Failure reason(s):")
            log_lines.extend(f"  - {reason}" for reason in failure_reasons)

        log_lines.extend(
            [
                f"output_product: {output_product}",
                f"compare_product: {compare_product}",
                f"exact diff image: {exact_out_diffimg_fname}",
                f"thresholded diff image: {out_diffimg_fname}",
                "",
                "Comparison statistics:",
                f"  Total pixels:                         {num_total_pixels:,}",
                f"  Exact mismatched pixels:              {num_mismatched_exactly:,}",
                f"  Exact mismatch fraction:              {exact_mismatch_fraction:.6%}",
                f"  Pixels with any RGB channel > {channel_diff_cutoff} DN:"
                f" {num_changed_pixels:,}",
                f"  Fraction with any channel > {channel_diff_cutoff} DN:"
                f" {changed_pixel_fraction:.6%}",
                f"  Mean absolute RGB difference:         {mean_abs_diff:.6f}",
                f"  Maximum RGB channel difference:       {max_abs_diff}",
                "",
                "Pixelmatch pass/fail:",
                f"  Pixelmatch threshold:                 {threshold}",
                f"  Pixelmatch thresholded mismatches:    {thresholded_retval:,}",
                f"  Pixelmatch thresholded fraction:      "
                f"{thresholded_pixel_fraction:.6%}",
                f"  Allowed thresholded fraction:         "
                f"{allowed_thresholded_pixel_fraction:.6%}",
                f"  Pixelmatch exact mismatches:          {exact_retval:,}",
            ]
        )

        log_with_emphasis(log_func, *log_lines)

        return passes

    def call(
        self,
        compare_path,
        output_products,
        threshold=gpaths["GEOIPS_TEST_OUTPUT_CHECKER_THRESHOLD_IMAGE"],
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
