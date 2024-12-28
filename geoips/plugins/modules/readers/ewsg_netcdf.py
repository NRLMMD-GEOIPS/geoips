# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read EWS-G data.

This EWS-G(Electro-Optical Infrared Weather System - Geostationary) reader is
designed for reading theEWS-G data files (EWS-G is renamed from GOES-13).
The reader is only using the python functions and xarray variables.
The reader is based on EWS-G data in netcdf4 format.

 V1.0:  NRL-Monterey, 02/25/2021

EWS-G file information::

    Example of the gvar filename:   2020.1212.0012.goes-13.gvar.nc

    Note that channel-3 is not available for EWS-G.
      gvar_Ch3(TIR=5.8-7.3um, ctr=6.48um,4km): unit=temp-deg(C), scale_factor=0.01

    variables:
      gvar_Ch1(VIS=0.55-0.75um, ctr=0.65um,1km): unit=albedo*100,  scale_factor=0.01
      gvar_Ch2(MWIR=3.8-4.0um,  ctr=3.9um, 4km): unit=temp-deg(C), scale_factor=0.01
      gvar_Ch4(TIR=10.2-11.2um, ctr=10.7um,4km): unit=temp-deg(C), scale_factor=0.01
      gvar_Ch6(TIR=12.9-13.7um, ctr=13.3um 4km): unit=temp-deg(C), scale_factor=0.01
      latitude: unit=degree
      longitude:unit=degree
      sat_zenith: unit=degree
      sun_zenith: unit=degree
      rel_azimuth:unit=degree

      variable array definition:  var(scan,pix); scan-->lines, pix-->samples

    attributes: many
