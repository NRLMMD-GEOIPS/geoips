# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolation methods using pyresample routines."""

import logging

import numpy
from pyresample import kd_tree

LOG = logging.getLogger(__name__)

# interface = None indicates to the GeoIPS interfaces that this is not a valid
# plugin, and this module will not be added to the GeoIPS plugin registry.
# This allows including python modules within the geoips/plugins directory
# that provide helper or utility functions to the geoips plugins, but are
# not full GeoIPS plugins on their own.
interface = None


def get_data_box_definition(source_name, lons, lats):
    """Obtain pyresample geometry definitions.

    For use with pyresample based reprojections

    Parameters
    ----------
    source_name : str
        geoips source_name for data type
    lons : ndarray
        Numpy array of longitudes, 0 to 360
    lats : ndarray
        Numpy array of latitudes, -90 to 90
    """
    from geoips.plugins.modules.interpolators.utils.boxdefinitions import (
        MaskedCornersSwathDefinition,
    )
    from geoips.plugins.modules.interpolators.utils.boxdefinitions import (
        PlanarPolygonDefinition,
    )
    from pyresample.geometry import GridDefinition

    if source_name == "abi" and lons.ndim > 1:
        data_box_definition = GridDefinition(
            lons=numpy.ma.array(lons, subok=False),
            lats=numpy.ma.array(lats, subok=False),
        )
    if source_name == "ahi":
        data_box_definition = PlanarPolygonDefinition(
            lons=numpy.ma.array(lons, subok=False),
            lats=numpy.ma.array(lats, subok=False),
        )
    else:
        data_box_definition = MaskedCornersSwathDefinition(
            lons=numpy.ma.array(lons, subok=False),
            lats=numpy.ma.array(lats, subok=False),
        )

    return data_box_definition


def interp_kd_tree(
    list_of_arrays,
    area_definition,
    data_box_definition,
    radius_of_influence,
    interp_type="nearest",
    sigmas=None,
    neighbours=None,
    nprocs=None,
    fill_value=None,
):
    """Interpolate using pyresample's kd_tree.resample_nearest method.

    Parameters
    ----------
    list_of_array : list of numpy.ndarray
        list of arrays to be interpolated
    area_definition : areadef
        pyresample area_definition object of current region of interest.
    data_box_definition : datadef
        pyresample/geoips data_box_definition specifying region covered
        by source data.
    radius_of_influence : float
        radius of influence for interpolation

    Other Parameters
    ----------------
    interp_type : str, default='nearest'
        One of 'nearest' or 'gauss' - kd_tree resampling methods.
    sigmas : int, default=None
        Used for interp_type 'gauss' - multiplication factor for sigmas option:
            * sigmas = [sigmas]*len(list_of_arrays)
    """
    dstacked_arrays = numpy.ma.dstack(list_of_arrays)

    if interp_type == "nearest":
        kw_args = {}
        kw_args["fill_value"] = None
        kw_args["radius_of_influence"] = radius_of_influence
        if nprocs is not None:
            kw_args["nprocs"] = nprocs
        LOG.info("Using interp_type %s", interp_type)
        dstacked_arrays = kd_tree.resample_nearest(
            data_box_definition,
            dstacked_arrays,
            area_definition,
            **kw_args,
        )
    elif interp_type == "gauss":
        kw_args = {}
        kw_args["sigmas"] = [4000] * len(list_of_arrays)
        kw_args["fill_value"] = None
        kw_args["radius_of_influence"] = radius_of_influence

        if sigmas is not None:
            kw_args["sigmas"] = [sigmas] * len(list_of_arrays)
        if neighbours is not None:
            kw_args["neighbours"] = neighbours
        if nprocs is not None:
            kw_args["nprocs"] = nprocs
        if fill_value is not None:
            kw_args["fill_value"] = fill_value

        LOG.info("Using interp_type %s %s", interp_type, sigmas)
        dstacked_arrays = kd_tree.resample_gauss(
            data_box_definition, dstacked_arrays, area_definition, **kw_args
        )
    else:
        raise TypeError("Unknown interp_type {0}, failing".format(interp_type))

    interpolated_arrays = []
    # We are explicitly expecting 2d arrays back, so if 3d, break it down.
    for arrind in range(len(list_of_arrays)):
        if len(dstacked_arrays.shape) == 3:
            interpolated_arrays += [dstacked_arrays[:, :, arrind]]
        else:
            interpolated_arrays += [dstacked_arrays]

    return interpolated_arrays
