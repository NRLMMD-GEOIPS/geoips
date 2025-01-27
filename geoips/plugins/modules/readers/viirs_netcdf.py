# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""VIIRS NetCDF reader.

This VIIRS reader is designed for reading the NPP/JPSS VIIRS files geoips.
The reader is only using the python functions and xarray variables.  Although
the file name indicates the data is in netcdf4 format.

Thus, the reader is based on the netcdf4 data format.

The orginal reader (viirs_aotcimss_ncdf4_reader.py) was developed for geoips1,
which applied many geoips1 function.

V1.0:  NRL-Monterey, 09/17/2020

VIIRS file infOrmation::

    There are 6 files for each time of VIIRS data, i.e.,
    For NASA NPP VIIRS
    20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02DNB.sdr.x.x.nc
    20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02IMG.sdr.x.x.nc
    20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02MOD.sdr.x.x.nc
    20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP03DNB.sdr.x.x.nc
    20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP03IMG.sdr.x.x.nc
    20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP03MOD.sdr.x.x.nc

    For JPSS VIIRS
    20200914.150000.npp.viirs.viirs_sips_jpss_uwssec_001.x.VJ102DNB.sdr.x.x.nc
    20200914.150000.npp.viirs.viirs_sips_jpss_uwssec_001.x.VJ102IMG.sdr.x.x.nc
    20200914.150000.npp.viirs.viirs_sips_jpss_uwssec_001.x.VJ102MOD.sdr.x.x.nc
    20200914.150000.npp.viirs.viirs_sips_jpss_uwssec_001.x.VJ103DNB.sdr.x.x.nc
    20200914.150000.npp.viirs.viirs_sips_jpss_uwssec_001.x.VJ103IMG.sdr.x.x.nc
    20200914.150000.npp.viirs.viirs_sips_jpss_uwssec_001.x.VJ103MOD.sdr.x.x.nc

    DNB: VIIRS day-night Band obs
    MOD: VIIRS M-Band  obs
    IMG: VIIRS I-Band  obs

The *.VNP02* files are for the data records, while the *.VNP03* files are for
the geolocation data records.

