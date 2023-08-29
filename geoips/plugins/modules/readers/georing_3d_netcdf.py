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

"""GEOring_3D NetCDF reader."""

# Python Standard Libraries
import logging
import os
from datetime import datetime

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "georing_3d_netcdf"


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read GEOring_3d netcdf data from a list of filenames.

    Dataset information::

        <xarray.Dataset>
        Dimensions:             (alt: 81, lat: 7000, lon: 18000)
        Dimensions without coordinates: alt, lat, lon
        Data variables:
            altitude            (alt) float32 ...
            cloud3d             (cloud3d) ushort ...
            latitude            (lat) float32 ...
            longitude           (lon) float32 ...

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
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
    fname = fnames[0]

    import xarray

    xobj = xarray.open_dataset(fname)

    date_time = os.path.basename(fname).split("_")[-1][:-5]
    date = date_time[:8]
    hour = date_time[8:10]
    minute = date_time[10:]
    dt = datetime.strptime(date + hour + minute, "%Y%m%d%H%M")
    xobj.attrs["data_provider"] = "cira"

    xobj.attrs["start_datetime"] = dt
    xobj.attrs["end_datetime"] = dt
    xobj.attrs["platform_name"] = "GEOring_3D"
    xobj.attrs["source_file_datetimes"] = [dt]
    xobj.attrs["source_name"] = "georing_3d"
    if metadata_only is True:
        return {"METADATA": xobj}
    return {"GEORING": xobj, "METADATA": xobj[[]]}
