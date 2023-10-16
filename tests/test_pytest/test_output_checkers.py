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
image = output_checkers.get_plugin("image")
savedir = str(environ["GEOIPS_PACKAGES_DIR"]) + "/test_data/test_images/pytest/"


def yield_images():
    """Yield a series of compare vs output image paths for testing purposes."""
    thresholds = ["lenient", "medium", "strict"]
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
            yield (comp_path, output_path)


@pytest.mark.parametrize("compare_path, output_path", yield_images())
def test_image_comparisons(compare_path, output_path):
    """Test the comparison of two images with the Image Output Checker."""
    threshold_floats = [0.1, 0.05, 0.0]
    for threshold in threshold_floats:
        image.module.outputs_match(image, output_path, compare_path, threshold)
