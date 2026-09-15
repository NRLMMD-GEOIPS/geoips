# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Cloud depth product.

Difference of cloud top height and cloud base height.

This is the doc-owned example used by the :ref:`algorithm tutorial <add-an-algorithm>`.
It is imported and executed by ``tests/unit_tests/docs/test_tutorial_examples.py``
so the code shown in the tutorial is exercised in CI.
"""

import logging

from xarray import DataArray

from geoips.interfaces.class_based.algorithms import BaseAlgorithmPlugin

LOG = logging.getLogger(__name__)


class MyCloudDepthAlgorithmPlugin(BaseAlgorithmPlugin):
    """My cloud depth algorithm plugin.

    Difference of cloud top height and cloud base height, scaled to kilometers.
    """

    interface = "algorithms"
    family = "xarray_to_xarray"
    name = "my_cloud_depth"

    def call(
        self,
        xobj,  # xarray Dataset holding the input variables
        variables,  # ordered list of required input variables (see product plugin)
        product_name,
        output_data_range,  # range of values the algorithm will output
        scale_factor,  # converts input meters to output kilometers
        min_outbounds="crop",
        max_outbounds="mask",
        norm=False,
        inverse=False,
    ):
        """Apply the cloud-depth manipulation steps to the input data."""
        from geoips.data_manipulations.corrections import apply_data_range

        cth = xobj[variables[0]]
        cbh = xobj[variables[1]]

        out = (cth - cbh) * scale_factor

        data = apply_data_range(
            out,
            min_val=output_data_range[0],
            max_val=output_data_range[1],
            min_outbounds=min_outbounds,
            max_outbounds=max_outbounds,
            norm=norm,
            inverse=inverse,
        )
        xobj[product_name] = DataArray(data)

        return xobj


# Tells pluginify (the plugin registry) which object in this module is the plugin.
PLUGIN_CLASS = MyCloudDepthAlgorithmPlugin
