# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for geoips.image_utils.mpl_utils.rgba_from_arrays."""

import numpy as np

from geoips.image_utils.mpl_utils import rgba_from_arrays


def test_rgba_from_plain_arrays():
    """Plain numpy arrays with an explicit alpha are stacked unchanged."""
    red = np.full((2, 3), 0.2)
    grn = np.full((2, 3), 0.4)
    blu = np.full((2, 3), 0.6)
    alp = np.ones((2, 3))

    rgba = rgba_from_arrays(red, grn, blu, alp)

    assert rgba.shape == (2, 3, 4)
    np.testing.assert_allclose(rgba[:, :, 0], 0.2)
    np.testing.assert_allclose(rgba[:, :, 1], 0.4)
    np.testing.assert_allclose(rgba[:, :, 2], 0.6)
    np.testing.assert_allclose(rgba[:, :, 3], 1)


def test_rgba_from_masked_arrays():
    """Masked values are filled with 0 and the inputs' fill_value is unchanged."""
    mask = np.array([[True, False], [False, False]])
    red = np.ma.masked_array(np.full((2, 2), 0.5), mask=mask, fill_value=-999)
    grn = np.ma.masked_array(np.full((2, 2), 0.5), mask=mask, fill_value=-999)
    blu = np.ma.masked_array(np.full((2, 2), 0.5), mask=mask, fill_value=-999)

    rgba = rgba_from_arrays(red, grn, blu)

    assert rgba.shape == (2, 2, 4)
    assert not np.ma.isMaskedArray(rgba)
    np.testing.assert_allclose(rgba[0, 0, :3], 0)
    np.testing.assert_allclose(rgba[1, 1, :3], 0.5)
    assert rgba[0, 0, 3] == 0
    assert rgba[1, 1, 3] == 1
    assert red.fill_value == -999
