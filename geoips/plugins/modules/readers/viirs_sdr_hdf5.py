"""VIIRS SDR Satpy reader.

This VIIRS reader is designed for reading the NPP/JPSS SDR HDF5 files.
The input files are produced by CSPP Polar (CSPP RDR pipeline),
and the read by satpy.

V1.1.0:  NRL-Monterey, Aug. 2024

"""

# Python Standard Libraries
import logging
import os

# Installed Libraries
import xarray as xr
import numpy as np
import h5py
from pandas import date_range
from pykdtree.kdtree import KDTree

# If this reader is not installed on the system, don't fail altogether, just skip this
# import. This reader will not work if the import fails, and the package will have to be
# installed to process data of this type.
LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "viirs_sdr_hdf5"
source_names = ["viirs"]

try:
    import satpy
except ImportError:
    LOG.info("Failed import satpy. If you need it, install it.")

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
    # no_shift_flag = np.argsort(ord_lat, axis=0) == unfold_idx

    rad_fold = np.take_along_axis(band, unfold_idx, axis=0)
    sort_lon = np.take_along_axis(lon, unfold_idx, axis=0)

    if np.all(np.isnan(rad_fold)):
        LOG.debug("All nan band, no bowtie correction")
        return rad_fold, ord_lat, sort_lon

    # Adjust lon, not used for satpy
    # Only need for manual read with overlapping granuales
    # ord_lon = np.empty(lon.shape)
    # xi = np.arange(sort_lon.shape[0])

    # for x in range(lon.shape[1]):
    # 0 shift xi values
    # xo = xi[no_shift_flag[:, x]]

    # if all(no_shift_flag[:, x]):
    # if there was no shift in the column
    # ord_lon[:, x] = lon[:, x]
    # continue
    # elif not any(no_shift_flag[:, x]):
    # if the whole column was shifted (should be rare)
    # ord_lon[:, x] = sort_lon[:, x]
    # continue

    # longitude values that were not shifted
    # noshift_lon = sort_lon[xo,x]
    # noshift_lon = sort_lon[:, x][no_shift_flag[:, x]]
    # replace only values that were shifted
    # nsf = no_shift_flag[:, x]

    # ord_lon[nsf, x] = noshift_lon
    # ord_lon[~nsf, x] = np.interp(xi, xo, noshift_lon)[~nsf]

    # Resample
    point_mask = np.isnan(rad_fold)

    good_points = np.dstack((ord_lat[~point_mask], sort_lon[~point_mask]))[0]
    bad_points = np.dstack((ord_lat[point_mask], sort_lon[point_mask]))[0]

    res_band = rad_fold.copy()
    good_rad = rad_fold[~point_mask]
    rad_idx = np.indices(rad_fold.shape)
    ridx, ridy = rad_idx[0][point_mask], rad_idx[1][point_mask]
    os.environ["OMP_NUM_THREADS"] = "64"

    kd_tree = KDTree(good_points)
    # print("Querying")
    dist, idx = kd_tree.query(bad_points, k=4)  # ,workers=4)

    for i in range(bad_points.shape[0]):
        xi, yi = ridx[i], ridy[i]

        if np.any(dist[i] == 0):
            # weight the zero to a small value
            weight = np.where(dist[i] == 0, 1e-6, dist[i])
            res_band[xi, yi] = np.average(good_rad[idx[i]], weights=1 / weight)
            continue

        res_band[xi, yi] = np.average(good_rad[idx[i]], weights=1 / dist[i])

    return res_band, ord_lat.astype(np.float64), sort_lon.astype(np.float64)


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
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

    Returns
    -------
    dict of xarray.Datasets
        * dictionary of xarray.Dataset objects with required Variables and
          Attributes.
        * Dictionary keys can be any descriptive dataset ids.
        * Conforms to geoips xarray standards, see more in geoips documentation.
    """
    # print("Reading")
    tmp_scn = satpy.Scene(reader="viirs_sdr", filenames=fnames)
    scn_start, scn_end = tmp_scn.start_time, tmp_scn.end_time
    base_fnames = list(map(os.path.basename, fnames))

    full_xr = {}
    if metadata_only:
        # average resolution
        # sensor, plat name
        tmp_scn.load([tmp_scn.available_dataset_names()[0]])
        tmp_attrs = tmp_scn[tmp_scn.available_dataset_names()[0]].attrs
        tmp_xr = xr.Dataset(
            attrs={
                "source_file_name": base_fnames[0],
                "start_datetime": scn_start,
                "end_datetime": scn_end,
                "source_name": tmp_attrs["sensor"],
                "platform_name": tmp_attrs["platform_name"],
                "data_provider": "NOAA",
                "sample_distance_km": 1,
                "interpolation_radius_of_influence": 1000,  # guess!
            }
        )
        tmp_dict = {"METADATA": tmp_xr}
        return tmp_dict

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

    # could opimize more
    tmp_coor = {}
    for var in VARLIST:
        tmp_dask = {}
        dataset_ids = [
            idx
            for idx in tmp_scn.available_dataset_ids()
            if idx["name"] in VARLIST[var]
        ]
        if len(dataset_ids) == 0:
            # print("No datasets found for {}.".format(VARLIST[var]))
            continue

        for d in dataset_ids:
            # print("Loading {}".format(d))
            tmp_scn.load([d])
            full_key = tmp_scn[d].attrs["name"] + tmp_scn[d].attrs[
                "calibration"
            ].capitalize()[:3].replace("Bri", "BT")

            tmp_ma = tmp_scn[d].to_masked_array().data

            #
            tmp_scn.load([d])

            lat = tmp_scn[d].area.lats.to_masked_array().data
            lon = tmp_scn[d].area.lons.to_masked_array().data

            # bowtie correction
            band_data, band_lat, band_lon = bowtie_correction(tmp_ma, lat, lon)

            tmp_dask |= {full_key: (("dim_0", "dim_1"), band_data)}

        # coordinates
        tmp_coor["latitude"] = (
            ("dim_0", "dim_1"),
            band_lat,
        )
        tmp_coor["longitude"] = (
            ("dim_0", "dim_1"),
            band_lon,
        )
        # print("Setting cal vals")
        # sample time to the proper shape (N*48), while lat/lon are ()
        time_range = date_range(
            start=scn_start, end=scn_end, periods=tmp_coor["latitude"][1].shape[0]
        ).values
        interp_time = np.tile(time_range, (tmp_coor["latitude"][1].shape[1], 1)).T
        tmp_coor["time"] = (("dim_0", "dim_1"), interp_time)
        # # print(tmp_coor["latitude"][1].shape)
        # raise

        tmp_attrs = tmp_scn[VARLIST[var][0]].attrs

        cal_params = [
            "satellite_azimuth_angle",
            "satellite_zenith_angle",
            "solar_azimuth_angle",
            "solar_zenith_angle",
        ]

        if var == "DNB":
            cal_params = [
                "dnb_lunar_azimuth_angle",
                "dnb_lunar_zenith_angle",
                "dnb_satellite_azimuth_angle",
                "dnb_satellite_zenith_angle",
                "dnb_solar_azimuth_angle",
                "dnb_solar_zenith_angle",
            ]

        tmp_scn.load(cal_params)
        tmp_cal_params = {
            i.removeprefix("dnb_"): (("dim_0", "dim_1"), tmp_scn[i].to_masked_array())
            for i in cal_params
        }

        if var == "DNB":
            try:
                from lunarref.lib.liblunarref import lunarref

                # tmp_scn.load(["dnb_moon_illumination_fraction"])
                # this results in the wrong value..
                # np.arccos((tmp_scn["dnb_moon_illumination_fraction"].data/50)-1)

                dnb_geofile = [i for i in fnames if "GDNBO" in os.path.basename(i)][0]
                h5_dnb = h5py.File(dnb_geofile)
                phase_ang = h5_dnb["All_Data/VIIRS-DNB-GEO_All/MoonPhaseAngle"][...]

                lunarref_data = lunarref(
                    tmp_dask["DNBRad"][1],
                    tmp_cal_params["solar_zenith_angle"][1],
                    tmp_cal_params["lunar_zenith_angle"][1],
                    scn_start.strftime("%Y%m%d%H"),
                    scn_start.strftime("%M"),
                    phase_ang,
                )
                lunarref_data = np.ma.masked_less_equal(lunarref_data, -999, copy=False)
                tmp_dask |= {"DNBRef": (("dim_0", "dim_1"), lunarref_data)}
            except ImportError:
                LOG.info("Failed lunarref in viirs reader.  If you need it, build it")

        # problem with sat_za/az values being too high, need to downsample
        # print("Building xarray")
        obs_xr = xr.Dataset(data_vars=tmp_dask)
        coor_xr = xr.Dataset(data_vars=tmp_coor)
        cal_xr = xr.Dataset(data_vars=tmp_cal_params)

        try:
            tmp_xr = xr.merge([obs_xr, coor_xr, cal_xr])
        except ValueError:
            # downsample for certain bands
            tmp_xr = xr.merge([obs_xr, coor_xr])

        tmp_xr.attrs = {
            "source_file_name": base_fnames,
            "start_datetime": tmp_scn.start_time,
            "end_datetime": tmp_scn.end_time,
            "source_name": tmp_attrs["sensor"],
            "platform_name": tmp_attrs["platform_name"],
            "data_provider": "NOAA",
            "sample_distance_km": tmp_attrs["resolution"] / 1e3,
            "interpolation_radius_of_influence": 1000,
        }

        full_xr |= {var: tmp_xr}
    full_xr["METADATA"] = xr.Dataset(attrs=tmp_xr.attrs)

    return full_xr
