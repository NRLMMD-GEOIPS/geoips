# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "airmass" EUMETSAT RGB product.

This algorithm expects four Infrared channels for an RGB image:
* Red SEVIRI B05BT - B06BT
* Green SEVIRI B08BT - B09BT
* Blue SEVIRI B05BT
"""

import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_to_numpy"
name = "airmass"


def call(xobj):
    """Airmass product algorithm data manipulation steps.

    This algorithm expects TBs from four SEVIRI channels:

    * Red: B05BT - B06BT
    * Green: B08BT - B09BT
    * Blue: B05BT

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
    bt05 = xobj["B05BT"].to_masked_array()  # 6.2 um TBs, B05 SEVIRI
    bt06 = xobj["B06BT"].to_masked_array()  # 7.3 um TBs, B06 SEVIRI
    bt08 = xobj["B08BT"].to_masked_array()  # 9.7 um TBs, B08 SEVIRI
    bt09 = xobj["B09BT"].to_masked_array()  # 10.8 um TBs, B09 SEVIRI

    # Convert TB from Kevin to Celsius
    from geoips.data_manipulations.conversions import unit_conversion

    bt05 = unit_conversion(bt05, input_units="Kelvin", output_units="celsius")
    bt06 = unit_conversion(bt06, input_units="Kelvin", output_units="celsius")
    bt08 = unit_conversion(bt08, input_units="Kelvin", output_units="celsius")
    bt09 = unit_conversion(bt09, input_units="Kelvin", output_units="celsius")

    from geoips.data_manipulations.corrections import apply_data_range, apply_gamma

    data_range = [-25, 0]
    red = apply_data_range(
        bt05 - bt06,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )  # need inverse option?
    red = apply_gamma(red, 1.0)
    red = apply_gamma(red, 1.0)

    data_range = [-40, 5]
    grn = apply_data_range(
        bt08 - bt09,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )
    grn = apply_gamma(grn, 1.0)
    grn = apply_gamma(grn, 1.0)

    data_range = [-65, -30]
    blu = apply_data_range(
        bt05,
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
