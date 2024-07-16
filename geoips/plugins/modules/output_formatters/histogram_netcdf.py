# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Produce histogram from the given dataset with specified bin size."""
import logging
import numpy

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xarray_data"
name = "histogram_json"


def call(
    xarray_obj, product_names, output_fnames, min_val=None, max_val=None, num_bins=501
):
    """Produce histogram.

    Parameters
    ----------
    xarray_obj: xarray Dataset

    Returns
    -------
    xarray.Dataset
        Resulting histogram
    """
    import xarray

    prod_xarray = xarray.Dataset()

    from geoips.geoips_utils import copy_standard_metadata

    copy_standard_metadata(xarray_obj, prod_xarray)
    for product_name in product_names:
        prod_xarray[product_name] = xarray_obj[product_name]

        if product_name == "latitude" or product_name == "longitude":
            continue
        xda = xarray_obj[product_name]
        hist = numpy.histogram(xda, numpy.linspace(min_val, max_val, num_bins + 1))
        prod_xarray[f"{product_name}_histogram"] = xarray.DataArray(
            hist[0], dims=("dim_2")
        )
        prod_xarray["bins"] = xarray.DataArray(hist[1], dims=("dim_3"))

    from geoips.plugins.modules.output_formatters.netcdf_xarray import (
        write_xarray_netcdf,
    )

    for ncdf_fname in output_fnames:
        write_xarray_netcdf(prod_xarray, ncdf_fname)
    return output_fnames
