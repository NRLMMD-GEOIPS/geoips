# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "Volcanic-Ash" EUMETSAT RGB product.

This algorithm expects three Infrared/Visible channels for an RGB image:
* Red SEVIRI B10BT - B09BT
* Green SEVIRI B09BT - B07BT
* Blue SEVIRI B09BT
"""

import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_to_numpy"
name = "Volcanic_Ash"


def call(xobj):
    """Night_Microphys product algorithm data manipulation steps.

    This algorithm expects TBs from three SEVIRI channels:

    * Red: B10BT - B09BT
    * Green: B09BT - B07BT
    * Blue: B07BT

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data,
            in order of sensor "channels" list
        * Unit in Degrees Kelvin and reflectance

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output
    """
    bt07 = xobj["B07BT"].to_masked_array()  # 3.9 um TBs, B04 SEVIRI
    bt09 = xobj["B09BT"].to_masked_array()  # 10.8 um reflectance, B09 SEVIRI
    bt10 = xobj["B10BT"].to_masked_array()  # 12.0 um reflectance, B10 SEVIRI

    # Convert TB from Kevin to Celsius
    from geoips.data_manipulations.conversions import unit_conversion

    bt07 = unit_conversion(bt07, input_units="Kelvin", output_units="celsius")
    bt09 = unit_conversion(bt09, input_units="Kelvin", output_units="celsius")
    bt10 = unit_conversion(bt10, input_units="Kelvin", output_units="celsius")

    from geoips.data_manipulations.corrections import apply_data_range, apply_gamma

    data_range = [-4, 2]
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
    # Note: may need additional solar correction

    data_range = [-4, 5]
    grn = apply_data_range(
        bt09 - bt07,
        min_val=data_range[0],
        max_val=data_range[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )
    grn = apply_gamma(grn, 1.0)
    grn = apply_gamma(grn, 1.0)
    # Note: may need additional solar correction

    data_range = [-30, 30]
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
