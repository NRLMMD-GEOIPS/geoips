"""GFS GRIB model reader

"""

# Python Standard Libraries
import logging
from os.path import basename
from operator import itemgetter


# Installed libraries
import xarray as xr
import pygrib as pyg
import numpy as np


surface_vars = ['Convective available potential energy','Convective inhibition','Temperature',
                'Snow depth','Ice thickness','Precipitation rate','Vegetation','Sunshine Duration',
                'Sea ice temperature','Sea ice area fraction','Wind speed (gust)']
# CAPE, CIN, and PWAT
tmp_attrs = ['units','pressureUnits']
surf_attrs = ['units','shortName',
              'name','typeOfLevel']



def press_grb_to_xr(grb_obj):
    """Converts pressure grb values to xarray.Dataset."""
    # get unq levels
    lvls = np.asarray(sorted(set((i['level'] for i in grb_obj))))
    lats, lons = grb_obj[0].latlons()
    # get unq vars
    tmp_vars = set((i['name'] for i in grb_obj))
    varlist = {}
    for i in tmp_vars:
        key = '_'.join(i.lower().split(' '))
        tmp_data = next(j for j in grb_obj if j['name'] == i)

        # data_attrs = itemgetter(*tmp_attrs)(next(tmp_data).attrs)
        data_attrs = {k:tmp_data[k] for k in tmp_attrs}

        varlist[key] = xr.DataArray(data=[j.values for j in grb_obj if j['name'] == i],
                                    dims=('pres','xi','yi'),
                                    attrs=data_attrs)

    varlist['lat'] = xr.DataArray(lats,dims=('xi','yi'))
    varlist['lon'] = xr.DataArray(lons,dims=('xi','yi'))
    varlist['pres'] = xr.DataArray(lvls,dims=('pres'))
    return varlist
        

def surf_grb_to_xr(grb_obj):
    """Converts surface grb values to xarray.Dataset"""
    varlist = {}

    lats, lons = grb_obj[0].latlons()

    for i in grb_obj:
        tmp_key = '_'.join(i.name.lower().split(' '))

        data_attrs = {k:i[k] for k in surf_attrs}

        varlist[tmp_key] = xr.DataArray(data=i.values,
                                        dims=('xi','yi'),
                                        attrs=data_attrs)

    varlist['lat'] = xr.DataArray(lats,dims=('xi','yi'))
    varlist['lon'] = xr.DataArray(lons,dims=('xi','yi'))
    return None


def read_atmos(filenames):
    """Read gfs common parameters.
    """
    print("Reading ATMOS file")
    xr_list = {'gfs_pressure':[],'gfs_surface':[],'gfs_singlelayer':[]}
    base_time = []
    fcst_time = []
    for f in filenames:
        # read each file
        pg_frame = pyg.open(f)

        # Pressure
        tmp_pres = pg_frame.select(typeOfLevel='isobaricInhPa')
        xr_pres = press_grb_to_xr(tmp_pres)

        # Surface
        tmp_surf = pg_frame.select(name=surface_vars,
                                   typeOfLevel='surface')
        surface_xr = surf_grb_to_xr(tmp_surf)

        # Single Layer, is ok to considerd as surface (slab)
        tmp_sl = pg_frame.select(typeOfLevel='atmosphereSingleLayer')
        single_atm_xr = surf_grb_to_xr(tmp_sl)

        xr_list['gfs_pressure'].append(xr_pres)
        xr_list['gfs_surface'].append(surface_xr)
        xr_list['gfs_singlelayer'].append(single_atm_xr)

        # track the analysis and valid forcast date
        base_time.append(tmp_sl[0].analDate)
        fcst_time.append(tmp_sl[0].validDate)

    if set(base_time) > 1:
        # one set time with multiple forcasts
        LOG.info("One forcast time")
        base_time = base_time[0]
    else:
        LOG.info("Multiple base forcast times, attempting merge")
    # track valid and analysis date

    return xr_list

def read_wave(filenames):
    """Read gfswave products.
    """
    print("Reading gfswave")
    return None

def read_comb(filenames):
    """Read combined (pgrb2full) products.
    """
    print("reading combined")
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
        res = float('.'.join(base_fnames[0].split(".")[3].split('p')))*111
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
        raise FileExistsError("Multiple file types given, please feed in one gfs file type.")
    if "gfs" in gfs_type:
        xr_array = read_atmos(fnames)
    elif "gfs_wave" in gfs_type:
        xr_array = read_wave(fnames)

    return xr_array
