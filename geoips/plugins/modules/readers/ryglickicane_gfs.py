"""Reader to read GFS Files in GRIB format.

    Current support includes:
       - GFS
       - GFS Wave

This reader can take in multiple forcast times and multiple analysis times.
"""
# Python Standard Libraries
import logging
from os.path import basename


# Installed libraries
import xarray as xr
import pygrib as pyg

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
# CAPE, CIN, and PWAT
tmp_attrs = ["units", "pressureUnits"]
surf_attrs = ["units", "shortName", "name", "typeOfLevel"]


def press_grb_to_xr(grb_obj):
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
            pres_dim = "unk_pres"

        varlist[key] = xr.DataArray(
            data=[j.values for j in grb_obj if j["name"] == i],
            dims=(pres_dim, "xi", "yi"),
            attrs=data_attrs,
        )

    varlist["lat"] = xr.DataArray(lats, dims=("xi", "yi"))
    varlist["lon"] = xr.DataArray(lons, dims=("xi", "yi"))

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

    varlist["lat"] = xr.DataArray(lats, dims=("xi", "yi"))
    varlist["lon"] = xr.DataArray(lons, dims=("xi", "yi"))

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

    for k in xr_list.keys():
        xr_list[k] = xr.concat(xr_list[k], tvar)
        xr_list[k]["forcast_time"] = xr.DataArray(fcst_time, dims=("atime"))

    return xr_list


def read_wave(filenames):
    """Read gfswave products."""
    LOG.info("Reading gfswave")
    return None


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
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
    if metadata_only:

        tmp_read = pyg.read(fnames[0])
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
                "interpolation_radius_of_influence": 1000,
            }
        )
        tmp_dict = {"METADATA": tmp_xr}
        return tmp_dict

    gfs_type = set([i.split(".")[0] for i in base_fnames])
    if len(gfs_type) > 1:
        raise FileExistsError(
            "Multiple file types given, please feed in one gfs file type."
        )
    if "gfs" in gfs_type:
        xr_array = read_atmos(fnames)
    elif "gfs_wave" in gfs_type:
        xr_array = read_wave(fnames)

    return xr_array