The xarray of geoips reader need both the data and lat/lon info. Thus, this
VIIRS reader is designed to read in the paired VNP02 and VNP03 files, depending
on any one of DNB or IMG or MOD file.  In order to minimize dupilcated excution
of VIIRS files, additional adjust of excution of the VIIRS files will be needed
(discussion with Mindy on how to do it).
"""
# Python Standard Libraries
from collections import defaultdict
from datetime import datetime
import logging
import os

# Third-Party Libraries
import numpy
import pandas as pd
import xarray as xr

# GeoIPS imports
from geoips.plugins.modules.readers.utils.geostationary_geolocation import get_indexes
from geoips.utils.context_managers import import_optional_dependencies

# If this reader is not installed on the system, don't fail altogether, just skip this
# import. This reader will not work if the import fails, and the package will have to be
# installed to process data of this type.
LOG = logging.getLogger(__name__)

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    import netCDF4 as ncdf


# @staticmethod                                     # not sure where it is uwas used?


VARLIST = {
    "DNB": ["DNB_observations"],
    "IMG": ["I04", "I05"],
    "IMG-Vis": ["I01", "I02", "I03"],
    "MOD": ["M07", "M08", "M10", "M11", "M12", "M13", "M14", "M15", "M16"],
    "MOD-Vis": ["M01", "M02", "M03", "M04", "M05", "M06", "M09"],
}

DNB_CHANNELS = ["DNB_observations"]
BT_CHANNELS = ["I04", "I05", "M12", "M13", "M14", "M15", "M16"]
REF_CHANNELS = [
    "I01",
    "I02",
    "I03",
    "M01",
    "M02",
    "M03",
    "M04",
    "M05",
    "M06",
    "M07",
    "M08",
    "M09",
    "M10",
    "M11",
]

# List of geolocation variables

GVARLIST = {
    "DNB": [
        "latitude",
        "longitude",
        "solar_zenith",
        "solar_azimuth",
        "sensor_zenith",
        "sensor_azimuth",
        "lunar_zenith",
        "moon_phase_angle",
    ],
    "IMG": [
        "latitude",
        "longitude",
        "solar_zenith",
        "solar_azimuth",
        "sensor_zenith",
        "sensor_azimuth",
    ],
    "IMG-Vis": [
        "latitude",
        "longitude",
        "solar_zenith",
        "solar_azimuth",
        "sensor_zenith",
        "sensor_azimuth",
    ],
    "MOD": [
        "latitude",
        "longitude",
        "solar_zenith",
        "solar_azimuth",
        "sensor_zenith",
        "sensor_azimuth",
    ],
    "MOD-Vis": [
        "latitude",
        "longitude",
        "solar_zenith",
        "solar_azimuth",
        "sensor_zenith",
        "sensor_azimuth",
    ],
}
xvarnames = {
    "solar_zenith": "solar_zenith_angle",
    "solar_azimuth": "solar_azimuth_angle",
    "sensor_zenith": "satellite_zenith_angle",
    "sensor_azimuth": "satellite_azimuth_angle",
    "lunar_zenith": "lunar_zenith_angle",
    "DNB_observations": "DNB",
}

# IMG:
#     I01(nline, npix): I-band 01 earth view reflectance (0-65527).
#                                                                 range of vlaues: 0 - 1
#                       add_offset=0,  scale_factor=1.9991758e-05,
#                       radiance_scale_factor=0.010167242, radiance_add_offset=0,
#                       radiance_units: Watts/meter^2/steradian/micrometer
#     I02(nline, npix): I-band 02 earth view reflectance (0-65527).
#                       add_offset=0,  scale_factor=1.9991758e-05,
#                       radiance_scale_factor=0.006007384, radiance_add_offset=0,
#                       radiance_units: Watts/meter^2/steradian/micrometer
#     I03(nline, npix): I-band 03 earth view reflectance (0-65527).
#                       add_offset=0,  scale_factor=1.9991758e-05,
#                       radiance_scale_factor=0.0015311801, radiance_add_offset=0,
#                       radiance_units: Watts/meter^2/steradian/micrometer
#     I04(nline, npix): I-band 04 earth view radiance (0-65527). need LUT for TB
#                                                                             conversion
#                       scale_factor=6.104354e-05, add_offset=0.0016703
#                       units: Watts/meter^2/steradian/micrometer
#                       I04_brightness_temperature_lut(65536). LUT[65535] is for
#                                                                          masked point.
#     I05(nline, npix): I-band 05 earth view radiance (0-65527). need LUT for TB
#                                                                             conversion
#                       scale_factor=0.0003815221, add_offset=0.141121
#                       units: Watts/meter^2/steradian/micrometer
#                       I05_brightness_temperature_lut(65536). LUT[65535] is for
#                                                                          masked point.
#     I04TB/I05TB     : associated TBs for I04/I05
#
#     Note: I04 and I05 converstion to TB will apply its TB conversion LUT. Since the
#                       change of TB is so small bewteen the LUT index, we just take
#                       value fo the I04/I05 as the LUT index (auto roundup) for easy
#                       process. This way will have an error of TB less than 0.05K.
#                       Otherwsie, a interpolation is needed for a more accurate TB.

# MOD:

#     M01 - M11(nline,npix):  M-band 01-11 earth view reflectance
#     M12 - M16(nline,npix):  M-band 12-16 earth view radiance. will convert radiance
#                                                                               anto TBs
#     M12TB-M16TB:         :  associated TBs for M12-16
#

#    Run plan:  fname has a list of VIIRS files (3 *02* or *03* files)

interface = "readers"
family = "standard"
name = "viirs_netcdf"
source_names = ["viirs"]


def _get_geolocation_metadata(orig_shape, fnames, xarray):
    """
    Gather all of the metadata used in creating geolocation data for input file.

    This is split out so we can easily create a chash of the data for creation
    of a unique filename. This allows us to avoid recalculation of angles that
    have already been calculated.
    """
    geomet = {}
    geomet["platform_name"] = "viirs"
    geomet["scene"] = "stitched_granules"
    # Just getting the nadir resolution in kilometers.  Must extract from a string.
    geomet["res_km"] = xarray.attrs["resolution_km"]
    geomet["roi_factor"] = 5  # roi = res * roi_factor, was 10
    geomet["num_lines"] = orig_shape[0]
    geomet["num_samples"] = orig_shape[1]
    geomet["fnames"] = fnames
    return geomet


def required_chan(chans, varnames):
    """Return True if required channel."""
    if chans is None:
        return True
    for varname in varnames:
        if varname in chans:
            return True
    return False


def required_geo_chan(xarrays, xvarname):
    """Return True if required geolocation channel."""
    # for data_type in list(xarrays.keys()):
    #     if xvarname in list(xarrays[data_type].keys()):
    #         LOG.info('        SKIPPING %s geolocation channel %s, xarray GEOLOCATION
    #                           variable %s exists', data_type, xvarname, xvarname)
    #         return False
    return True


def required_geo(chans, data_type):
    """Return True if required geolocation dataset."""
    if chans is None:
        return True
    for varname in chans:
        if (
            varname.replace("Ref", "").replace("Rad", "").replace("BT", "")
            in VARLIST[data_type]
        ):
            return True
        if (
            varname.replace("Ref", "").replace("Rad", "").replace("BT", "")
            + "_observations"
            in VARLIST[data_type]
        ):
            return True
    return False


def add_to_xarray(varname, nparr, xobj, dataset_masks, data_type, nparr_mask):
    """Add variable to xarray Dataset."""
    # Add current dataset to xarray object
    if varname not in xobj.variables:
        merged_array = nparr
    else:
        merged_array = numpy.vstack([xobj[varname].to_masked_array(), nparr])
    xobj[varname] = xr.DataArray(
        merged_array, dims=["dim_" + str(merged_array.shape[0]), "dim_1"]
    )

    # If nparr_mask.shape != nparr.shape, then it is "False" so create an
    # array of False the size of nparr
    if nparr_mask.shape != nparr.shape:
        nparr_mask = numpy.zeros(nparr.shape).astype(bool)
    # If we haven't merged nparr_mask into dataset_masks[data_type] yet, do it now
    if dataset_masks[data_type] is False:
        dataset_masks[data_type] = nparr_mask
    elif dataset_masks[data_type].shape != merged_array.shape:
        # This was previously only being applied to "BT_CHANNELS", which
        # caused the unprojected test scripts to fail (due to incorrect
        # shape of the final mask array).  Removing that check so ALL
        # variables are vstacked.
        dataset_masks[data_type] = numpy.vstack([dataset_masks[data_type], nparr_mask])


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    resample=False,
):
    """Read VIIRS netcdf data products.

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

    See Also
    --------
    :ref:`xarray_standards`
        Additional information regarding required attributes and variables
        for GeoIPS-formatted xarray Datasets.
    """
    # since fname is a LIST of input files, this reader needs additional adjustments to
    # read all files and put them into the XARRAY output (add one more array for
    # number of files)

    """
    fnames=['readers/data_viirs/20200916.081200.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02DNB.sdr.x.x.nc',\
           'readers/data_viirs/20200916.081200.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02IMG.sdr.x.x.nc',\
           'readers/data_viirs/20200916.081200.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02MOD.sdr.x.x.nc']

    fnames=['data_viirs/20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02DNB.sdr.x.x.nc',\
           'data_viirs/20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02IMG.sdr.x.x.nc',\
           'data_viirs/20200826.074800.npp.viirs.viirs_npp_nasaearthdata_x.x.VNP02MOD.sdr.x.x.nc']
    """

    # --------------- loop input files ---------------
    xarrays = {}
    dataset_masks = {}
    LOG.info("Requested Channels: %s", chans)

    tracked_data_type_vars = defaultdict(dict)
    # This fails if fnames happens to be in a different order
    for fname in sorted(fnames):
        # LOG.info('tst name= ', fname)

        # # chech for right VIIRS file
        # if 'viirs' in os.path.basename(fname):
        #     LOG.info('found a VIIRS file')
        # else:
        #     LOG.info('not a VIIRS file: skip it')
        #     raise

        # open the paired input files
        ncdf_file = ncdf.Dataset(str(fname), "r")

        LOG.info("    Trying file %s", fname)

        # *************** input VIRRS variables *****************

        # read IMG  or MOD  or DNB files

        # if data_type == 'IMG' or data_type == 'MOD' or data_type == 'DNB':

        # dict_var =dict.fromkeys(VARLIST[data_type])
        # dict_gvar=dict.fromkeys(GVARLIST[data_type])

        data_type = ncdf_file.product_name[5:8]

        if data_type not in dataset_masks:
            dataset_masks[data_type] = False
            xarrays[data_type] = xr.Dataset()
            xarrays[data_type].attrs["source_file_names"] = []

        #  ------  Time info for each pixel ------
        #  Start (end) time of VIIRS scan in seconds since 1/1/1993
        #  Python datetime64 time starts on '1970-01-01T00:00:00Z'
        #  Thus, 1/1/1993 datetime64 has seconds of 725846400
        #  The scan info does not match the line info of each fields (lines x pix)
        # thus, no tiemstamp is applied.  Just the Start_date and End_date are
        # sued for time info.

        scan_start_time = ncdf_file["scan_line_attributes"].variables[
            "scan_start_time"
        ][:]
        scan_end_time = ncdf_file["scan_line_attributes"].variables["scan_end_time"][:]

        # scan = ncdf_file.groups["scan_line_attributes"]
        # stime = scan.variables['scan_start_time'][:]
        # etime = scan.variables['scan_end_time'][:]

        s_time = scan_start_time + 725846400
        e_time = scan_end_time + 725846400

        # convert it to UTC time in format: datetime.datetime(2020, 8, 26, 7,
        #                                                     48, 10, 445420)
        Start_date = datetime.utcfromtimestamp(s_time[0])
        End_date = datetime.utcfromtimestamp(e_time[-1])

        #    ************  setup VIIRS xarray variables *****************
        #    only the avaialble fileds are arranged in the xaaray object
        #         the missing fields in the data file are not included.
        #         i.e, if I01-03 are missing the *IMG file, then only I04 and
        #              I05 fields will be processed and output to Xarray

        # from IPython import embed as shell

        xarrays[data_type].attrs["start_datetime"] = Start_date
        xarrays[data_type].attrs["end_datetime"] = End_date
        xarrays[data_type].attrs["source_name"] = "viirs"
        if ncdf_file.platform == "Suomi-NPP":
            xarrays[data_type].attrs["platform_name"] = "npp"
        if ncdf_file.platform == "JPSS-1":
            # xarrays[data_type].attrs['platform_name']  = 'jpss-1'
            # Attribute still lists JPSS-1, but operational satellite name is NOAA-20.
            xarrays[data_type].attrs["platform_name"] = "noaa-20"
        xarrays[data_type].attrs["data_provider"] = "NASA"
        if os.path.basename(fname) not in xarrays[data_type].attrs["source_file_names"]:
            xarrays[data_type].attrs["source_file_names"] += [os.path.basename(fname)]

        # MTIFs need to be "prettier" for PMW products, so 2km resolution for
        # final image
        xarrays[data_type].attrs["sample_distance_km"] = 2
        xarrays[data_type].attrs["interpolation_radius_of_influence"] = 3000

        if metadata_only is True:
            LOG.info(
                "metadata_only is True, reading only first file for metadata "
                "information and returning"
            )
            return {"METADATA": xarrays[data_type]}

        # check fo avaialble varaibles
        if "observation_data" in ncdf_file.groups.keys():
            list_vars = ncdf_file["observation_data"].variables.keys()
            ncdata = ncdf_file["observation_data"]
        if "geolocation_data" in ncdf_file.groups.keys():
            list_vars = ncdf_file["geolocation_data"].variables.keys()
            ncdata = ncdf_file["geolocation_data"]

        # Assign visible chans to own data_type, since they will disappear
        # from day -> night.
        # These are located in the VNP02MOD/IMG files, or the MOD dataset type
        # Also keep track of all variables in the parent file of the data_type
        # This will help determine if we need to add geolocation vars to the
        # data_type xarray downstream
        default_data_type = data_type
        vis_data_type = data_type + "-Vis"
        if Start_date not in tracked_data_type_vars[default_data_type]:
            tracked_data_type_vars[default_data_type][Start_date] = []
        tracked_data_type_vars[default_data_type][Start_date].extend(list(list_vars))
        if data_type in ["MOD", "IMG"]:
            if vis_data_type not in dataset_masks:
                dataset_masks[vis_data_type] = False
                xarrays[vis_data_type] = xr.Dataset()
                xarrays[vis_data_type].attrs["source_file_names"] = []
            xarrays[vis_data_type].attrs = xarrays[data_type].attrs
            geo_target_data_types = [default_data_type, vis_data_type]
            vis_vars = VARLIST[vis_data_type]
            if Start_date not in tracked_data_type_vars[vis_data_type]:
                tracked_data_type_vars[vis_data_type][Start_date] = []
            tracked_data_type_vars[vis_data_type][Start_date].extend(list(list_vars))
        else:
            geo_target_data_types = [default_data_type]
            vis_vars = []

        for var in list_vars:
            xvarname = var
            if var in xvarnames:
                xvarname = xvarnames[var]

            btvarname = xvarname + "BT"
            refvarname = xvarname + "Ref"
            radvarname = xvarname + "Rad"

            ncvar = ncdata.variables[var]

            if var in vis_vars:
                data_type = vis_data_type
            else:
                data_type = default_data_type

            # Need Rad in order to calculate DNB Ref variable.
            if var in DNB_CHANNELS and required_chan(chans, [radvarname, refvarname]):
                LOG.info(
                    "        Reading %s channel %s into DNB variable %s",
                    data_type,
                    var,
                    radvarname,
                )
                nparr = numpy.ma.masked_greater(ncvar[...], ncvar.valid_max)
                add_to_xarray(
                    radvarname,
                    nparr,
                    xarrays[data_type],
                    dataset_masks,
                    data_type,
                    nparr.mask,
                )
                for attrname in ncvar.ncattrs():
                    xarrays[data_type][radvarname].attrs[attrname] = ncvar.getncattr(
                        attrname
                    )

            # Apply Brightness Temperature conversions if BT version of variable was
            # requested.
            if (
                var in BT_CHANNELS + REF_CHANNELS
                and required_chan(chans, [btvarname])
                and var + "_brightness_temperature_lut" in ncdata.variables.keys()
            ):
                LOG.info(
                    "        Reading %s channel %s into BRIGHTNESS TEMPERATURE "
                    "variable %s",
                    data_type,
                    var,
                    btvarname,
                )
                btlut = ncdata.variables[var + "_brightness_temperature_lut"][...]
                ncvar.set_auto_maskandscale(False)
                unscaled_rad = ncvar[...]
                nparr = btlut[unscaled_rad]
                add_to_xarray(
                    btvarname,
                    nparr,
                    xarrays[data_type],
                    dataset_masks,
                    data_type,
                    nparr.mask,
                )
                xarrays[data_type][btvarname].attrs["units"] = "Kelvin"

            if (
                var in BT_CHANNELS + REF_CHANNELS
                and required_chan(chans, [radvarname])
                and "radiance_add_offset" in ncvar.ncattrs()
            ):
                LOG.info(
                    "        Reading %s channel %s into RADIANCE variable %s",
                    data_type,
                    var,
                    radvarname,
                )

                ncvar.set_auto_maskandscale(True)

                # Bowtie correction
                nparr_bowtie = numpy.ma.masked_equal(ncvar[...].data, 65533)

                nparr_masked = numpy.ma.masked_greater(
                    ((ncvar[...] - ncvar.add_offset) / ncvar.scale_factor)
                    * ncvar.radiance_scale_factor
                    + ncvar.radiance_add_offset,
                    ncvar.valid_max * ncvar.radiance_scale_factor
                    + ncvar.radiance_add_offset,
                )

                add_to_xarray(
                    radvarname,
                    nparr_masked,
                    xarrays[data_type],
                    dataset_masks,
                    data_type,
                    nparr_bowtie.mask,
                )

                for attrname in ncvar.ncattrs():
                    xarrays[data_type][radvarname].attrs[attrname] = ncvar.getncattr(
                        attrname
                    )

            if var in REF_CHANNELS and required_chan(chans, [refvarname]):
                LOG.info(
                    "        Reading %s channel %s into REFLECTANCE variable %s",
                    data_type,
                    var,
                    refvarname,
                )

                nparr_bowtie = numpy.ma.masked_equal(ncvar[...].data, 65533)

                nparr_masked = numpy.ma.masked_greater(
                    ncvar[...], ncvar.valid_max * ncvar.scale_factor + ncvar.add_offset
                )

                # Gamma, Scale factor from old Vis product
                from geoips.data_manipulations.corrections import (
                    apply_gamma,
                    apply_scale_factor,
                )

                nparr_masked = apply_gamma(nparr_masked, 1.5)
                nparr_masked = apply_scale_factor(nparr_masked, 100)

                add_to_xarray(
                    refvarname,
                    nparr_masked,
                    xarrays[data_type],
                    dataset_masks,
                    data_type,
                    nparr_bowtie.mask,
                )

            for geo_target_data_type in geo_target_data_types:
                if var in GVARLIST[geo_target_data_type] and required_geo(
                    chans, geo_target_data_type
                ):
                    source_file_vars = tracked_data_type_vars[geo_target_data_type][
                        Start_date
                    ]
                    if geo_target_data_type == vis_data_type and not all(
                        [x in source_file_vars for x in vis_vars]
                    ):
                        # Only add geolocation to vis_data_type if corresponding
                        # channels are in the source file
                        continue
                    xvarname = var
                    if var in xvarnames:
                        xvarname = xvarnames[var]

                    if not required_geo_chan(xarrays, xvarname):
                        continue

                    LOG.info(
                        "        Reading %s geolocation channel %s into GEOLOCATION "
                        "variable %s",
                        geo_target_data_type,
                        var,
                        xvarname,
                    )
                    nparr = numpy.ma.masked_equal(ncvar[...], ncvar._FillValue)
                    add_to_xarray(
                        xvarname,
                        nparr,
                        xarrays[geo_target_data_type],
                        dataset_masks,
                        geo_target_data_type,
                        nparr.mask,
                    )
                    for attrname in ncvar.ncattrs():
                        xarrays[geo_target_data_type][xvarname].attrs[attrname] = (
                            ncvar.getncattr(attrname)
                        )

        # LongName is something like:
        # 'VIIRS/JPSS1 Day/Night Band 6-Min L1B Swath SDR 750m NRT'
        # or
        # 'VIIRS/NPP Day/Night Band 6-Min L1B Swath 750m'
        long_name_parts = ncdf_file.LongName.split(" ")
        if long_name_parts[-1] == "NRT":
            resolution_m = long_name_parts[-2]
        else:
            resolution_m = long_name_parts[-1]
        resolution_m = int(resolution_m.replace("m", ""))
        LOG.info("Resolution: %s", resolution_m)
        xarrays[data_type].attrs["resolution_km"] = resolution_m / 1000.0

        # close the files
        ncdf_file.close()

    # Geolocation resampling
    if resample and area_def:
        adname = area_def.area_id
        new_shape = area_def.shape

        LOG.info("")
        LOG.info("Getting geolocation information for {}.".format(adname))

        for dtype in xarrays.keys():
            if "latitude" not in xarrays[dtype].variables:
                LOG.info(
                    "No data read for dataset %s, removing from xarray list", dtype
                )
                continue
            fldk_lats = xarrays[dtype]["latitude"]
            fldk_lons = xarrays[dtype]["longitude"]
            # Get just the metadata we need
            geo_metadata = _get_geolocation_metadata(
                fldk_lats.shape, fnames, xarrays[dtype]
            )
            lines, samples = get_indexes(geo_metadata, fldk_lats, fldk_lons, area_def)

            index_mask = lines != -999

            new_dim0 = "dim_{:d}".format(new_shape[0])
            new_dim1 = "dim_{:d}".format(new_shape[1])

            # Resample the mask
            old_dataset_masks = dataset_masks[dtype]
            dataset_masks[dtype] = numpy.full(new_shape, True)
            dataset_masks[dtype][index_mask] = old_dataset_masks[
                lines[index_mask], samples[index_mask]
            ]

            for varname in xarrays[dtype].variables.keys():
                new_var = numpy.full(new_shape, -999.1)
                new_var[index_mask] = xarrays[dtype][varname].values[
                    lines[index_mask], samples[index_mask]
                ]
                if varname not in list(xvarnames.values()) + ["latitude", "longitude"]:
                    # Set values <= -999.9 to NaN so they also get interpolated.
                    new_var[numpy.where(new_var <= -999.9)] = numpy.nan
                    # Interpolate missing data.
                    out_var = numpy.array(pd.DataFrame(new_var).interpolate())
                    # Reset the mask so these values get shown.
                    skip_mask = numpy.where(
                        numpy.isnan(new_var) & ~numpy.isnan(out_var)
                    )
                    dataset_masks[dtype][skip_mask] = False
                else:
                    out_var = new_var
                xarrays[dtype][varname] = xr.DataArray(
                    out_var, dims=[new_dim0, new_dim1]
                )

        LOG.interactive("Done with geolocation for {}".format(adname))
        LOG.info("")

    # Clean up the final xarray dictionary
    xarray_returns = {}
    for dtype in xarrays.keys():
        if "latitude" not in xarrays[dtype].variables:
            LOG.info("No data read for dataset %s, removing from xarray list", dtype)
            continue
        for varname in xarrays[dtype].variables.keys():
            xarrays[dtype][varname] = xarrays[dtype][varname].where(
                ~dataset_masks[dtype]
            )
        if "DNBRad" in list(xarrays[dtype].variables.keys()) and required_chan(
            chans, ["DNBRef"]
        ):
            with import_optional_dependencies(loglevel="info"):
                """Attempt to import a package log to INFO if the import fails."""
                from lunarref.lib.liblunarref import lunarref

                lunarref_data = lunarref(
                    xarrays["DNB"]["DNBRad"].to_masked_array(),
                    xarrays["DNB"]["solar_zenith_angle"].to_masked_array(),
                    xarrays["DNB"]["lunar_zenith_angle"].to_masked_array(),
                    xarrays["DNB"].start_datetime.strftime("%Y%m%d%H"),
                    xarrays["DNB"].start_datetime.strftime("%M"),
                    xarrays["DNB"]["moon_phase_angle"].mean(),
                )
                lunarref_data = numpy.ma.masked_less_equal(
                    lunarref_data, -999, copy=False
                )
                xarrays["DNB"]["DNBRef"] = xr.DataArray(
                    lunarref_data, dims=xarrays["DNB"]["DNBRad"].dims
                )
        # This will not duplicate memory - reference
        xarray_returns[dtype] = xarrays[dtype]

    # Force masking of latitude/longitude fill values, otherwise causes issues
    # when sectoring
    # fill_value = -999.9
    for dtype in xarray_returns:
        bad_llmask = xarray_returns[dtype]["latitude"] == -999.9
        for var in xarray_returns[dtype].variables.keys():
            xarray_returns[dtype][var] = xarray_returns[dtype][var].where(~bad_llmask)

    xarray_returns["METADATA"] = list(xarray_returns.values())[0][[]]

    return xarray_returns
