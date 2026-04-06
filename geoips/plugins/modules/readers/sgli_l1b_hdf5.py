# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Reader to read GCOM-C1 SGLI files.

(NRL-Monterey, Oct. 2025)
"""

# Python Standard Libraries
import logging
from os.path import basename
from datetime import datetime

# Installed libraries
import xarray as xr
import numpy as np
from scipy.ndimage import zoom
from h5py import File as h5File

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "sgli_l1b_hdf5"

"""
Channel Info:
channel name, center wavelength (um), resolution (km)
SW01, 1.05, 1
SW02, 1.38, 1
SW03, 1.63, .25
SW04, 2.21, 1
TI01, 10.8, .5
TI02, 12, .5

VN01, .38, .25
VN02, .412, .25
VN03, .443, .25
VN04, .49, .25
VN05, .53, .25
VN06, .565, .25
VN07, .6735, .25
VN08, .6735, .25
VN09, .763, 1
VN10, .8685, .25
VN11, .8685, .25

P01, .6735, 1
P02, .8685, 1
(Pol-chans are seperated by stokes polarization: I,Q,U)
"""

ir_chans = {"Lt_SW01", "Lt_SW02", "Lt_SW03", "Lt_SW04", "Lt_TI01", "Lt_TI02"}
vis_chans = {
    "Lt_VN01",
    "Lt_VN02",
    "Lt_VN03",
    "Lt_VN04",
    "Lt_VN05",
    "Lt_VN06",
    "Lt_VN07",
    "Lt_VN08",
    "Lt_VN09",
    "Lt_VN10",
    "Lt_VN11",
}
pol_chans = {"Lt_PI01", "Lt_PI02", "Lt_PQ01", "Lt_PQ02", "Lt_PU01", "Lt_PU02"}

res_mapping = {1000: "LOW", 500: "MED", 250: "HIGH"}


def commit_to_dict(data_dict, key, tmp_xry):
    """Commit data as a list item to a dictionary."""
    if key in data_dict.keys():
        data_dict[key].append(tmp_xry)
    else:
        data_dict[key] = [tmp_xry]

    return data_dict


def rad_to_temp(rad, center_wl):
    """Convert Radiance to Temp."""
    c1 = 1.1911042e8
    c2 = 1.4387752e4
    temp = c2 / (center_wl * np.log(c1 / ((center_wl**5) * rad + 1)))

    return temp


def read_irs(infile, data_chans=ir_chans):
    """Read the infrared scanner (SWIR & TIR) data."""
    # three possible resolutions
    # HIGH (250m) MED (500m) LOW (1km)
    xrt = xr.Dataset(attrs={"res_types": []})
    with h5File(infile) as irs_h5:
        # load all respective channels
        for k in data_chans:
            raw_chan = irs_h5["Image_data"][k]
            # mask data, top two bits are masked
            chan_name = k.split("_")[1]
            raw_img = raw_chan[...] & 0x3FFF
            raw_ma = np.where(raw_img == 16383, np.nan, raw_img)
            # create radiance, reflectance
            toa_rad = (raw_chan.attrs["Slope"][...] * raw_ma) + raw_chan.attrs[
                "Offset"
            ][...]
            ref_flag = False
            if "Slope_reflectance" in raw_chan.attrs.keys():
                toa_ref = (
                    raw_chan.attrs["Slope_reflectance"][...] * raw_ma
                ) + raw_chan.attrs["Offset_reflectance"][...]
                ref_flag = True

            res_type = res_mapping[int(raw_chan.attrs["Spatial_resolution"][0])]
            if res_type not in xrt.attrs["res_types"]:
                # commit geo values
                xrt.attrs["res_types"].append(res_type)
                # load geo channels
                lat = irs_h5["Geometry_data"]["Latitude"][...]
                lon = irs_h5["Geometry_data"]["Longitude"][...]
                sol_azi_angle = irs_h5["Geometry_data"]["Solar_azimuth"][...] * 0.01
                sol_zen_angle = irs_h5["Geometry_data"]["Solar_zenith"][...] * 0.01
                sat_azi = irs_h5["Geometry_data"]["Sensor_azimuth"][...] * 0.01
                sat_zen = irs_h5["Geometry_data"]["Sensor_zenith"][...] * 0.01
                # zoom if needed
                if lat.shape != raw_img.shape:
                    coef = (
                        raw_img.shape[0] / lat.shape[0],
                        raw_img.shape[1] / lat.shape[1],
                    )
                    lat = zoom(lat, coef)
                    lon = zoom(lon, coef)
                    sat_azi = zoom(sat_azi, coef)
                    sat_zen = zoom(sat_zen, coef)
                    sol_zen_angle = zoom(sol_zen_angle, coef)
                    sol_azi_angle = zoom(sol_azi_angle, coef)

                xrt[res_type.lower() + "lat"] = xr.DataArray(
                    lat.ravel(), dims=(res_type.lower() + "_dim0")
                )
                xrt[res_type.lower() + "lon"] = xr.DataArray(
                    lon.ravel(), dims=(res_type.lower() + "_dim0")
                )
                xrt[res_type.lower() + "sat_zen"] = xr.DataArray(
                    sat_zen.ravel(), dims=(res_type.lower() + "_dim0")
                )
                xrt[res_type.lower() + "sat_azi"] = xr.DataArray(
                    sat_azi.ravel(), dims=(res_type.lower() + "_dim0")
                )
                xrt[res_type.lower() + "sol_zen"] = xr.DataArray(
                    sol_zen_angle.ravel(), dims=(res_type.lower() + "_dim0")
                )
                xrt[res_type.lower() + "sol_azi"] = xr.DataArray(
                    sol_azi_angle.ravel(), dims=(res_type.lower() + "_dim0")
                )
            # commit data to xarray
            xrt[chan_name + "Rad"] = xr.DataArray(
                toa_rad.ravel(), dims=(res_type.lower() + "_dim0",)
            )
            temp = rad_to_temp(toa_rad, raw_chan.attrs["Center_wavelength"][...] / 1000)
            xrt[chan_name + "BT"] = xr.DataArray(
                temp.ravel(), dims=(res_type.lower() + "_dim0",)
            )

            if ref_flag:
                xrt[chan_name + "Ref"] = xr.DataArray(
                    toa_ref.ravel(),
                    dims=(res_type.lower() + "_dim0",),
                )

    return xrt


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
):
    """Read GFS GRIB data.

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
        * Return before actually reading data if True
    chans : list of str, default=None
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
        * Conforms to geoips xarray standards, see more in geoips documentation.
    """
    base_fnames = list(map(basename, fnames))
    fnames = sorted(fnames)

    # approximate for metadata only
    dtime_start = datetime.strptime(base_fnames[0].split("_")[1][:10], "%Y%m%d%H%M")
    dtime_end = datetime.strptime(base_fnames[-1].split("_")[1][:10], "%Y%m%d%H%M")

    # if mixed res assume low
    res_types = set(f.split("_")[3][-1] for f in base_fnames)
    res_dict = {"K": 1, "L": 1, "Q": 0.25}

    if len(list(res_types)) > 1:
        res = 1
    else:
        res = res_dict[res_types.pop()]

    tmp_xr = xr.Dataset(
        attrs={
            "source_file_name": base_fnames,
            "start_datetime": dtime_start,
            "end_datetime": dtime_end,
            "source_name": "sgli",
            "platform_name": "GCOM-C1",
            "data_provider": "JAXA",
            "sample_distance_km": res,
            "interpolation_radius_of_influence": 3000,
        }
    )
    if metadata_only:
        tmp_dict = {"METADATA": tmp_xr}
        return tmp_dict

    vnr_chans = vis_chans
    irs_chans = ir_chans

    if chans is not None:
        req_chans = set("Lt_" + i[:4] for i in chans)
        irs_chans = req_chans & ir_chans
        vnr_chans = req_chans & vis_chans
        polo_chans = req_chans & pol_chans
        if (
            len(list(irs_chans)) == 0
            and len(list(vnr_chans)) == 0
            and len(list(polo_chans)) == 0
        ):
            raise ValueError(
                "No channels found for SGLI, check requestd channels: {}".format(
                    req_chans
                )
            )
            # read data, seperated by resolution
    data_xr_dict = {}
    res_list = []
    for f in fnames:
        f_basename = basename(f)
        if "IRS" in f_basename:
            data_xarray = read_irs(f, data_chans=irs_chans)
            data_xr_dict = commit_to_dict(data_xr_dict, "IRS", data_xarray)
        elif "VNR" in f_basename:
            data_xarray = read_irs(f, data_chans=vnr_chans)
            data_xr_dict = commit_to_dict(data_xr_dict, "VNR", data_xarray)
        elif "POL" in f_basename:
            data_xarray = read_irs(f, data_chans=polo_chans)
            data_xr_dict = commit_to_dict(data_xr_dict, "POL", data_xarray)
        else:
            LOG.warning("No data type readable in file: {}".format(f_basename))
            raise ValueError("No matching file key for IRS, VNR, or POL in filename.")

        res_list.extend(data_xarray.attrs["res_types"])

    if len(list(data_xr_dict.keys())) == 1:
        single_key = list(data_xr_dict.keys())[0]
        full_xarray = xr.concat(data_xr_dict[single_key], dim="dimN")
    else:
        # multi-file merge/concat
        for k in data_xr_dict.keys():
            data_xr_dict[k] = xr.concat(data_xr_dict[k], dim="dimN")
        full_xarray = xr.merge(data_xr_dict.values())

    final_data = {}
    # Reorder science data for a dict based upon resolution
    res_avail = set(res_list)
    for r in set(res_list):

        res_pop = res_avail - {r}
        res_pop = [i.lower() + "_dim0" for i in res_pop]
        final_data[r] = full_xarray.drop_dims(res_pop).rename(
            {
                r.lower() + "lat": "latitude",
                r.lower() + "lon": "longitude",
                r.lower() + "_dim0": "dim_0",
                r.lower() + "sat_zen": "satellite_zenith_angle",
                r.lower() + "sat_azi": "satellite_azimuth_angle",
                r.lower() + "sol_zen": "solar_zenith_angle",
                r.lower() + "sol_azi": "solar_azimuth_angle",
            }
        )
        final_data[r].attrs["res_types"] = r
        final_data[r].attrs |= tmp_xr.attrs

    final_data |= {"METADATA": tmp_xr}

    return final_data