"""
# Python Standard Libraries
import logging
import os

# Third-Party Libraries
import calendar
import numpy as np
import pandas as pd
import xarray as xr

from geoips.interfaces import readers
from geoips.utils.context_managers import import_optional_dependencies

# If this reader is not installed on the system, don't fail altogether, just skip this
# import. This reader will not work if the import fails, and the package will have to be
# installed to process data of this type.

LOG = logging.getLogger(__name__)

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    import netCDF4 as ncdf


# @staticmethod                                     # not sure where it is was used?

# gvar_ch6 has only half scanlines of other channels (1,2,4), we temporally do not read
# the ch6 in. We will modify this reader if gvar_ch6 is needed in the future.
VARLIST = [
    "gvar_ch1",
    "gvar_ch2",
    "gvar_ch4",
    "latitude",
    "longitude",
    "sun_zenith",
    "sat_zenith",
    "rel_azimuth",
]

# setup needed to convert var_name used in geoips: i.e., solar_zenith_angle (not
# sun_zenith) is used.
xvarnames = {
    "sun_zenith": "solar_zenith_angle",
    "sat_zenith": "satellite_zenith_angle",
    "rel_azimuth": "satellite_azimuth_angle",
}

interface = "readers"
family = "standard"
name = "ewsg_netcdf"
source_names = ["gvar"]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read EWS-G data in netcdf4 format.

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
    return readers.read_data_to_xarray_dict(
        fnames,
        call_single_time,
        metadata_only,
        chans,
        area_def,
        self_register,
    )


def call_single_time(
    fnames, metadata_only=False, chans=None, area_def=None, self_register=False
):
    """Read EWS-G data in netcdf4 format for one or more files.

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
    # --------------- loop input files ---------------
    xarray_ewsg = xr.Dataset()
    xarray_ewsg.attrs["source_file_names"] = []
    # LOG.info('Requested Channels: %s', chans)

    for fname in fnames:
        # check for a correct goes-13 data file
        data_name = os.path.basename(fname).split("_")[-1].split(".")[-1]
        if data_name != "nc":
            LOG.info("Warning: EWS-G data type:  data_type=", data_name)
            raise

        # open the paired input files
        ncdf_file = ncdf.Dataset(str(fname), "r")
        LOG.info("    Trying file %s", fname)

        if ncdf_file.satellite in ["goes-13", "goes-15"]:
            LOG.info("found a NOAA EWS-G data file")
        else:
            LOG.info("not a NOAA EWS-G data file: skip it")
            raise ValueError(
                f"Found {ncdf_file.satellite}, expected either goes-13 or goes-15"
            )

        # setup attributes
        # use fname to get an initial info of  year, month, day
        # test hour/minute/second of "start_datetime" info from start_time (second of
        # the day). add scan_time info to determine the "end_datetime". scan_time has
        # time of scans for this input data file(one obs).  If end_time of this data >24
        # hr, modify value of "day" from fname.  Note: scan_time units are seconds from
        # (start_time + time_adjust)

        # date info from fname
        #        1  2  3  4  5  6  7  8  9  10 11 12
        days_mo = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        days_mo_lp = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # Leap year

        # date information is not contained in the data so we have to get it from
        # filename
        data_name = os.path.basename(fname)
        yr = int(data_name.split(".")[0])
        mo = int(data_name.split(".")[1][0:2])
        dy = int(data_name.split(".")[1][2:4])
        # hr = int(data_name.split(".")[2][0:2])
        # mm = int(data_name.split(".")[2][2:4])

        # determine a Leap Year?
        if calendar.isleap(yr):
            days = days_mo_lp[mo - 1]
        else:
            days = days_mo[mo - 1]

        # second of the date for this file
        start_time = (
            ncdf_file.start_time + ncdf_file.time_adjust + ncdf_file.scan_time[0]
        )
        end_time = (
            ncdf_file.start_time + ncdf_file.time_adjust + ncdf_file.scan_time[29]
        )

        yr_s = yr
        yr_e = yr
        mo_s = mo
        mo_e = mo
        dy_s = dy
        dy_e = dy
        hr_s = int(start_time / 3600)
        mm_s = int((start_time - hr_s * 3600) / 60)
        ss_s = int(start_time - (hr_s * 3600 + mm_s * 60))
        hr_e = int(end_time / 3600)
        mm_e = int((end_time - hr_e * 3600) / 60)
        ss_e = int(end_time - (hr_e * 3600 + mm_e * 60))

        if hr_s >= 24:
            # dy_s_ = dy + 1  # forward to the next date
            hr_s = hr_s - 24
            if dy_s > days:  # move to next mon
                mo_s = mo + 1
                if mo_s > 12:  # move to near year
                    yr_s = yr + 1
        if hr_e >= 24:
            # dy_e_ = dy + 1  # forward to the next date
            hr_e = hr_e - 24
            if dy_e > days:  # move to next mon
                mo_e = mo + 1
                if mo_e > 12:  # move to near year
                    yr_e = yr + 1

        start_scan = "%04d%02d%02d%02d%02d%02d" % (yr_s, mo_s, dy_s, hr_s, mm_s, ss_s)
        end_scan = "%04d%02d%02d%02d%02d%02d" % (yr_e, mo_e, dy_e, hr_e, mm_e, ss_e)

        # convert date in required format
        Start_date = pd.to_datetime(start_scan, format="%Y%m%d%H%M%S")
        End_date = pd.to_datetime(end_scan, format="%Y%m%d%H%M%S")

        xarray_ewsg.attrs["start_datetime"] = Start_date
        xarray_ewsg.attrs["end_datetime"] = End_date
        # Goes VARiable (gvar) data is on GOES-12/13 - older GOES satellites were gvissr
        # ncdf_file.sensor_name is gvissr - I think that is a mistake on
        # Terascan's part - hold out from years ago
        xarray_ewsg.attrs["source_name"] = "gvar"

        if ncdf_file.satellite == "goes-13":
            xarray_ewsg.attrs["platform_name"] = "ews-g1"
        if ncdf_file.satellite == "goes-15":
            xarray_ewsg.attrs["platform_name"] = "ews-g2"
        xarray_ewsg.attrs["legacy_platform_name"] = ncdf_file.satellite
        xarray_ewsg.attrs["data_provider"] = "noaa"
        xarray_ewsg.attrs["source_file_names"] = [
            os.path.basename(fname) for fname in fnames
        ]

        # MTIFs need to be "prettier" for PMW products, so 2km resolution for
        # final image
        xarray_ewsg.attrs["sample_distance_km"] = 2
        xarray_ewsg.attrs["interpolation_radius_of_influence"] = 3000
        # Just return the metadata
        if metadata_only:
            # close the files
            ncdf_file.close()
            return {"METADATA": xarray_ewsg}
        # Otherwise, get the actual data, as well as the metadata
        # *************** input VIRRS variables  and output xarray required by geo

        # for varname in ncdf_file.variables.keys():
        for var in VARLIST:
            varname = var
            data = ncdf_file[varname]
            # masked_data=np.ma.masked_equal(
            #   ncdf_file[varname],ncdf_file[varname].missing_value
            # )
            masked_data = np.ma.masked_equal(data, data.missing_value)

            if var in xvarnames:
                varname = xvarnames[var]  # rename zenith/azimuth-related variables

            xarray_ewsg[varname] = xr.DataArray(masked_data)
            """
            # scale_factor should not be applied
            if 'scale_factor' in data.ncattrs():
                # apply scale_factor correction
                #xarray_ewsg[varname]=xarray_ewsg[varname]*ncdf_file[varname].scale_factor  # NOQA
                xarray_ewsg[varname]=xarray_ewsg[varname]*data.scale_factor
            """
            # convert unit from degree to Kelvin for ch2, ch4, and ch6 (ch1 is in unit
            # of albedo)
            if varname in ["gvar_ch2", "gvar_ch4", "gvar_ch6"]:
                xarray_ewsg[varname] = xarray_ewsg[varname] + 273.15
                xarray_ewsg[varname].attrs["units"] = "Kelvin"

        # close the files
        ncdf_file.close()

    return {"LOW": xarray_ewsg, "METADATA": xarray_ewsg[[]]}
