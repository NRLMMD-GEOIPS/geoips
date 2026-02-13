# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read NASA GPM GMI hdf5 data files.

Read a grannual NASA GPM GMI TBs in h5 format (each grannual file is about
5 minutes GPM GMI data)

Output variables in xarray object for geoips processing system

V0:   August 4, 2020

Dataset information::

    variables in original TBs structure format
    tb_info = { 'S1': {  'tb10v': 0,
                         'tb10h': 1,
                         'tb19v': 2,
                         'tb19h': 3,
                         'tb23v': 4,
                         'tb37v': 5,
                         'tb37h': 6,
                         'tb89v': 7,
                         'tb89h': 8,},
                 'S2': { 'tb166v': 0,
                         'tb166h': 1,
                         'tb183_3v': 2,
                         'tb183_7v': 3}
             }
"""

# Python Standard Libraries
import logging
from os.path import basename

# Third-Party Libraries
import h5py
import matplotlib
import numpy as np
import pandas as pd
import xarray as xr

matplotlib.use("agg")
LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "gmi_hdf5"
source_names = ["gmi"]


def read_gmi_file(fname, xarray_gmi):
    """Read a single GMI file fname."""
    fileobj = h5py.File(fname, mode="r")
    # get the variables ( tbt/lon(nscan,npix), tb(nscan,npix,nChan),....., time(ns))

    lon = fileobj["S1"]["Longitude"][()]
    lat = fileobj["S1"]["Latitude"][()]
    tb = fileobj["S1"]["Tb"][()]
    tb_hi = fileobj["S2"]["Tb"][()]  # for 166 and 183-7 GHz

    # time info for each scan
    yy = fileobj["S1"]["ScanTime"]["Year"][()]
    mo = fileobj["S1"]["ScanTime"]["Month"][()]
    dd = fileobj["S1"]["ScanTime"]["DayOfMonth"][()]
    hh = fileobj["S1"]["ScanTime"]["Hour"][()]
    mm = fileobj["S1"]["ScanTime"]["Minute"][()]
    ss = fileobj["S1"]["ScanTime"]["Second"][()]

    # setup time in datetime64 format required by geoips

    nscan = lat.shape[0]
    npix = lat.shape[1]  # 221 pixels per scan
    time_scan = np.zeros((nscan, npix))

    for i in range(nscan):
        time_scan[i:] = "%04d%02d%02d%02d%02d%02d" % (
            yy[i],
            mo[i],
            dd[i],
            hh[i],
            mm[i],
            ss[i],
        )

    # assignment of TB at each channel
    V10 = tb[:, :, 0]
    H10 = tb[:, :, 1]
    V19 = tb[:, :, 2]
    H19 = tb[:, :, 3]
    V23 = tb[:, :, 4]
    V37 = tb[:, :, 5]
    H37 = tb[:, :, 6]
    V89 = tb[:, :, 7]
    H89 = tb[:, :, 8]

    V166 = tb_hi[:, :, 0]
    H166 = tb_hi[:, :, 1]
    V183_3 = tb_hi[:, :, 2]
    V183_7 = tb_hi[:, :, 3]

    # close the h5 object
    fileobj.close()

    #          ------  setup xarray variables   ------

    # namelist_gmi  = ['latitude', 'longitude', 'V10', 'H10', 'V19','H19','V23', 'V37',
    #                  'H37', 'V89' ,'H89', 'V166', 'H166', 'V183-3','V183-7', 'time']

    final_xarray = xr.Dataset()
    if "latitude" not in xarray_gmi.variables.keys():
        # setup GMI xarray
        final_xarray["latitude"] = xr.DataArray(lat)
        final_xarray["longitude"] = xr.DataArray(lon)
        final_xarray["V10"] = xr.DataArray(V10)
        final_xarray["H10"] = xr.DataArray(H10)
        final_xarray["V19"] = xr.DataArray(V19)
        final_xarray["H19"] = xr.DataArray(H19)
        final_xarray["V23"] = xr.DataArray(V23)
        final_xarray["V37"] = xr.DataArray(V37)
        final_xarray["H37"] = xr.DataArray(H37)
        final_xarray["V89"] = xr.DataArray(V89)
        final_xarray["H89"] = xr.DataArray(H89)
        final_xarray["V166"] = xr.DataArray(V166)
        final_xarray["H166"] = xr.DataArray(H166)
        final_xarray["V183-3"] = xr.DataArray(V183_3)
        final_xarray["V183-7"] = xr.DataArray(V183_7)
        final_xarray["time"] = xr.DataArray(
            pd.DataFrame(time_scan)
            .astype(int)
            .apply(pd.to_datetime, format="%Y%m%d%H%M%S")
        )
    else:
        final_xarray["latitude"] = xr.DataArray(
            np.vstack([xarray_gmi["latitude"].to_masked_array(), lat])
        )
        final_xarray["longitude"] = xr.DataArray(
            np.vstack([xarray_gmi["longitude"].to_masked_array(), lon])
        )
        final_xarray["V10"] = xr.DataArray(
            np.vstack([xarray_gmi["V10"].to_masked_array(), V10])
        )
        final_xarray["H10"] = xr.DataArray(
            np.vstack([xarray_gmi["H10"].to_masked_array(), H10])
        )
        final_xarray["V19"] = xr.DataArray(
            np.vstack([xarray_gmi["V19"].to_masked_array(), V19])
        )
        final_xarray["H19"] = xr.DataArray(
            np.vstack([xarray_gmi["H19"].to_masked_array(), H19])
        )
        final_xarray["V23"] = xr.DataArray(
            np.vstack([xarray_gmi["V23"].to_masked_array(), V23])
        )
        final_xarray["V37"] = xr.DataArray(
            np.vstack([xarray_gmi["V37"].to_masked_array(), V37])
        )
        final_xarray["H37"] = xr.DataArray(
            np.vstack([xarray_gmi["H37"].to_masked_array(), H37])
        )
        final_xarray["V89"] = xr.DataArray(
            np.vstack([xarray_gmi["V89"].to_masked_array(), V89])
        )
        final_xarray["H89"] = xr.DataArray(
            np.vstack([xarray_gmi["H89"].to_masked_array(), H89])
        )
        final_xarray["V166"] = xr.DataArray(
            np.vstack([xarray_gmi["V166"].to_masked_array(), V166])
        )
        final_xarray["H166"] = xr.DataArray(
            np.vstack([xarray_gmi["H166"].to_masked_array(), H166])
        )
        final_xarray["V183-3"] = xr.DataArray(
            np.vstack([xarray_gmi["V183-3"].to_masked_array(), V183_3])
        )
        final_xarray["V183-7"] = xr.DataArray(
            np.vstack([xarray_gmi["V183-7"].to_masked_array(), V183_7])
        )
        new_time = xr.DataArray(
            pd.DataFrame(time_scan)
            .astype(int)
            .apply(pd.to_datetime, format="%Y%m%d%H%M%S")
        )
        final_xarray["time"] = xr.DataArray(
            np.vstack(
                [
                    xarray_gmi["time"].to_masked_array(),
                    new_time.to_masked_array(),
                ]
            )
        )
    return final_xarray


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read GMI hdf5 data products.

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
    # fname='data_gmi/20200518.203639.gpm.gmi.gpm_pps.x.gmi.TB2016.x.TB2016_1b_v05a.h5'

    LOG.info("Reading files %s", fnames)

    xarray_gmi = xr.Dataset()
    source_file_names = []
    for fname in fnames:
        source_file_names += [basename(fname)]
        xarray_gmi = read_gmi_file(fname, xarray_gmi)

    # setup attributors
    from geoips.xarray_utils.time import (
        get_max_from_xarray_time,
        get_min_from_xarray_time,
    )

    xarray_gmi.attrs["source_file_names"] = sorted(source_file_names)
    xarray_gmi.attrs["start_datetime"] = get_min_from_xarray_time(xarray_gmi, "time")
    xarray_gmi.attrs["end_datetime"] = get_max_from_xarray_time(xarray_gmi, "time")
    xarray_gmi.attrs["source_name"] = "gmi"
    xarray_gmi.attrs["platform_name"] = "GPM"
    xarray_gmi.attrs["data_provider"] = "NASA"
    xarray_gmi.attrs["granule_minutes"] = 5

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    xarray_gmi.attrs["sample_distance_km"] = 2
    xarray_gmi.attrs["interpolation_radius_of_influence"] = 12500

    return {"GMI": xarray_gmi, "METADATA": xarray_gmi[[]]}
