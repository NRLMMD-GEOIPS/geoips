# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "Convective_Storms" EUMETSAT RGB product.

This algorithm expects five Infrared/Visible channels for an RGB image:
* Red SEVIRI B05BT - B06BT
* Green SEVIRI B04BT - B09BT
* Blue SEVIRI B03Ref - B01Ref
"""

from ast import literal_eval

from geoips.interfaces.class_based.algorithms import BaseAlgorithmPlugin
from geoips.interfaces import algorithm_configs

import logging

LOG = logging.getLogger(__name__)


class ConvectiveStormAlgorithmPlugin(BaseAlgorithmPlugin):
    """Convective Storm algorithm plugin class."""

    interface = "algorithms"
    family = "xarray_to_numpy"
    name = "config_rgb"

    def call(self, xobj, config_name):  # NOQA -- xobj is used in the literal eval calls
        """Dust RGB product algorithm data manipulation steps.

        This algorithm expects TBs from five SEVIRI channels:

        * Red: B05BT - B06BT
        * Green: B04BT - B09BT
        * Blue: B03Ref - B01Ref

        Parameters
        ----------
        xobj : xarray.Dataset
            The dataset containing variables needed for a given rgb recipe.
        config_name : str
            The name of the config plugin that contains the RGB recipe.

        Returns
        -------
        numpy.ndarray
            numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output
        """
        config = algorithm_configs.get_plugin(config_name)

        red = literal_eval(config["spec"]["red"]["equation"])
        grn = literal_eval(config["spec"]["green"]["equation"])
        blu = literal_eval(config["spec"]["blue"]["equation"])

        input_units_red = config["spec"]["red"]["input_units"]
        output_units_red = config["spec"]["red"]["output_units"]
        input_units_grn = config["spec"]["green"]["input_units"]
        output_units_grn = config["spec"]["green"]["output_units"]
        input_units_blu = config["spec"]["blue"]["input_units"]
        output_units_blu = config["spec"]["blue"]["output_units"]

        # Convert TB from Kevin to Celsius
        from geoips.data_manipulations.conversions import unit_conversion

        red = unit_conversion(
            red, input_units=input_units_red, output_units=output_units_red
        )
        grn = unit_conversion(
            grn, input_units=input_units_grn, output_units=output_units_grn
        )
        blu = unit_conversion(
            blu, input_units=input_units_blu, output_units=output_units_blu
        )

        from geoips.data_manipulations.corrections import apply_data_range, apply_gamma

        data_range = config["spec"]["red"]["data_range"]
        gamma = config["spec"]["red"]["gamma"]
        red = apply_data_range(
            red,
            min_val=data_range[0],
            max_val=data_range[1],
            min_outbounds="crop",
            max_outbounds="crop",
            norm=True,
            inverse=False,
        )  # need inverse option?
        red = apply_gamma(red, gamma)

        data_range = config["spec"]["green"]["data_range"]
        gamma = config["spec"]["green"]["gamma"]
        grn = apply_data_range(
            grn,
            min_val=data_range[0],
            max_val=data_range[1],
            min_outbounds="crop",
            max_outbounds="crop",
            norm=True,
            inverse=False,
        )
        grn = apply_gamma(grn, gamma)

        data_range = config["spec"]["blue"]["data_range"]
        gamma = config["spec"]["blue"]["gamma"]
        blu = apply_data_range(
            blu,
            min_val=data_range[0],
            max_val=data_range[1],
            min_outbounds="crop",
            max_outbounds="crop",
            norm=True,
            inverse=False,
        )  # create image of deep clouds in blueish color
        # norm=True, inverse=False)    #create image of deep clouds in yellowish color
        blu = apply_gamma(blu, gamma)

        from geoips.image_utils.mpl_utils import (
            alpha_from_masked_arrays,
            rgba_from_arrays,
        )

        alp = alpha_from_masked_arrays([red, grn, blu])
        rgba = rgba_from_arrays(red, grn, blu, alp)

        return rgba


PLUGIN_CLASS = ConvectiveStormAlgorithmPlugin
