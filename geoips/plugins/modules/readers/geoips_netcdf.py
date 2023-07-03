# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Read pre-processed GeoIPS-formatted NetCDF data."""

# Python Standard Libraries
import logging

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "geoips_netcdf"


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read preprocessed geoips netcdf output.

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
        * NOT YET IMPLEMENTED
        * Return before actually reading data if True
    chans : list of str, default=None
        * NOT YET IMPLEMENTED
        * List of desired channels (skip unneeded variables as needed).
        * Include all channels if None.
    area_def : pyresample.AreaDefinition, default=None
        * NOT YET IMPLEMENTED
        * Specify region to read
        * Read all data if None.
    self_register : str or bool, default=False
        * NOT YET IMPLEMENTED
        * register all data to the specified dataset id (as specified in the
          return dictionary keys).
        * Read multiple resolutions of data if False.

    Returns
    -------
    dict of xarray.Datasets
        * dictionary of xarray.Dataset objects with required Variables and
          Attributes.
        * Dictionary keys can be any descriptive dataset ids.

    See Also
    --------
    :ref:`xarray_standards`
        Additional information regarding required attributes and variables
        for GeoIPS-formatted xarray Datasets.
    """
    LOG.info("Reading files %s", fnames)

    from os.path import basename

    xarray_objs = {}
    for fname in fnames:
        xarray_objs[basename(fname)] = read_xarray_netcdf(fname)

    xarray_objs["METADATA"] = list(xarray_objs.values())[0][[]]

    return xarray_objs


def read_xarray_netcdf(ncdf_fname):
    """Read NetCDF file written out using the xarray python package."""
    import xarray
    from datetime import datetime

    try:
        xarray_obj = xarray.open_dataset(ncdf_fname)
    except IOError:
        raise IOError
    for attr in xarray_obj.attrs.keys():
        if "datetime" in attr:
            xarray_obj.attrs[attr] = datetime.strptime(xarray_obj.attrs[attr], "%c")
        if attr == "None":
            xarray_obj.attrs[attr] = None
        if attr == "True":
            xarray_obj.attrs[attr] = True
        if attr == "False":
            xarray_obj.attrs[attr] = False
    return xarray_obj
