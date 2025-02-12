# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "Dust" EUMETSAT RGB product.

This algorithm expects three visible reflectances for an RGB image:
* Red SEVIRI B10BT - B09BT
* Green SEVIRI B09BT - B07BT
* Blue SEVIRI B09BT
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_to_numpy"
name = "Dust_RGB"


def call(xobj):
    """Dust RGB product algorithm data manipulation steps.

    This algorithm expects reflectance values for

    * Red SEVIRI B10BT - B09BT
    * Green SEVIRI B09BT - B07BT
    * Blue SEVIRI B09BT

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data,
            in order of sensor "channels" list
        * Degrees Kelvin

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output
    """
    bt07 = xobj["B07BT"].to_masked_array()  # 8.7 um TB, B07 SEVIRI
    bt09 = xobj["B09BT"].to_masked_array()  # 10.8 um TB, B09 SEVIRI
    bt10 = xobj["B10BT"].to_masked_array()  # 12.0 um TB, B10 SEVIRI

    from geoips.data_manipulations.corrections import apply_data_range, apply_gamma

    data_range = [-4, 2.0]
    red = apply_data_range(
        bt10 - bt09,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )  # need inverse option?
    red = apply_gamma(red, 1.0)
    red = apply_gamma(red, 1.0)

    data_range = [0, 15.0]
    grn = apply_data_range(
        bt09 - bt07,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )
    grn = apply_gamma(grn, 2.5)
    grn = apply_gamma(grn, 1.0)

    data_range = [261.0, 289.0]
    blu = apply_data_range(
        bt09,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )  # create image of deep clouds in blueish color
    # norm=True, inverse=False)    #create image of deep clouds in yellowish color
    blu = apply_gamma(blu, 1.0)
    blu = apply_gamma(blu, 1.0)

    from geoips.image_utils.mpl_utils import alpha_from_masked_arrays, rgba_from_arrays

    alp = alpha_from_masked_arrays([red, grn, blu])
    rgba = rgba_from_arrays(red, grn, blu, alp)

    return rgba
