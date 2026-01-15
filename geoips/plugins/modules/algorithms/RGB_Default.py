# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "Night_Vis_IR" product.

This algorithm expects two VIIRS channels (DNBRad and M16BT) for a RGB image
"""
import logging

from geoips.image_utils.mpl_utils import alpha_from_masked_arrays, rgba_from_arrays
from geoips.data_manipulations.corrections import apply_solar_zenith_correction
from geoips.data_manipulations.corrections import apply_data_range

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "RGB_Default"


def call(
    arrays,
    sun_zen_correction=False,
    output_data_range=None,
    min_outbounds="crop",
    max_outbounds="crop",
    norm=True,
    inverse=False,
):
    """Apply default RGB algorithm.

    Plots RGB with the red gun being the first variable specified in the
    product YAML, green second, and blue third.

    Full support for this algorithm is still a WIP.

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data,
            in order of sensor "channels" list

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output
    """
    red = arrays[0]  # Red gun: First listed variable
    grn = arrays[1]  # Green gun: Second listed variable
    blu = arrays[2]  # Blue gun: Third listed variable

    if sun_zen_correction and len(arrays) >= 4:
        sun_zenith = arrays[3]

        red = apply_solar_zenith_correction(red, sun_zenith)
        grn = apply_solar_zenith_correction(grn, sun_zenith)
        blu = apply_solar_zenith_correction(blu, sun_zenith)

    if output_data_range is None:
        output_data_range = [red.min(), red.max()]
    red = apply_data_range(
        red,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )
    if output_data_range is None:
        output_data_range = [grn.min(), grn.max()]
    grn = apply_data_range(
        grn,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )

    if output_data_range is None:
        output_data_range = [blu.min(), blu.max()]
    blu = apply_data_range(
        blu,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )

    alp = alpha_from_masked_arrays([red, grn, blu])
    rgba = rgba_from_arrays(red, grn, blu, alp)

    return rgba
