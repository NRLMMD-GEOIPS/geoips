# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""VIIRS SDR Satpy reader.

This VIIRS reader is designed for reading the NPP/JPSS SDR HDF5 files.
The input files are produced by CSPP Polar (CSPP RDR pipeline),
and the read by satpy.

V1.1.0:  NRL-Monterey, Aug. 2024

"""

# Python Standard Libraries
import logging
import os

# Third-Party Libraries
import h5py
import numpy as np
from pandas import DataFrame, date_range, to_datetime
from scipy.interpolate import NearestNDInterpolator
import xarray as xr

# GeoIPS Libraries
from geoips.plugins.modules.readers.utils.geostationary_geolocation import get_indexes
from geoips.utils.context_managers import import_optional_dependencies

# If this reader is not installed on the system, don't fail altogether, just skip this
# import. This reader will not work if the import fails, and the package will have to be
# installed to process data of this type.

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "viirs_sdr_hdf5"
source_names = ["viirs"]

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    import satpy

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


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    resample=False,
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
            LOG.warning("No variables found in data for viirs_sdr reader.")
            continue

        for d in dataset_ids:
            tmp_scn.load([d])
            full_key = tmp_scn[d].attrs["name"] + tmp_scn[d].attrs[
                "calibration"
            ].capitalize()[:3].replace("Bri", "BT")

            tmp_ma = tmp_scn[d].to_masked_array().data

            # load band
            tmp_scn.load([d])

            lat = tmp_scn[d].area.lats.to_masked_array().data
            lon = tmp_scn[d].area.lons.to_masked_array().data

            # bowtie correction
            if bowtie:
                band_data, band_lat, band_lon = bowtie_correction(tmp_ma, lat, lon)
            else:
                band_data, band_lat, band_lon = tmp_ma, lat, lon

            if "Ref" in full_key:
                from geoips.data_manipulations.corrections import apply_gamma

                # gamma expects data 0-1 range
                # Gamma factor derived from log rule
                # log(mean)/log(0.5) for mean rng 0 to 1
                band_data = apply_gamma(band_data / 100, 1.65) * 100

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

        # sample time to the proper shape (N*48), while lat/lon are ()
        time_range = date_range(
            start=scn_start,
            end=scn_end,
            periods=tmp_coor["latitude"][1].shape[0],
        ).values
        interp_time = np.tile(time_range, (tmp_coor["latitude"][1].shape[1], 1)).T
        tmp_coor["time"] = (("dim_0", "dim_1"), interp_time)

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
            i.removeprefix("dnb_"): (
                ("dim_0", "dim_1"),
                tmp_scn[i].to_masked_array(),
            )
            for i in cal_params
        }

        if var == "DNB":
            try:
                from lunarref.lib.liblunarref import lunarref

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

        if cal_xr.sizes["dim_0"] > coor_xr.sizes["dim_0"]:
            cal_xr = cal_xr.coarsen(dim_0=2, dim_1=2).mean()

        tmp_xr = xr.merge([obs_xr, coor_xr, cal_xr])

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

    # Geolocation resampling
    if resample and area_def:
        adname = area_def.area_id
        new_shape = area_def.shape

        LOG.info("")
        LOG.info("Getting geolocation information for {}.".format(adname))

        for dtype in full_xr.keys():
            if "latitude" not in full_xr[dtype].variables:
                LOG.info(
                    "No data read for dataset %s, removing from xarray list", dtype
                )
                continue
            fldk_lats = full_xr[dtype]["latitude"]
            fldk_lons = full_xr[dtype]["longitude"]
            # Get just the metadata we need
            geo_metadata = full_xr[dtype].attrs.copy()
            geo_metadata["num_lines"], geo_metadata["num_samples"] = fldk_lats.shape
            geo_metadata["scene"] = "stitched_granules"
            geo_metadata["fnames"] = geo_metadata.pop("source_file_name")
            geo_metadata["roi_factor"] = 5
            lines, samples = get_indexes(geo_metadata, fldk_lats, fldk_lons, area_def)

            index_mask = lines != -999

            new_dim0 = "dim_{:d}".format(new_shape[0])
            new_dim1 = "dim_{:d}".format(new_shape[1])

            for varname in full_xr[dtype].variables.keys():
                new_var = np.full(new_shape, -999.1)
                new_var[index_mask] = full_xr[dtype][varname].values[
                    lines[index_mask], samples[index_mask]
                ]
                # out_var = new_var
                if varname not in cal_params + ["latitude", "longitude"]:
                    # Set values <= -999.9 to NaN so they also get interpolated.
                    new_var[np.where(new_var <= -999.9)] = np.nan
                    # Interpolate missing data.
                    out_var = np.array(DataFrame(new_var).interpolate())
                else:
                    out_var = new_var
                full_xr[dtype][varname] = xr.DataArray(
                    out_var, dims=[new_dim0, new_dim1]
                )
            if "time" in full_xr[dtype].variables:
                time_data = full_xr[dtype]["time"].data
                time_data = np.asarray(to_datetime(time_data.ravel())).reshape(
                    time_data.shape
                )
                full_xr[dtype]["time"].data = time_data

            ll_mask = full_xr[dtype]["latitude"].data >= -90
            for varname in full_xr[dtype].variables.keys():
                full_xr[dtype][varname] = full_xr[dtype][varname].where(ll_mask)

        LOG.interactive("Done with geolocation for {}".format(adname))
        LOG.info("")

    return full_xr
