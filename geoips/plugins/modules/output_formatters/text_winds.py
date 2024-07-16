# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Routines for outputting formatted text wind speed and vector data files."""

import logging
import os
from datetime import datetime
import numpy
import shutil

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xrdict_varlist_outfnames_to_outlist"
name = "text_winds"


def call(
    xarray_dict, varlist, output_fnames, append=False, overwrite=True, source_names=None
):
    """Write text windspeed output file."""
    output_products = []
    num_arrs = 0
    for key in xarray_dict:
        if key == "METADATA":
            continue
        xarray_obj = xarray_dict[key]
        if "wind_speed_kts" not in xarray_obj.variables:
            continue
        if num_arrs == 0:
            curr_append = append
        else:
            curr_append = True
        num_arrs = num_arrs + 1
        output_products += write_text_winds(
            xarray_obj,
            varlist,
            output_fnames.copy(),  # It will overwrite it if we don't copy
            append=curr_append,
            overwrite=overwrite,
            source_names=source_names,
        )

    # Remove any duplicates - they would have been overwritten
    return list(set(output_products))


def write_text_winds(
    xarray_obj, varlist, output_fnames, append=False, overwrite=True, source_names=None
):
    """Write out TC formatted text file of wind speeds.

    Parameters
    ----------
    text_fname : str
        String full path to output filename
    speed_array : ndarray
        array of windspeeds
    time_array : ndarray
        array of POSIX time stamps same length as speed_array
    lon_array : ndarray
        array of longitudes of same length as speed_array
    lat_array : ndarray
        array of latitudes of same length as speed_array
    platform_name : str
        String platform name
    """
    # NOTE long does not exist in Python 3, so changed this to int.  This will
    # limit us to 32 bit integers within Python 2
    # time_array = wind_xarray['time'].to_masked_array().astype(long).flatten()
    time_array = xarray_obj["time"].to_masked_array().astype(int).flatten()
    # This results in an array of POSIX timestamps - seconds since epoch.
    time_array = time_array / 10**9

    speed_array = xarray_obj["wind_speed_kts"].to_masked_array().flatten()
    lat_array = xarray_obj["latitude"].to_masked_array().flatten()
    lon_array = xarray_obj["longitude"].to_masked_array().flatten()
    platform_name = xarray_obj.platform_name
    source_name = platform_name.upper()
    # If we passed a dictionary of source_name mappings, and it contains the
    # current platform_name, swap it out.
    if source_names is not None and platform_name in source_names:
        source_name = source_names[platform_name].upper()
    dir_array = None
    if "wind_dir_deg_met" in xarray_obj.variables:
        dir_array = xarray_obj["wind_dir_deg_met"].to_masked_array().flatten()
    output_products = []

    if not isinstance(platform_name, str):
        raise TypeError("Parameter platform_name must be a str")
    if not isinstance(output_fnames, list):
        raise TypeError("Parameter output_fnames must be a list of str")
    if not isinstance(speed_array, numpy.ndarray):
        raise TypeError("Parameter speed_array must be a numpy.ndarray of wind speeds")
    if not isinstance(lat_array, numpy.ndarray):
        raise TypeError("Parameter lat_array must be a numpy.ndarray of latitudes")
    if not isinstance(lon_array, numpy.ndarray):
        raise TypeError("Parameter lon_array must be a numpy.ndarray of longitudes")
    if not isinstance(time_array, numpy.ndarray):
        raise TypeError(
            "Parameter time_array must be a numpy.ndarray of POSIX timestamps"
        )

    if hasattr(speed_array, "mask"):
        if dir_array is not None:
            newmask = (
                speed_array.mask
                | time_array.mask
                | lat_array.mask
                | lon_array.mask
                | dir_array.mask
            )
        else:
            newmask = (
                speed_array.mask | time_array.mask | lat_array.mask | lon_array.mask
            )
        inds = numpy.ma.where(~newmask)
        speed_array = speed_array[inds]
        time_array = time_array[inds]
        lon_array = lon_array[inds]
        lat_array = lat_array[inds]
        if dir_array is not None:
            dir_array = dir_array[inds]

    openstr = "w"
    if append:
        openstr = "a"
    startdt_str = datetime.utcfromtimestamp(time_array[0]).strftime("%Y%m%d%H%M")
    header = ""

    for text_fname in output_fnames:
        if os.path.exists(text_fname) and not overwrite and not append:
            LOG.info("File already exists, not overwriting %s", text_fname)
            continue
        if not isinstance(text_fname, str):
            raise TypeError("Parameter text_fname must be a str")

        from geoips.filenames.base_paths import make_dirs

        make_dirs(os.path.dirname(text_fname))

    text_fname = output_fnames.pop()
    if not os.path.exists(text_fname) or not append:
        header = "METXSCT {0} ASC (FULL DAY)\n".format(startdt_str)
    with open(text_fname, openstr) as fobj:
        if dir_array is not None:
            fobj.write(header)
            for speed, time, lon, lat, direction in zip(
                speed_array, time_array, lon_array, lat_array, dir_array
            ):
                # dtstr = time.strftime('%Y%m%d%H%M')
                dtstr = datetime.utcfromtimestamp(time).strftime("%Y%m%d%H%M")
                # if lon > 180:
                #     lon = lon - 360
                format_string = " {0:>3s} {1:>8.1f} {2:>6.1f} {3:>3d} {4:>3d} {5:s}\n"
                fobj.write(
                    format_string.format(
                        source_name, lat, lon, int(direction), int(speed), dtstr
                    )
                )
        else:
            for speed, time, lon, lat in zip(
                speed_array, time_array, lon_array, lat_array
            ):
                # dtstr = time.strftime('%Y%m%d%H%M')
                dtstr = datetime.utcfromtimestamp(time).strftime("%Y%m%d%H%M")
                # if lon > 180:
                #     lon = lon - 360
                format_string = "{0:>6s}{1:>8.2f}{2:>8.2f}{3:>4d} {4:s}\n"
                if source_name == "SMAP" or source_name == "SMOS":
                    format_string = " {0:<6s} {1:>5.1f} {2:>5.1f} {3:>3d} {4:s}\n"
                fobj.write(
                    format_string.format(source_name, lat, lon, int(speed), dtstr)
                )
        output_products += [text_fname]

    ctime = datetime.fromtimestamp(os.stat(text_fname).st_ctime)
    LOG.info("    SUCCESS wrote out text windspeed file %s at %s", text_fname, ctime)

    for additional_text_fname in output_fnames:
        shutil.copy(text_fname, additional_text_fname)
        ctime = datetime.fromtimestamp(os.stat(additional_text_fname).st_ctime)
        LOG.info(
            "    SUCCESS wrote out text windspeed file %s at %s",
            additional_text_fname,
            ctime,
        )
        output_products += [additional_text_fname]
    return output_products
