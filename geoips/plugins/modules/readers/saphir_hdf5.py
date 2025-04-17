# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read SAPHIR hdf files."""

# Python Standard Libraries
from datetime import datetime
import logging

# Third-Party Libraries
import h5py
import numpy as np
import xarray as xr

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "saphir_hdf5"
source_names = ["saphir"]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read SAPHIR hdf data products.

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
    if len(fnames) > 1:
        raise ValueError(
            "Multiple files not supported with this reader. "
            "Please call with a single file."
        )
    fname = fnames[0]
    fileobj = h5py.File(str(fname), mode="r")

    lon_obj = fileobj["ScienceData"]["Longitude_Samples"]
    londata = float(lon_obj.attrs["scale_factor"]) * (lon_obj[...]) + float(
        lon_obj.attrs["add_offset"]
    )
    lat_obj = fileobj["ScienceData"]["Latitude_Samples"]
    # Offset is -40.0, scale_factor is 0.01
    latdata = float(lat_obj.attrs["scale_factor"]) * (lat_obj[...]) + float(
        lat_obj.attrs["add_offset"]
    )

    date_time_group = fileobj["ScienceData"]["Scan_FirstSampleAcqTime"][...]

    sstart_date_time_group = date_time_group[0, 0]
    # NOTE in Python 3, since h5py returns a binary string, splitting on ' ' failed,
    # but splitting on the default delimeter worked.
    # This appears to work on Python 2 as well.
    # sstart_date_group, sstart_time_group = sstart_date_time_group.split(' ')
    sstart_date_group, sstart_time_group = sstart_date_time_group.split()
    sstart_group_time = sstart_time_group[0:6]

    start_date_group = int(sstart_date_group)
    start_time_group = int(sstart_group_time)

    edtg = date_time_group.size - 1
    send_date_time_group = date_time_group[0, edtg]
    # NOTE in Python 3, since h5py returns a binary string, splitting on ' ' failed,
    # but splitting on the default delimeter worked.
    # This appears to work on Python 2 as well.
    send_date_group, send_time_group = send_date_time_group.split()
    send_group_time = send_time_group[0:6]

    end_date_group = int(send_date_group)
    end_time_group = int(send_group_time)

    incidence_angle = 0.01 * np.ma.masked_equal(
        fileobj["ScienceData"]["IncidenceAngle_Samples"], 32767
    )
    ch1qf = np.ma.masked_equal(
        np.squeeze((fileobj["ScienceData"]["QF_Samples_S1"][...])), 65535
    )
    ch2qf = np.ma.masked_equal(
        np.squeeze((fileobj["ScienceData"]["QF_Samples_S2"][...])), 65535
    )
    ch3qf = np.ma.masked_equal(
        np.squeeze((fileobj["ScienceData"]["QF_Samples_S3"][...])), 65535
    )
    ch4qf = np.ma.masked_equal(
        np.squeeze((fileobj["ScienceData"]["QF_Samples_S4"][...])), 65535
    )
    ch5qf = np.ma.masked_equal(
        np.squeeze((fileobj["ScienceData"]["QF_Samples_S5"][...])), 65535
    )
    ch6qf = np.ma.masked_equal(
        np.squeeze((fileobj["ScienceData"]["QF_Samples_S6"][...])), 65535
    )
    ch1 = np.ma.masked_equal(
        np.squeeze(0.01 * (fileobj["ScienceData"]["TB_Samples_S1"][...])), 65535
    )
    ch2 = np.ma.masked_equal(
        np.squeeze(0.01 * (fileobj["ScienceData"]["TB_Samples_S2"][...])), 65535
    )
    ch3 = np.ma.masked_equal(
        np.squeeze(0.01 * (fileobj["ScienceData"]["TB_Samples_S3"][...])), 65535
    )
    ch4 = np.ma.masked_equal(
        np.squeeze(0.01 * (fileobj["ScienceData"]["TB_Samples_S4"][...])), 65535
    )
    ch5 = np.ma.masked_equal(
        np.squeeze(0.01 * (fileobj["ScienceData"]["TB_Samples_S5"][...])), 65535
    )
    ch6 = np.ma.masked_equal(
        np.squeeze(0.01 * (fileobj["ScienceData"]["TB_Samples_S6"][...])), 65535
    )
    scanqf = np.ma.masked_equal(
        np.squeeze((fileobj["ScienceData"]["SAPHIR_QF_scan"][...])), 65535
    )

    LOG.info("Reading file %s", fname)

    # setup saphir xarray
    xarray_saphir = xr.Dataset()
    xarray_saphir["latitude"] = xr.DataArray(latdata)
    xarray_saphir["longitude"] = xr.DataArray(londata)
    xarray_saphir["IncidenceAngle"] = xr.DataArray(incidence_angle)
    xarray_saphir["scan_qf"] = xr.DataArray(scanqf)
    xarray_saphir["ch1qf_183.31_0.2"] = xr.DataArray(ch1qf)
    xarray_saphir["ch2qf_183.31_1.1"] = xr.DataArray(ch2qf)
    xarray_saphir["ch3qf_183.31_2.8"] = xr.DataArray(ch3qf)
    xarray_saphir["ch4qf_183.31_4.2"] = xr.DataArray(ch4qf)
    xarray_saphir["ch5qf_183.31_6.8"] = xr.DataArray(ch5qf)
    xarray_saphir["ch6qf_183.31_11.0"] = xr.DataArray(ch6qf)
    xarray_saphir["ch1_183.31_0.2"] = xr.DataArray(np.ma.masked_where(ch1qf > 64, ch1))
    xarray_saphir["ch2_183.31_1.1"] = xr.DataArray(np.ma.masked_where(ch2qf > 64, ch2))
    xarray_saphir["ch3_183.31_2.8"] = xr.DataArray(np.ma.masked_where(ch3qf > 64, ch3))
    xarray_saphir["ch4_183.31_4.2"] = xr.DataArray(np.ma.masked_where(ch4qf > 64, ch4))
    xarray_saphir["ch5_183.31_6.8"] = xr.DataArray(np.ma.masked_where(ch5qf > 64, ch5))
    xarray_saphir["ch6_183.31_11.0"] = xr.DataArray(np.ma.masked_where(ch6qf > 64, ch6))
    # xarray_saphir['time']=xr.DataArray(pd.DataFrame(time_scan).astype(int).apply(pd.to_datetime,format='%Y%j%H%M'))

    # add attributes to xarray
    xarray_saphir.attrs["start_datetime"] = datetime.strptime(
        "%08d%06d" % (start_date_group, start_time_group), "%Y%m%d%H%M%S"
    )
    xarray_saphir.attrs["end_datetime"] = datetime.strptime(
        "%08d%06d" % (end_date_group, end_time_group), "%Y%m%d%H%M%S"
    )
    xarray_saphir.attrs["source_name"] = "saphir"
    xarray_saphir.attrs["platform_name"] = "meghatropiques"
    xarray_saphir.attrs["data_provider"] = "GSFC"
    xarray_saphir.attrs["sample_distance_km"] = 10
    xarray_saphir.attrs["interpolation_radius_of_influence"] = 20000

    return {"SAPHIR": xarray_saphir, "METADATA": xarray_saphir[[]]}
