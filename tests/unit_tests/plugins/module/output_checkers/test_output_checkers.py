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

"""Test all Output Checker plugins."""
import pytest
from PIL import Image
import numpy as np
from os import environ

from geoips.interfaces import output_checkers
from geoips.commandline import log_setup


log_setup.setup_logging()


class TestOutputCheckers:
    """TestOutputChecker class, defining methods as well."""

    image = output_checkers.get_plugin("image")
    savedir = str(environ["GEOIPS_PACKAGES_DIR"]) + "/test_data/test_images/pytest/"
    available_output_checkers = {
        "geotiff": (False, False),
        "image": (True, True),
        "netcdf": (False, False),
        "text": (False, False),
    }

    def yield_images(self):
        """Return a series of compare vs output image paths for testing purposes."""
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
                comp_path = self.savedir + "comp_img_" + threshold + str(i) + ".png"
                output_path = self.savedir + "output_img_" + threshold + str(i) + ".png"
                comp_img.save(comp_path)
                output_img.save(output_path)
                compare_paths.append(comp_path)
                output_paths.append(output_path)
        return compare_paths, output_paths

    def image_comparisons(self, compare_paths, output_paths):
        """Test the comparison of two images with the Image Output Checker."""
        threshold_floats = [0.1, 0.05, 0.0]
        for threshold in threshold_floats:
            for path_idx in range(len(compare_paths)):
                self.image.module.outputs_match(
                    self.image,
                    output_paths[path_idx],
                    compare_paths[path_idx],
                    threshold,
                )

    @pytest.mark.parametrize("checker_name", available_output_checkers)
    def test_plugins(self, checker_name):
        """Test all output_checkers that are ready for testing."""
        output_checker = self.available_output_checkers[checker_name]
        if not output_checker[0] or not output_checker[1]:
            pytest.xfail(checker_name + " is not ready to be tested yet.")
        if checker_name == "image":
            compare_paths, output_paths = self.yield_images()
            self.image_comparisons(compare_paths, output_paths)
