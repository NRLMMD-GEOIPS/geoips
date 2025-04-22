# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Reader to read GFS Files in GRIB format.

    (NRL-Monterey, Sept. 2024)

    Current support includes:
       - GFS
       - GFS Wave global domain

This reader can take in multiple forcast times at multiple analysis times.
"""

# Python Standard Libraries
import logging
from os.path import basename


# Installed libraries
import xarray as xr
import pygrib as pyg
import numpy as np

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "gfs_grib"

surface_vars = [
    "Convective available potential energy",
    "Convective inhibition",
    "Temperature",
    "Snow depth",
    "Ice thickness",
    "Precipitation rate",
    "Vegetation",
    "Sunshine Duration",
    "Sea ice temperature",
    "Sea ice area fraction",
    "Wind speed (gust)",
]
# TBD: rename variables to shorter, simpler names
# ex: significant_height_of_combined_wind_waves_and_swell -> comb_wave_height
tmp_attrs = ["units", "pressureUnits"]
surf_attrs = ["units", "shortName", "name", "typeOfLevel"]

MS_TO_KTS = 1.94384


def convert_uv_to_kts(xr_df):
    """Convert U/V Components to windspeed and winddir."""
    sqrt_func = np.sqrt
    arctan2_func = np.arctan2
    degrees_func = np.degrees

    ucomp = xr_df.u_component_of_wind.values
    vcomp = xr_df.v_component_of_wind.values
    wind_dims = xr_df.u_component_of_wind.dims

    xr_df["windspeed_kts"] = xr.DataArray(
        sqrt_func((ucomp**2) + (vcomp**2)) * MS_TO_KTS, dims=wind_dims
    )
    xr_df["winddir"] = xr.DataArray(
        degrees_func(arctan2_func(-ucomp, -vcomp)) % 360, dims=wind_dims
    )
    return xr_df


def press_grb_to_xr(grb_obj, custom_pressure_name="unk_pres"):
    """Convert pressure grb values to xarray.Dataset.

    Parameters
    ----------
    grb_obj : list of pygrib objects
        * pygrib selected objects (pressure)

    Returns
    -------
    final_xarray : xarray.Dataset
        * xarray formatted to geoips standards
    """
    lats, lons = grb_obj[0].latlons()

    tmp_vars = set((i["name"] for i in grb_obj))
    varlist = {}
    unq_pres = False
    for i in tmp_vars:
        key = "_".join(i.lower().split(" "))
        tmp_data = next(j for j in grb_obj if j["name"] == i)

        data_attrs = {k: tmp_data[k] for k in tmp_attrs}
        tmp_press_lvls = sorted(set(j["level"] for j in grb_obj if j["name"] == i))

        if len(tmp_press_lvls) == 22:
            pres_dim = "coarse_press"
            cpres = tmp_press_lvls
        elif len(tmp_press_lvls) == 33:
            pres_dim = "fine_press"
            fpres = tmp_press_lvls
        else:
            pres_dim = custom_pressure_name
            upres = tmp_press_lvls
            unq_pres = True

        varlist[key] = xr.DataArray(
            data=[j.values for j in grb_obj if j["name"] == i],
            dims=(pres_dim, "xi", "yi"),
            attrs=data_attrs,
        )

    varlist["latitude"] = xr.DataArray(lats, dims=("xi", "yi"))
    varlist["longitude"] = xr.DataArray(lons, dims=("xi", "yi"))
    if unq_pres:
        varlist[custom_pressure_name] = xr.DataArray(upres, dims=(custom_pressure_name))
    else:
        varlist["coarse_press"] = xr.DataArray(cpres, dims=("coarse_press"))
        varlist["fine_press"] = xr.DataArray(fpres, dims=("fine_press"))

    xr_dset = xr.Dataset(varlist)

    return xr_dset


def surf_grb_to_xr(grb_obj):
    """Convert surface grb values to xarray.Dataset.

    Parameters
    ----------
    grb_obj : list of pygrib objects
        * pygrib selected objects (single/surface layer)

    Returns
    -------
    final_xarray : xarray.Dataset
        * xarray formatted to geoips standards
    """
    varlist = {}

    lats, lons = grb_obj[0].latlons()

    for i in grb_obj:
        tmp_key = "_".join(i.name.lower().split(" "))

        data_attrs = {k: i[k] for k in surf_attrs}

        varlist[tmp_key] = xr.DataArray(
            data=i.values, dims=("xi", "yi"), attrs=data_attrs
        )

    varlist["latitude"] = xr.DataArray(lats, dims=("xi", "yi"))
    varlist["longitude"] = xr.DataArray(lons, dims=("xi", "yi"))

    xr_dset = xr.Dataset(varlist)
    return xr_dset


def read_atmos(filenames):
    """Read gfs files.

    Parameters
    ----------
    filenames : list of filepaths
        * gfs grib files

    Returns
    -------
    final_xarray : xarray.Dataset
        * xarray formatted to geoips standards
    """
    LOG.info("Reading ATMOS file")
    xr_list = {"gfs_pressure": [], "gfs_surface": [], "gfs_singlelayer": []}
    base_time = []
    fcst_time = []
    for f in filenames:
        # read each file
        pg_frame = pyg.open(f)

        # Pressure
        tmp_pres = pg_frame.select(typeOfLevel="isobaricInhPa")
        xr_pres = press_grb_to_xr(tmp_pres)

        xr_pres = convert_uv_to_kts(xr_pres)

        # Surface
        tmp_surf = pg_frame.select(name=surface_vars, typeOfLevel="surface")
        surface_xr = surf_grb_to_xr(tmp_surf)

        # Single Layer, is ok to considerd as surface (slab)
        tmp_sl = pg_frame.select(typeOfLevel="atmosphereSingleLayer")
        single_atm_xr = surf_grb_to_xr(tmp_sl)

        xr_list["gfs_pressure"].append(xr_pres)
        xr_list["gfs_surface"].append(surface_xr)
        xr_list["gfs_singlelayer"].append(single_atm_xr)

        # track the analysis and valid forcast date
        base_time.append(tmp_sl[0].analDate)
        fcst_time.append(tmp_sl[0].validDate)

    tvar = xr.DataArray(base_time, dims=("atime"))
    bname = list(map(basename, filenames))
    res = float(".".join(bname[0].split(".")[3].split("p"))) * 111

    xr_attrs = {
        "source_file_name": bname,
        "start_datetime": base_time[0],
        "end_datetime": fcst_time[-1],
        "source_name": "gfs",
        "platform_name": "model",
        "data_provider": "NOAA",
        "sample_distance_km": res,
        "interpolation_radius_of_influence": 30000,
    }

    for k in xr_list.keys():
        xr_list[k] = xr.concat(xr_list[k], tvar)
        xr_list[k]["forcast_time"] = xr.DataArray(fcst_time, dims=("atime"))
        xr_list[k] = xr_list[k].assign_attrs(xr_attrs)
        # fix lat lon shape (fix upstream)
        xr_list[k]["latitude"] = xr_list[k]["latitude"][0]
        # if np.any(xr_list[k]['longitude'][0] > 180):
        xr_list[k]["longitude"] = xr_list[k]["longitude"][0]
        xr_list[k] = xr_list[k].transpose("xi", "yi", ...)

    return xr_list


def read_wave(filenames):
    """Read gfswave products."""
    LOG.info("Reading gfswave")
    xr_list = {"wave_surface": [], "wave_seq": []}
    base_time = []
    fcst_time = []
    for f in filenames:
        # read each file
        pg_frame = pyg.open(f)

        # Surface
        tmp_surf = pg_frame.select(typeOfLevel="surface")
        surface_xr = surf_grb_to_xr(tmp_surf)

        # sequence data
        tmp_seq = pg_frame.select(typeOfLevel="orderedSequenceData")
        # this is equal to levels
        seq_xr = press_grb_to_xr(tmp_seq, custom_pressure_name="wave_seq")

        xr_list["wave_seq"].append(seq_xr)
        xr_list["wave_surface"].append(surface_xr)

        base_time.append(tmp_seq[0].analDate)
        fcst_time.append(tmp_seq[0].validDate)

    tvar = xr.DataArray(base_time, dims=("atime"))
    bname = list(map(basename, filenames))
    res = float(".".join(bname[0].split(".")[3].split("p"))) * 111

    xr_attrs = {
        "source_file_name": bname,
        "start_datetime": base_time[0],
        "end_datetime": fcst_time[-1],
        "source_name": "gfs",
        "platform_name": "model",
        "data_provider": "NOAA",
        "sample_distance_km": res,
        "interpolation_radius_of_influence": 30000,
    }

    for k in xr_list.keys():
        xr_list[k] = xr.concat(xr_list[k], tvar)
        xr_list[k]["forcast_time"] = xr.DataArray(fcst_time, dims=("atime"))
        xr_list[k] = xr_list[k].assign_attrs(xr_attrs)
        # fix lat lon shape (fix upstream)
        xr_list[k]["latitude"] = xr_list[k]["latitude"][0]
        # if np.any(xr_list[k]['longitude'][0] > 180):
        xr_list[k]["longitude"] = xr_list[k]["longitude"][0]
        xr_list[k] = xr_list[k].transpose("xi", "yi", ...)

    return xr_list


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read GFS GRIB data.

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
        * Conforms to geoips xarray standards, see more in geoips documentation.
    """
    base_fnames = list(map(basename, fnames))
    fnames = sorted(fnames)

    tmp_read = pyg.open(fnames[0])
    tmp_val = tmp_read.read(1)[0]

    dtime_start = tmp_val.analDate
    dtime_end = tmp_val.validDate

    # rough resolution from degrees
    res = float(".".join(base_fnames[0].split(".")[3].split("p"))) * 111
    tmp_xr = xr.Dataset(
        attrs={
            "source_file_name": base_fnames,
            "start_datetime": dtime_start,
            "end_datetime": dtime_end,
            "source_name": "gfs",
            "platform_name": "model",
            "data_provider": "NOAA",
            "sample_distance_km": res,
            "interpolation_radius_of_influence": 30000,
        }
    )
    if metadata_only:
        tmp_dict = {"METADATA": tmp_xr}
        return tmp_dict

    gfs_type = set([i.split(".")[0] for i in base_fnames])
    xr_array = {}
    if len(gfs_type) > 1:
        raise FileExistsError(
            "Multiple file types given, please feed in one gfs file type."
        )
    if "gfs" in gfs_type:
        xr_array = read_atmos(fnames)
    elif "gfswave" in gfs_type:
        xr_array = read_wave(fnames)

    xr_array["METADATA"] = tmp_xr

    return xr_array
