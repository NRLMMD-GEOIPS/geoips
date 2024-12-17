# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "Natural Color" EUMETSAT RGB product.

This algorithm expects three visible reflectances for an RGB image:
* 0.6 um
* 0.8 um
* 1.6 um
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_to_numpy"
name = "Natural_Color"


def call(xobj):
    """Natural Color RGB product algorithm data manipulation steps.

    This algorithm expects reflectance values for

    * Blue: 0.6 um, SEVIRI B03 Reflectances
    * Green: 0.8 um, SEVIRI B02 Reflectances
    * Red: 1.6 um, SEVIRI B01 Reflectances

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
    bt01 = xobj["B01Ref"].to_masked_array()  # 0.6 um reflectances, B01 SEVIRI
    bt02 = xobj["B02Ref"].to_masked_array()  # 0.8 um reflectances, B02 SEVIRI
    bt03 = xobj["B03Ref"].to_masked_array()  # 1.6 um, B03 SEVIRI

    data_range = [0.0, 1.0]

    from geoips.data_manipulations.corrections import apply_data_range

    red = apply_data_range(
        bt03,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )  # need inverse option?

    grn = apply_data_range(
        bt02,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )

    blu = apply_data_range(
        bt01,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )  # create image of deep clouds in blueish color
    # norm=True, inverse=False)    #create image of deep clouds in yellowish color

    from geoips.image_utils.mpl_utils import alpha_from_masked_arrays, rgba_from_arrays

    alp = alpha_from_masked_arrays([red, grn, blu])
    rgba = rgba_from_arrays(red, grn, blu, alp)

    return rgba
