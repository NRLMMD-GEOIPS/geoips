# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""VIIRS SDR Satpy reader.

This VIIRS reader is designed for reading the NPP/JPSS SDR HDF5 files.
The input files are produced by CSPP Polar (CSPP RDR pipeline),
and the read by hdf5.

V2.0.0:  NRL-Monterey, 082025

"""

# Python Standard Libraries
import logging
import os
import re
from itertools import chain
from datetime import datetime, timedelta

# Third-Party Libraries
import h5py
import numpy as np
import xarray as xr
from scipy.interpolate import NearestNDInterpolator

# geoips libraries
from geoips.data_manipulations.corrections import apply_gamma

LOG = logging.getLogger(__name__)

try:
    from lunarref.lib.liblunarref import lunarref

    lunarref_lib = True
except ImportError:
    lunarref_lib = False
    LOG.warning("Failed lunarref import, if needed, install it.")


interface = "readers"
family = "standard"
name = "viirs_sdr_hdf5"
source_names = ["viirs"]


VARLIST = {
    "DNB": ["DNB"],
    "IMG": ["I04", "I05"],
    "IMG-Vis": ["I01", "I02", "I03"],
    "MOD": ["M07", "M08", "M10", "M11", "M12", "M13", "M14", "M15", "M16"],
    "MOD-Vis": ["M01", "M02", "M03", "M04", "M05", "M06", "M09"],
}


def bowtie_correction(band, lat, lon):
    """Correct input data for the instrument bowtie effect.

    Correction derived from: Remote Sens. 2016, 8, 79.
    """
    # Unfold
    ord_lat = np.sort(lat, axis=0)
    unfold_idx = np.argsort(lat, axis=0)

    rad_fold = np.take_along_axis(band, unfold_idx, axis=0)
    sort_lon = np.take_along_axis(lon, unfold_idx, axis=0)

    if np.all(np.isnan(rad_fold)):
        LOG.debug("All nan band, no bowtie correction")
        return rad_fold, ord_lat, sort_lon
    if np.all(np.isnan(rad_fold)):
        LOG.debug("All NaNs, no bowtie correction")
        return rad_fold, ord_lat, sort_lon

    res_band = rad_fold.copy()
    # mask and indicies of bad data
    rad_nan_flag = np.isnan(rad_fold)
    nan_mask = np.where(~rad_nan_flag)

    interp = NearestNDInterpolator(np.transpose(nan_mask), rad_fold[nan_mask])
    interp_nans = interp(*np.indices(rad_fold.shape)[:, rad_nan_flag], **{"workers": 4})
    res_band[rad_nan_flag] = interp_nans

    return res_band, ord_lat.astype(np.float64), sort_lon.astype(np.float64)


def get_time(hfile):
    """Get datetime from the metadata."""
    with h5py.File(hfile) as h5data:
        base_key = list(h5data["Data_Products"].keys())[0]
        main_key = [
            i for i in h5data["Data_Products"][base_key].keys() if "Gran_0" in i
        ][0]

        start_time = h5data["Data_Products"][base_key][main_key].attrs[
            "N_Beginning_Time_IET"
        ][0][0]
        end_time = h5data["Data_Products"][base_key][main_key].attrs[
            "N_Ending_Time_IET"
        ][0][0]

    stime = timedelta(microseconds=int(start_time)) + datetime.strptime(
        "1958-01-01", "%Y-%m-%d"
    )
    etime = timedelta(microseconds=int(end_time)) + datetime.strptime(
        "1958-01-01", "%Y-%m-%d"
    )

    return stime, etime


def get_plat(hfile):
    """Get platform from the metadata."""
    with h5py.File(hfile) as h5data:
        plat = h5data.attrs["Platform_Short_Name"][0][0].astype("str")
    platform_dict = {
        "NPP": "Suomi-NPP",
        "JPSS-1": "NOAA-20",
        "J01": "NOAA-20",
        "JPSS-2": "NOAA-21",
        "J02": "NOAA-21",
    }
    plat_name = platform_dict[plat]
    return plat_name


def get_sci_data(hfile, sv_key):
    """Get science data from file."""
    with h5py.File(hfile) as h5data:
        band_key = list(h5data["All_Data"].keys())[0]
        # get BT and Radiance
        bt_flag = False
        ref_flag = False

        if "BrightnessTemperature" in h5data["All_Data"][band_key].keys():
            bt_raw = h5data["All_Data"][band_key]["BrightnessTemperature"][...]
            if "BrightnessTemperatureFactors" in h5data["All_Data"][band_key].keys():
                bt_fac = h5data["All_Data"][band_key]["BrightnessTemperatureFactors"][
                    ...
                ]
                bt_cal = bt_raw * bt_fac[0] + bt_fac[1]
            else:
                bt_cal = bt_raw
            bt_flag = True
        elif "Reflectance" in h5data["All_Data"][band_key].keys():

            bt_raw = h5data["All_Data"][band_key]["Reflectance"][...]
            if "ReflectanceFactors" in h5data["All_Data"][band_key].keys():
                bt_fac = h5data["All_Data"][band_key]["ReflectanceFactors"][...]
                bt_cal = bt_raw * bt_fac[0] + bt_fac[1]
            else:
                bt_cal = bt_raw
            bt_cal = apply_gamma(bt_cal, 1.65) * 100
            ref_flag = True

        rad_raw = h5data["All_Data"][band_key]["Radiance"][...]
        if "RadianceFactors" in h5data["All_Data"][band_key].keys():
            rad_fac = h5data["All_Data"][band_key]["RadianceFactors"][...]
            LOG.info("Applying calibration values to radiance data.")
            rad_cal = rad_raw * rad_fac[0] + rad_fac[1]
        else:
            rad_cal = rad_raw
        # flag data
        flag_key = [k for k in h5data["All_Data"][band_key].keys() if "QF1_" in k][0]
        qflag = h5data["All_Data"][band_key][flag_key][...]

    mask = np.where(qflag > 1, True, False)
    if not np.isdtype(rad_cal.dtype, np.float32):
        rad_cal = rad_cal.astype(np.float32)
    # seems like DNB quality flags are bad??
    # leads to NaN granules
    rad_cal[mask] = np.nan

    if bt_flag or ref_flag:
        if not np.isdtype(bt_cal.dtype, np.float32):
            bt_cal = bt_cal.astype(np.float32)
        bt_cal[mask] = np.nan

    sci_xr = xr.Dataset()
    if bt_flag:
        sci_xr[sv_key + "BT"] = xr.DataArray(bt_cal, dims=("dim_0", "dim_1"))
    if ref_flag:
        sci_xr[sv_key + "Ref"] = xr.DataArray(bt_cal, dims=("dim_0", "dim_1"))

    sci_xr[sv_key + "Rad"] = xr.DataArray(rad_cal, dims=("dim_0", "dim_1"))
    sci_xr["Quality_Flag"] = xr.DataArray(qflag, dims=("dim_0", "dim_1"))

    return sci_xr


def get_geo_data(bname, band_type, flist):
    """Get geolocation data based upon the band provided.

    Input
    -----
    bname: basename of input file
    band_type: band type (DNB, SVI, SVM)
    flist: file list

    Output:
    -------
    dict: output parameters
    latitude:
    longitude:
    """
    BAD_VAL = -998.0
    geo_dict = {"SVI": "GITCO", "SVD": "GDNBO", "SVM": "GMTCO"}
    geo_key = geo_dict[band_type]

    # get proper geo file and at the right time
    set_start = re.search(r"_t\d{7}_", bname)[0]
    flist = [f for f in flist if set_start in f]

    base_flist = list(map(os.path.basename, flist))
    geo_list = [flist[i] for i, j in enumerate(base_flist) if geo_key in j]
    if len(geo_list) == 0:
        # try to find ellispoid files
        LOG.warning("No GEO terrain corrected files found, reverting to ellispoid.")
        geo_dict = {"SVI": "GIMGO", "SVM": "GMODO"}
        # catch error for DNB files
        if band_type not in geo_dict.keys():
            raise LookupError("No VIIRS geo-file found, check input filelist.")
        geo_key = geo_dict[band_type]
        geo_list = [flist[i] for i, j in enumerate(base_flist) if geo_key in j]

    if len(geo_list) == 0:
        raise LookupError("No VIIRS GEO file found, check input filelist.")
    geo_file = geo_list[0]
    LOG.info("Reading geo file {}".format(os.path.basename(geo_file)))
    with h5py.File(geo_file) as h5geo:
        geo_key = list(h5geo["All_Data"].keys())[0]
        latitude = h5geo["All_Data"][geo_key]["Latitude"][...]
        longitude = h5geo["All_Data"][geo_key]["Longitude"][...]
        mask = h5geo["All_Data"][geo_key]["QF2_VIIRSSDRGEO"][...]

        sol_zea = h5geo["All_Data"][geo_key]["SolarZenithAngle"][...]
        sol_azi = h5geo["All_Data"][geo_key]["SolarAzimuthAngle"][...]

        sat_zea = h5geo["All_Data"][geo_key]["SatelliteZenithAngle"][...]
        sat_azi = h5geo["All_Data"][geo_key]["SatelliteAzimuthAngle"][...]
        extra_params = {}
        if "DNB" in geo_key:
            latitude = (
                h5geo["All_Data"][geo_key]["Latitude_TC"]
                if "latitude_tc" in h5geo["All_Data"][geo_key].keys()
                else h5geo["All_Data"][geo_key]["Latitude"][...]
            )
            longitude = (
                h5geo["All_Data"][geo_key]["Longitude_TC"]
                if "longitude_tc" in h5geo["All_Data"][geo_key].keys()
                else h5geo["All_Data"][geo_key]["Longitude"][...]
            )

            lza = h5geo["All_Data"][geo_key]["LunarZenithAngle"][...]
            laa = h5geo["All_Data"][geo_key]["LunarAzimuthAngle"][...]
            moon_frac = h5geo["All_Data"][geo_key]["MoonIllumFraction"][...]
            moon_phase_ang = h5geo["All_Data"][geo_key]["MoonPhaseAngle"][...]

            # moon_frac = 0.5 * (1 + np.cos(moon_phase_ang))
            lza = np.where(lza < BAD_VAL, np.nan, lza)
            laa = np.where(laa < BAD_VAL, np.nan, laa)

            extra_params = {
                "lza": lza,
                "laa": laa,
                "moon_fraction": moon_frac,
                "moon_phase_angle": moon_phase_ang,
            }

    # mask and flagging
    flag = np.where(mask > 0, True, False)
    latitude[flag] = np.nan
    longitude[flag] = np.nan

    if np.any(latitude < -90) or np.any(latitude > 90):
        lat_flag = np.where(latitude < -90, True, False)
        lat_flag = np.logical_or(np.where(latitude > 90, True, False), lat_flag)
        latitude[lat_flag] = np.nan

    comb_mask = (
        (sol_zea < BAD_VAL)
        | (sol_azi < BAD_VAL)
        | (sat_zea < BAD_VAL)
        | (sat_azi < BAD_VAL)
        | flag
    )
    sol_zea = np.where(sol_zea < BAD_VAL, np.nan, sol_zea)
    sol_azi = np.where(sol_azi < BAD_VAL, np.nan, sol_azi)

    sat_zea = np.where(sat_zea < BAD_VAL, np.nan, sat_zea)
    sat_azi = np.where(sat_azi < BAD_VAL, np.nan, sat_azi)
    # create xarray dataset
    geo_xr = xr.Dataset()
    geo_xr["latitude"] = xr.DataArray(latitude, dims=("dim_0", "dim_1"))
    geo_xr["longitude"] = xr.DataArray(longitude, dims=("dim_0", "dim_1"))
    geo_xr["solar_zenith_angle"] = xr.DataArray(sol_zea, dims=("dim_0", "dim_1"))
    geo_xr["solar_azimuth_angle"] = xr.DataArray(sol_azi, dims=("dim_0", "dim_1"))
    geo_xr["satellite_zenith_angle"] = xr.DataArray(sat_zea, dims=("dim_0", "dim_1"))
    geo_xr["satellite_azimuth_angle"] = xr.DataArray(sat_azi, dims=("dim_0", "dim_1"))
    geo_xr["geo_mask"] = xr.DataArray(comb_mask, dims=("dim_0", "dim_1"))

    if len(extra_params.keys()) > 0:
        geo_xr["lunar_zenith_angle"] = xr.DataArray(
            extra_params["lza"], dims=("dim_0", "dim_1")
        )
        geo_xr["lunar_azimuth_angle"] = xr.DataArray(
            extra_params["laa"], dims=("dim_0", "dim_1")
        )
        geo_xr["moon_frac"] = xr.DataArray(
            np.full(sol_zea.shape, extra_params["moon_fraction"] / 100.0),
            dims=("dim_0", "dim_1"),
        )

        geo_xr["moon_phase"] = xr.DataArray(
            np.full(sol_zea.shape, extra_params["moon_phase_angle"]),
            dims=("dim_0", "dim_1"),
        )

    return geo_xr


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    bowtie=True,
):
    """Read VIIRS SDR hdf5 data products.

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
    bowtie: bool, default=True
        * Preform bowtie correction for edge of scan.

    Returns
    -------
    dict of xarray.Datasets
        * dictionary of xarray.Dataset objects with required Variables and
          Attributes.
        * Dictionary keys can be any descriptive dataset ids.
        * Conforms to geoips xarray standards, see more in geoips documentation.
    """
    base_fnames = list(map(os.path.basename, fnames))
    sorted_fnames = sorted(fnames)

    dt_start = get_time(sorted_fnames[0])[0]
    dt_end = get_time(sorted_fnames[-1])[-1]
    plat_name = get_plat(sorted_fnames[0])
    meta_attrs = {
        "source_file_name": base_fnames,
        "start_datetime": dt_start,
        "end_datetime": dt_end,
        "source_name": "viirs",
        "platform_name": plat_name,
        "data_provider": "NOAA",
        "sample_distance_km": 1,
        "interpolation_radius_of_influence": 2000,
    }

    attr_xr = xr.Dataset(attrs=meta_attrs)
    attr_dict = {"METADATA": attr_xr}
    if metadata_only:
        return attr_dict

    full_xr = {}
    # trim VARLIST based on channels requested
    if chans:
        tmp_vl = VARLIST.copy()
        for key, val in tmp_vl.items():
            km = [c[:3] in val for c in chans]
            if not any(km):
                VARLIST.pop(key)
            else:
                matches = [s for s in val for c in chans if s in c]
                VARLIST[key] = matches

    # create list from requested keys
    vlist = list(chain.from_iterable(VARLIST.values()))
    trim_flist = [f for f in fnames for v in vlist if "SV" + v in os.path.basename(f)]
    # parse all science files
    for scifile in trim_flist:

        fn_base = os.path.basename(scifile)
        band_fname = re.search(r"SV\w{1}(\d{2}|\w{2})", fn_base)[0]
        LOG.info("Parsing VIIRS file; band {}, filename {}".format(band_fname, fn_base))
        band_type = band_fname[:3]
        band_spec = band_fname[2:]

        sci_xrt = get_sci_data(scifile, band_spec)

        # apply children xr to parents
        parent_key = [k for k, v in VARLIST.items() if band_spec in v][0]
        # update, append, or create xarray
        if parent_key in full_xr.keys():
            if band_spec + "Rad" in list(full_xr[parent_key].variables):
                # append
                geo_xrt = get_geo_data(fn_base, band_type, fnames)
                sci_xrt.update(geo_xrt)
                full_xr[parent_key] = xr.concat(
                    [full_xr[parent_key], sci_xrt], dim="dim_0"
                )
            else:
                # same geo, new data, same band
                full_xr[parent_key].update(sci_xrt)
        else:
            # new geo, new data, new band
            full_xr[parent_key] = sci_xrt
            geo_xrt = get_geo_data(fn_base, band_type, fnames)
            full_xr[parent_key].update(geo_xrt)
            full_xr[parent_key].attrs = meta_attrs
    if bowtie:
        # update data
        for k, dset in full_xr.items():
            tmp_lat = dset["latitude"].data
            tmp_lon = dset["longitude"].data
            # trim_dset = dset.drop_vars(["latitude","longitude"])
            var_avail = list(dset.variables)

            rad_list = [i for i in var_avail if "Rad" in i]
            rad_map = {}
            for rad_name in rad_list:
                rad_var = dset[rad_name].data
                rad_bow, slat, slon = bowtie_correction(rad_var, tmp_lat, tmp_lon)
                rad_map[rad_name] = xr.DataArray(rad_bow, dims=("dim_0", "dim_1"))
            bt_list = [i for i in var_avail if "Ref" in i or "BT" in i]
            bt_map = {}
            for bt_name in bt_list:
                bt_var = dset[bt_name].data
                bt_bow, slat, slon = bowtie_correction(bt_var, tmp_lat, tmp_lon)
                bt_map[bt_name] = xr.DataArray(bt_bow, dims=("dim_0", "dim_1"))

            udict = {
                "latitude": xr.DataArray(slat, dims=("dim_0", "dim_1")),
                "longitude": xr.DataArray(slon, dims=("dim_0", "dim_1")),
            }
            udict.update(bt_map)
            udict.update(rad_map)
            full_xr[k].update(udict)

    if "DNBRef" in chans or chans is None:
        lunar_ref_data = lunarref(
            full_xr["DNB"]["DNBRad"].data,
            full_xr["DNB"]["solar_zenith_angle"].data,
            full_xr["DNB"]["lunar_zenith_angle"].data,
            meta_attrs["start_datetime"].strftime("%Y%m%d%H"),
            meta_attrs["end_datetime"].strftime("%M"),
            full_xr["DNB"]["moon_phase"].data,
        )
        full_xr["DNB"]["DNBRef"] = xr.DataArray(lunar_ref_data, dims=("dim_0", "dim_1"))

    full_xr |= attr_dict

    return full_xr
