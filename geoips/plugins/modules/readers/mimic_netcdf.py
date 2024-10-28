# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""MIMIC TPW NetCDF reader."""

# Python Standard Libraries
from datetime import datetime
import logging
import os

# Third-Party Libraries
import numpy
import xarray

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "mimic_netcdf"
source_names = ["mimic"]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read TPW MIMIC data from a list of filenames.

    Dataset information::

        <xarray.Dataset>
        Dimensions:             (lat: 721, lon: 1440)
        Dimensions without coordinates: lat, lon
        Data variables:
            lonArr              (lon) float32 ...
            latArr              (lat) float32 ...
            tpwGrid             (lat, lon) float32 ...
            tpwGridPrior        (lat, lon) float32 ...
            tpwGridSubseq       (lat, lon) float32 ...
            timeAwayGridPrior   (lat, lon) timedelta64[ns] ...
            timeAwayGridSubseq  (lat, lon) timedelta64[ns] ...
            footGridPrior       (lat, lon) float32 ...
            footGridSubseq      (lat, lon) float32 ...
            satGridPrior        (lat, lon) uint8 ...
            satGridSubseq       (lat, lon) uint8 ...

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

    xobj = xarray.open_dataset(fname)

    [date, time, ext] = os.path.basename(fname).split(".")
    dt = datetime.strptime(date + time, "comp%Y%m%d%H%M%S")
    xobj.attrs["data_provider"] = "cimss"

    xobj.attrs["start_datetime"] = dt
    xobj.attrs["end_datetime"] = dt
    xobj.attrs["platform_name"] = "tpw"
    xobj.attrs["source_file_datetimes"] = [dt]
    xobj.attrs["source_name"] = "mimic"
    # ~2km for data_fine
    xobj.attrs["sample_distance_km"] = 110.0 * abs(
        xobj.variables["latArr"][1].data - xobj.variables["latArr"][0].data
    )
    xobj.attrs["interpolation_radius_of_influence"] = (
        xobj.attrs["sample_distance_km"] * 1000.0 * 1.5
    )
    if metadata_only is True:
        return {"METADATA": xobj}

    LOG.info("Obtaining lat/lon from xarray")
    # Meshgrid requires Latitude and Longitude at once, so don't put in loop
    lat = xobj.variables["latArr"][...]
    lon = xobj.variables["lonArr"][...]

    LOG.info("Calculating full lat/lon grid")
    lon_final, lat_final = numpy.meshgrid(lon, lat)

    LOG.info("Adding lat grid to xarray")
    xobj["latitude"] = xarray.DataArray(numpy.ma.array(lat_final), dims=("lat", "lon"))
    LOG.info("Adding lon grid to xarray")
    xobj["longitude"] = xarray.DataArray(numpy.ma.array(lon_final), dims=("lat", "lon"))
    xobj = xobj.drop("latArr")
    xobj = xobj.drop("lonArr")
    xobj["tpw"] = xobj["tpwGrid"]

    return {"MIMIC": xobj, "METADATA": xobj[[]]}
