# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""MODIS HDF4 reader.

This reader is designed for geoips for importing MODIS data files in hdf4 format
Example files are::

    AQUA:      MYD files
         MYD021KM.A2021004.2005.061.NRT.hdf
         MYD03.A2021004.2005.061.NRT.hdf
         MYD14.A2021004.2005.006.NRT.hdf
    Terra:     MOD files
         MOD021KM.A2021004.2005.061.NRT.hdf
         MOD02HKM.A2021004.2005.061.NRT.hdf
         MOD02QKM.A2021004.2005.061.NRT.hdf
         MOD03.A2021004.2005.061.NRT.hdf
         MOD14.A2021004.2005.006.NRT.hdf

The MOD03 and MOD14 files have the geolocation (lat/lon) and sensor geoometry
infomation, while other files have values at each channels.
"""
# Python Standard Libraries
from datetime import datetime
import logging
from os.path import basename

# Third-Party Libraries
import numpy as np
import xarray as xr

# GeoIPS imports
from geoips.utils.context_managers import import_optional_dependencies

LOG = logging.getLogger(__name__)

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    from pyhdf.HDF import ishdf
    from pyhdf.SD import SD, SDC
    from pyhdf.error import HDF4Error

LOG.info("info on imported functions")

interface = "readers"
family = "standard"
name = "modis_hdf4"
source_names = ["modis"]

# define functions


def parse_metadata(metadatadict):
    """Parse MODIS metadata dictionary."""
    metadata = {}
    for ii in metadatadict.keys():
        # metadata passed by reference - add to it in subroutines.
        if ii == "CoreMetadata.0":
            parse_core_metadata(metadata, metadatadict["CoreMetadata.0"])
        elif ii == "ArchiveMetadata.0":
            parse_archive_metadata(metadata, metadatadict["ArchiveMetadata.0"])
        elif ii == "StructMetadata.0":
            parse_struct_metadata(metadata, metadatadict["StructMetadata.0"])
        else:
            metadata[ii] = metadatadict[ii]
    return metadata


def parse_struct_metadata(metadata, metadatastr):
    """Parse metadata struct."""
    pass


def parse_core_metadata(metadata, metadatastr):
    """Parse core metadata."""
    ii = 0
    lines = metadatastr.split("\n")
    # The HDF4 structure is stored as a big text string in
    # ArchiveMetadata.0, StructMetadata.0, and CoreMetadata.0
    # dictionary entries.  Parsing out the values we need from
    # CoreMetadata.0
    for line in lines:
        # We want to skip END_OBJECT, and only match OBJECT tags. So put a ' '
        # in front of OBJECT Get the value 2 lines past the opening tag
        # (that is the actual value) Remove white space and "s

        # Lines like:
        # '      OBJECT                 = ASSOCIATEDINSTRUMENTSHORTNAME'
        # Skip anything that does not fit that format
        try:
            [typ, field] = [piece.strip() for piece in line.split("=")]
        except ValueError:
            ii += 1
            continue
        for currval in [
            "RANGEENDINGDATE",
            "RANGEBEGINNINGDATE",
            "DAYNIGHTFLAG",
            "SHORTNAME",
        ]:
            if "OBJECT" == typ and currval == field:
                metadata[currval] = lines[ii + 2].split("=")[1].replace('"', "").strip()

        # Also remove the trailing .0000000 from times.
        for currval in ["RANGEBEGINNINGTIME", "RANGEENDINGTIME"]:
            if "OBJECT" == typ and " = " + currval in line:
                metadata[currval] = (
                    lines[ii + 2].split("=")[1].strip().replace('"', "").split(".")[0]
                )

        # These have 'CLASS' in addition to 'NUMVAL' between OBJECT and VALUE.
        # So have to do ii+3
        for currval in ["ASSOCIATEDSENSORSHORTNAME", "ASSOCIATEDPLATFORMSHORTNAME"]:
            if "OBJECT" == typ and currval == field:
                metadata[currval] = lines[ii + 3].split("=")[1].strip().replace('"', "")
        ii += 1


def parse_archive_metadata(metadata, metadatastr):
    """Parse archive metadata."""
    lines = metadatastr.split("\n")
    ii = 0

    # The HDF4 structure is stored as a big text string in
    # ArchiveMetadata.0, StructMetadata.0, and CoreMetadata.0
    # dictionary entries.  Parsing out the values we need from
    # ArchiveMetadata.0
    for line in lines:
        for currattr in [
            "EASTBOUNDINGCOORDINATE",
            "NORTHBOUNDINGCOORDINATE",
            "SOUTHBOUNDINGCOORDINATE",
            "WESTBOUNDINGCOORDINATE",
        ]:
            if " OBJECT" in line and currattr in line:
                # Get the value 2 lines past the opening tag (that is the
                # actual value) Remove white space
                metadata[currattr] = lines[ii + 2].split("=")[1].strip()
        ii += 1


def add_to_xarray(varname, nparr, xobj, cumulative_mask, data_type):
    """Add variable to xarray Dataset."""
    # cumulative_mask is not the best name for this variable. It is used for mask info
    # of field 'varname' so that is not actually a comulative mask. It should be a mask
    # for each variable.
    LOG.info("ADDING %s to xobj", varname)
    if varname not in xobj.variables:
        xobj[varname] = xr.DataArray(nparr)
    else:
        merged_array = np.vstack([xobj[varname].to_masked_array(), nparr])
        xobj[varname] = xr.DataArray(
            merged_array, dims=["dim_" + str(merged_array.shape[0]), "dim_1"]
        )
        cumulative_mask[varname] = xr.DataArray(
            xobj[varname].to_masked_array().mask,
            dims=["dim_" + str(merged_array.shape[0]), "dim_1"],
        )

    # add mask info for 'varname'
    if varname not in list(cumulative_mask.variables.keys()):
        cumulative_mask[varname] = xr.DataArray(xobj[varname].to_masked_array().mask)
    elif cumulative_mask[varname].shape == xobj[varname].shape:
        cumulative_mask[varname] = (
            cumulative_mask[varname] | xobj[varname].to_masked_array().mask
        )


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read MODIS Aqua and Terra hdf data files.

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
    dataset_info = {
        "1KM": [
            "chan20.0Rad",  # emissive 3.750 sfc/cld temp
            "chan21.0Rad",  # emissive 3.750 sfc/cld temp
            "chan22.0Rad",  # emissive 3.959 sfc/cld temp
            "chan23.0Rad",  # emissive 4.050 sfc/cld temp
            "chan24.0Rad",  # emissive 4.465 atm temperature
            "chan25.0Rad",  # emissive 4.515 atm temperature
            "chan27.0Rad",  # emissive 6.715 water vapor
            "chan28.0Rad",  # emissive 7.325 water vapor
            "chan29.0Rad",  # emissive 8.55 sfc/cld temp
            "chan30.0Rad",  # emissive 9.73 ozone
            "chan31.0Rad",  # emissive 11.03 sfc/cld temp
            "chan32.0Rad",  # emissive 12.02 sfc/cld temp
            "chan33.0Rad",  # emissive 13.335 cld top properties
            "chan34.0Rad",  # emissive 13.635 cld top properties
            "chan35.0Rad",  # emissive 13.935 cld top properties
            "chan36.0Rad",  # emissive 14.235 cld top properties
            "chan20.0BT",  # emissive 3.750 sfc/cld temp
            "chan21.0BT",  # emissive 3.750 sfc/cld temp
            "chan22.0BT",  # emissive 3.959 sfc/cld temp
            "chan23.0BT",  # emissive 4.050 sfc/cld temp
            "chan24.0BT",  # emissive 4.465 atm temperature
            "chan25.0BT",  # emissive 4.515 atm temperature
            "chan27.0BT",  # emissive 6.715 water vapor
            "chan28.0BT",  # emissive 7.325 water vapor
            "chan29.0BT",  # emissive 8.55 sfc/cld temp
            "chan30.0BT",  # emissive 9.73 ozone
            "chan31.0BT",  # emissive 11.03 sfc/cld temp
            "chan32.0BT",  # emissive 12.02 sfc/cld temp
            "chan33.0BT",  # emissive 13.335 cld top properties
            "chan34.0BT",  # emissive 13.635 cld top properties
            "chan35.0BT",  # emissive 13.935 cld top properties
            "chan36.0BT",  # emissive 14.235 cld top properties
        ],
        "Fire_Mask": [
            "fire_mask",
        ],
        "HKM": [
            "chan3.0Rad",  # reflective 0.470 land/cld properties
            "chan4.0Rad",  # reflective 0.555 land/cld properties
            "chan5.0Rad",  # reflective 1.24 land/cld properties
            "chan6.0Rad",  # reflective 1.64 land/cld properties
            "chan7.0Rad",  # reflective 2.13 land/cld properties
            "chan16.0Rad",  # reflective 1.64 land/cld properties
            "chan3.0Ref",  # reflective 0.470 land/cld properties
            "chan4.0Ref",  # reflective 0.555 land/cld properties
            "chan5.0Ref",  # reflective 1.24 land/cld properties
            "chan6.0Ref",  # reflective 1.64 land/cld properties
            "chan7.0Ref",  # reflective 2.13 land/cld properties
            "chan16.0Ref",  # reflective 1.64 land/cld properties
        ],
        "QKM": [
            "chan1.0Rad",  # reflective 0.645 land/cld boundaries
            "chan2.0Rad",  # reflective 0.865 land/cld boundaries
            "chan1.0Ref",  # reflective 0.645 land/cld boundaries
            "chan2.0Ref",  # reflective 0.865 land/cld boundaries
        ],
    }
    # @staticmethod

    # from pyhdf.SD import SD, SDC
    # from pyhdf.SD import *

    # fnames=['MYD021KM.A2021004.2005.061.NRT.hdf','MYD03.A2021004.2005.061.NRT.hdf']
    # fnames=['MYD14.A2021004.2005.006.NRT.hdf']
    # fnames=['MYD021KM.A2021004.2005.061.NRT.hdf','MYD03.A2021004.2005.061.NRT.hdf',
    #         'MYD14.A2021004.2005.006.NRT.hdf']

    # process of reading the data
    xarrays = {}
    cumulative_mask = {}  # name of xarray for mask info of all variables
    datapaths = []
    datasettag = ""
    corrections = {}
    corrections_ref = {"aqua": {}, "terra": {}}

    for fname in fnames:  # Loop MODIS files
        LOG.info("Reading file %s", fname)

        # check for a right input MODIS data file
        if ishdf(fname):
            try:
                mf = SD(fname, SDC.READ)
            except HDF4Error:
                LOG.info("wrong input hdf file %s", fname)
                raise

        mf = SD(fname, SDC.READ)
        mf_metadata = parse_metadata(mf.attributes())

        # If start/end datetime happen to vary, adjust here.
        sdt = datetime.strptime(
            mf_metadata["RANGEBEGINNINGDATE"] + mf_metadata["RANGEBEGINNINGTIME"],
            "%Y-%m-%d%H:%M:%S",
        )
        edt = datetime.strptime(
            mf_metadata["RANGEENDINGDATE"] + mf_metadata["RANGEENDINGTIME"],
            "%Y-%m-%d%H:%M:%S",
        )
        cname = mf_metadata["SHORTNAME"]
        xarrays["METADATA"] = xr.Dataset()
        xarrays["METADATA"].attrs["start_datetime"] = sdt
        xarrays["METADATA"].attrs["end_datetime"] = edt
        xarrays["METADATA"].attrs["source_name"] = "modis"
        xarrays["METADATA"].attrs["platform_name"] = mf_metadata[
            "ASSOCIATEDPLATFORMSHORTNAME"
        ].lower()
        xarrays["METADATA"].attrs["data_provider"] = "nasa"
        xarrays["METADATA"].attrs["source_file_names"] = [basename(fname)]
        xarrays["METADATA"].attrs["sample_distance_km"] = 2  # ????
        xarrays["METADATA"].attrs["interpolation_radius_of_influence"] = 3000  # ???
        if metadata_only:
            return xarrays

        if "MOD02QKM" == cname or "MYD02QKM" == cname:
            datapaths = ["EV_250_RefSB"]
            chanlocspaths = ["Band_250M"]
            datasettag = "QKM"
            if datasettag not in cumulative_mask:
                cumulative_mask[datasettag] = xr.Dataset()
                xarrays[datasettag] = xr.Dataset()
                xarrays[datasettag].attrs["source_file_names"] = []
            # corrections_ref[0] = scale
            # corrections_ref[1] = offset
            corrections_ref["aqua"] = {
                "chan1.0": [0.00201941, 0],
                "chan2.0": [0.00327573, 0],
            }
            corrections_ref["terra"] = {
                "chan1.0": [0.00201509, 0],
                "chan2.0": [0.00326201, 0],
            }
        if "MOD02HKM" == cname or "MYD02HKM" == cname:
            datapaths = ["EV_500_RefSB"]
            chanlocspaths = ["Band_500M"]
            datasettag = "HKM"
            if datasettag not in cumulative_mask:
                cumulative_mask[datasettag] = xr.Dataset()
                xarrays[datasettag] = xr.Dataset()
                xarrays[datasettag].attrs["source_file_names"] = []
            # corrections_ref[0] = scale
            # corrections_ref[1] = offset
            corrections_ref["aqua"] = {
                "chan3.0": [0.00155510, 0],
                "chan4.0": [0.00174094, 0],
                "chan5.0": [0.00683729, 0],
                "chan6.0": [0.0134965, 0],
                "chan7.0": [0.0359228, -0],
            }
            corrections_ref["terra"] = {
                "chan3.0": [0.00155013, 0],
                "chan4.0": [0.00173456, 0],
                "chan5.0": [0.00682327, 0],
                "chan6.0": [0.0134728, 0],
                "chan7.0": [0.0358326, -0],
            }
        if "MOD14" == cname or "MYD14" == cname:
            datasettag = "Fire_Mask"
            if datasettag not in cumulative_mask:
                cumulative_mask[datasettag] = xr.Dataset()
                xarrays[datasettag] = xr.Dataset()
                xarrays[datasettag].attrs["source_file_names"] = []
        if "MOD021KM" == cname or "MYD021KM" == cname:
            datapaths = ["EV_1KM_RefSB", "EV_1KM_Emissive"]
            datasettag = "1KM"
            chanlocspaths = ["Band_1KM_RefSB", "Band_1KM_Emissive"]
            if datasettag not in cumulative_mask:
                cumulative_mask[datasettag] = xr.Dataset()
                xarrays[datasettag] = xr.Dataset()
                xarrays[datasettag].attrs["source_file_names"] = []
            # corrections_ref[0] = scale
            # corrections_ref[1] = offset
            corrections_ref["aqua"] = {
                "chan8.0": [0.00185801, 0],
                "chan9.0": [0.00170356, 0],
                "chan10.0": [0.00164244, 0],
                "chan11.0": [0.00172248, 0],
                "chan12.0": [0.00171558, 0],
                "chan13.0": [0.00209848, 0],
                "chan13.5": [0.00209848, -0],
                "chan14.0": [0.00215609, 0],
                "chan14.5": [0.00215609, 0],
                "chan15.0": [0.00250819, 0],
                "chan16.0": [0.00333670, 0],
                "chan17.0": [0.00347492, 0],
                "chan18.0": [0.00372233, 0],
                "chan19.0": [0.00371927, 0],
                "chan26.0": [0.00889511, 0],
            }
            corrections_ref["terra"] = {
                "chan8.0": [0.00185398, 0],
                "chan9.0": [0.00170009, 0],
                "chan10.0": [0.00163386, 0],
                "chan11.0": [0.00171776, 0],
                "chan12.0": [0.00171045, 0],
                "chan13.0": [0.00209057, 0],
                "chan13.5": [0.00209057, -0],
                "chan14.0": [0.00214607, 0],
                "chan14.5": [0.00214607, 0],
                "chan15.0": [0.00249967, 0],
                "chan16.0": [0.00332639, 0],
                "chan17.0": [0.00346232, 0],
                "chan18.0": [0.00370446, 0],
                "chan19.0": [0.00370657, -0],
                "chan26.0": [0.00886857, 0],
            }
            # corrections[chan][0] = (ems1km_um) effective central wavelength in microns
            # corrections[chan][1] = (tcs1km) temperature correction slope
            # corrections[chan][2] = (tci1km) temperature correction intercept
            corrections = {
                "chan20.0": [3.7853, 9.993411e-01, 4.770532e-01],
                "chan21.0": [3.9916, 9.998646e-01, 9.262664e-02],
                "chan22.0": [3.9714, 9.998584e-01, 9.757996e-02],
                "chan23.0": [4.0561, 9.998682e-01, 8.929242e-02],
                "chan24.0": [4.4726, 9.998819e-01, 7.310901e-02],
                "chan25.0": [4.5447, 9.998845e-01, 7.060415e-02],
                "chan27.0": [6.7661, 9.994877e-01, 2.204921e-01],
                "chan28.0": [7.3382, 9.994918e-01, 2.046087e-01],
                "chan29.0": [8.5238, 9.995495e-01, 1.599191e-01],
                "chan30.0": [9.7303, 9.997398e-01, 8.253401e-02],
                "chan31.0": [11.0121, 9.995608e-01, 1.302699e-01],
                "chan32.0": [12.0259, 9.997256e-01, 7.181833e-02],
                "chan33.0": [13.3629, 9.999160e-01, 1.972608e-02],
                "chan34.0": [13.6818, 9.999167e-01, 1.913568e-02],
                "chan35.0": [13.9108, 9.999191e-01, 1.817817e-02],
                "chan36.0": [14.1937, 9.999281e-01, 1.583042e-02],
            }

        # Lat/Lons found in 1km data file appears to be downsampled to 406x271,
        # the lat/lons in MOD03 file are full 1km resolution. hkm and 1km data
        # files appear to have full 1km resolution also (2030x1354)
        # Also, the python resize function appears to just replicate the data,
        # and not interpolate. Which is not what we want.
        if cname == "MOD03" or cname == "MYD03":
            scifile_names = {
                "Latitude": "latitude",
                "Longitude": "longitude",
                "SolarZenith": "solar_zenith_angle",
                "SensorZenith": "satellite_zenith_angle",
                "SolarAzimuth": "solar_azimuth_angle",
                "SensorAzimuth": "satellite_azimuth_angle",
            }

            for datasettag in dataset_info.keys():  # loop the data_type
                #  create a xarray for a data_type if it does not exist
                if datasettag not in cumulative_mask:
                    cumulative_mask[datasettag] = xr.Dataset()
                    xarrays[datasettag] = xr.Dataset()
                    xarrays[datasettag].attrs["source_file_names"] = []

                for (
                    currvar
                ) in scifile_names.keys():  # loop variables assocaited with geo-info
                    sfgvar = scifile_names[currvar]  # name of a field
                    select_data = mf.select(currvar)  # select this field
                    attrs = select_data.attributes()  # get attributes of this field
                    data = select_data.get()  # get the all data of this field

                    # for datasettag in dataset_info.keys():  # loop the data_type
                    # Checking if we need this resolution based on requested
                    # channels
                    if not chans or list(set(chans) & set(dataset_info[datasettag])):
                        LOG.info("    adding " + datasettag + " " + currvar)
                        pass
                    else:
                        continue

                    outdata = data
                    if datasettag == "QKM" or datasettag == "HKM":
                        #  create a xarray for a datasettag if it does not exist
                        # if datasettag not in cumulative_mask:
                        #    cumulative_mask[datasettag] = False
                        #    xarrays[datasettag] = xr.Dataset()

                        factor = 2
                        if datasettag == "QKM":
                            factor = 4
                        outdata = np.zeros(
                            (len(data) * factor, data.shape[1] * factor), data.dtype
                        )
                        x = np.arange(data.shape[0])
                        y = np.arange(data.shape[1])
                        xx = np.linspace(x.min(), x.max(), outdata.shape[0])
                        yy = np.linspace(y.min(), y.max(), outdata.shape[1])
                        from scipy.interpolate import RectBivariateSpline

                        # x, y: 1-D array of coordinate in strickly ascending order
                        # kx, ky (integer,optional): degrees of the bivariate Spline.
                        #                                                   Default is 3
                        # s (float, optional): positive smoothing facter defined for
                        #                     estimation condition. Deault is 0
                        newKernel = RectBivariateSpline(x, y, data, kx=2, ky=2)
                        outdata = newKernel(xx, yy)
                    # Appears lat/lon does not need to be *.01, and
                    # Zenith/Azimuth do. These scale_factors are hard coded
                    # because I can't seem to easily pull them out of the big
                    # text metadata string.
                    factor = 1
                    if "scale_factor" in attrs.keys():
                        factor = attrs["scale_factor"]
                    masked_data = np.ma.masked_equal(
                        np.ma.array(outdata * factor), attrs["_FillValue"]
                    )
                    # variables get propagated to top level in scifile object.
                    # geolocation_variables do not since azimuth/zenith need
                    # to be calculated for each resolution, need to be in
                    # Read lat/lons directly from MOD14.
                    add_to_xarray(
                        sfgvar,
                        masked_data,
                        xarrays[datasettag],
                        cumulative_mask[datasettag],
                        datasettag,
                    )
                    for attrname in attrs:  # add attributes
                        xarrays[datasettag][sfgvar].attrs[attrname] = attrs[attrname]

                # Add attributes
                xarrays[datasettag].attrs["start_datetime"] = sdt
                xarrays[datasettag].attrs["end_datetime"] = edt
                xarrays[datasettag].attrs["source_name"] = "modis"
                xarrays[datasettag].attrs["platform_name"] = mf_metadata[
                    "ASSOCIATEDPLATFORMSHORTNAME"
                ].lower()
                xarrays[datasettag].attrs["data_provider"] = "nasa"
                if (
                    basename(fname)
                    not in xarrays[datasettag].attrs["source_file_names"]
                ):
                    xarrays[datasettag].attrs["source_file_names"] += [basename(fname)]
                xarrays[datasettag].attrs["sample_distance_km"] = 2  # ????
                xarrays[datasettag].attrs[
                    "interpolation_radius_of_influence"
                ] = 3000  # ???

        # elif ('MOD14' == cname or 'MYD14' == cname) and 'fire_mask' in chans:
        elif "MOD14" == cname or "MYD14" == cname:
            # Put shell statement here to figure out how to correct fire_mask
            fire_mask = mf.select("fire mask").get()
            masked_data = np.ma.masked_less(np.ma.array(fire_mask), 7)
            add_to_xarray(
                "fire_mask",
                masked_data,
                xarrays[datasettag],
                cumulative_mask[datasettag],
                datasettag,
            )
            scifile_names = {
                "Latitude": "latitude",
                "Longitude": "longitude",
            }
            # Read lat/lons directly out of MOD14 file, don't need satzenith,etc

            for currvar in scifile_names.keys():
                sfgvar = scifile_names[currvar]
                try:
                    select_data = mf.select(currvar)  # select this field
                except HDF4Error:
                    LOG.warning("SKIPPING %s does not exist in %s", currvar, datasettag)
                    continue
                attrs = select_data.attributes()  # get attributes of this field
                data = select_data.get()  # get the all data of this field
                # data = mf.select(currvar).get()

                add_to_xarray(
                    sfgvar,
                    data,
                    xarrays[datasettag],
                    cumulative_mask[datasettag],
                    datasettag,
                )
                for attrname in attrs:  # add attributes
                    xarrays[datasettag][sfgvar].attrs[attrname] = attrs[attrname]

            # Add attributes
            xarrays[datasettag].attrs["start_datetime"] = sdt
            xarrays[datasettag].attrs["end_datetime"] = edt
            xarrays[datasettag].attrs["source_name"] = "modis"
            xarrays[datasettag].attrs["platform_name"] = mf_metadata[
                "ASSOCIATEDPLATFORMSHORTNAME"
            ].lower()
            xarrays[datasettag].attrs["data_provider"] = "nasa"
            if basename(fname) not in xarrays[datasettag].attrs["source_file_names"]:
                xarrays[datasettag].attrs["source_file_names"] += [basename(fname)]
            xarrays[datasettag].attrs["sample_distance_km"] = 2  # ????
            xarrays[datasettag].attrs["interpolation_radius_of_influence"] = 3000  # ???
        else:
            for ii in range(len(datapaths)):
                datapath = datapaths[ii]
                chanlocspath = chanlocspaths[ii]
                select_alldata = mf.select(datapath)
                chanlocs = mf.select(chanlocspath).get()

                alldata = select_alldata.get()
                attrs = select_alldata.attributes()

                for jj in range(len(chanlocs)):
                    channame = "chan" + str(chanlocs[jj])
                    if (
                        not chans
                        or channame + "Rad" in chans
                        or channame + "Ref" in chans
                        or channame + "BT" in chans
                    ):
                        pass
                    else:
                        continue

                    ind = jj
                    if len(attrs["radiance_offsets"]) == 1:
                        ind = 0
                    data = (alldata[jj] - attrs["radiance_offsets"][ind]) * attrs[
                        "radiance_scales"
                    ][ind]
                    masked_data = np.ma.masked_equal(
                        np.ma.array(data), attrs["_FillValue"]
                    )
                    masked_data = np.ma.masked_greater(
                        masked_data, attrs["valid_range"][1]
                    )
                    masked_data = np.ma.masked_less(
                        masked_data, attrs["valid_range"][0]
                    )

                    LOG.info(
                        "    Adding channame: "
                        + str(channame + "Rad")
                        + " offset: "
                        + str(attrs["radiance_offsets"][ind])
                        + " scale: "
                        + str(attrs["radiance_scales"][ind])
                    )
                    add_to_xarray(
                        channame + "Rad",
                        masked_data,
                        xarrays[datasettag],
                        cumulative_mask[datasettag],
                        datasettag,
                    )
                    for attrname in attrs:  # add attributes
                        xarrays[datasettag][channame + "Rad"].attrs[attrname] = attrs[
                            attrname
                        ]

                    if channame in corrections.keys():
                        cor = corrections[channame]
                        h = 6.626176e-34
                        c = 2.99792458e8
                        bc = 1.380658e-23

                        data1 = np.log(
                            1
                            + 2
                            * h
                            * c
                            * c
                            / (
                                cor[0]
                                * cor[0]
                                * cor[0]
                                * cor[0]
                                * cor[0]
                                * 1.0e-30
                                * masked_data
                                * 1.0e6
                            )
                        )
                        data2 = h * c / (bc * cor[0] * 1.0e-6) / data1
                        # masked_data = ((data2-cor[2])/cor[1]) - 273.15
                        # By default, GeoIPS readers should store BT data internally in
                        # Kelvin.
                        masked_data = (data2 - cor[2]) / cor[1]

                        LOG.info(
                            "    Adding channame: "
                            + str(channame + "BT")
                            + " offset: "
                            + str(attrs["radiance_offsets"][ind])
                            + " scale: "
                            + str(attrs["radiance_scales"][ind])
                            + " ems1km: "
                            + str(cor[0])
                            + " tcs1km: "
                            + str(cor[1])
                            + " tci1km: "
                            + str(cor[2])
                            + " min: "
                            + str(masked_data.min())
                            + " max: "
                            + str(masked_data.max())
                        )
                        add_to_xarray(
                            channame + "BT",
                            masked_data,
                            xarrays[datasettag],
                            cumulative_mask[datasettag],
                            datasettag,
                        )
                        xarrays[datasettag][channame + "BT"].attrs["units"] = "Kelvin"
                    if (
                        channame
                        in corrections_ref[
                            mf_metadata["ASSOCIATEDPLATFORMSHORTNAME"].lower()
                        ].keys()
                    ):
                        corrected_data = np.ma.masked_equal(
                            np.ma.array(data), attrs["_FillValue"]
                        )
                        corrected_data = np.ma.masked_greater(
                            masked_data, attrs["valid_range"][1]
                        )
                        corrected_data = np.ma.masked_less(
                            masked_data, attrs["valid_range"][0]
                        )
                        offset = corrections_ref[
                            mf_metadata["ASSOCIATEDPLATFORMSHORTNAME"].lower()
                        ][channame][1]
                        scale = corrections_ref[
                            mf_metadata["ASSOCIATEDPLATFORMSHORTNAME"].lower()
                        ][channame][0]
                        corrected_data += offset
                        corrected_data *= 100.0 * scale
                        LOG.info(
                            "    Adding channame: "
                            + str(channame + "Ref")
                            + " offset: "
                            + str(offset)
                            + " scale: "
                            + str(scale)
                        )
                        add_to_xarray(
                            channame + "Ref",
                            corrected_data,
                            xarrays[datasettag],
                            cumulative_mask[datasettag],
                            datasettag,
                        )

            # Add attributes
            xarrays[datasettag].attrs["start_datetime"] = sdt
            xarrays[datasettag].attrs["end_datetime"] = edt
            xarrays[datasettag].attrs["source_name"] = "modis"
            xarrays[datasettag].attrs["platform_name"] = mf_metadata[
                "ASSOCIATEDPLATFORMSHORTNAME"
            ].lower()
            xarrays[datasettag].attrs["data_provider"] = "nasa"
            if basename(fname) not in xarrays[datasettag].attrs["source_file_names"]:
                xarrays[datasettag].attrs["source_file_names"] += [basename(fname)]
            xarrays[datasettag].attrs["sample_distance_km"] = 2  # ????
            xarrays[datasettag].attrs["interpolation_radius_of_influence"] = 3000  # ???

    # compbine output fields
    xarray_returns = {}
    for dtype in xarrays.keys():
        LOG.info("Trying xarrays[%s]", dtype)
        if dtype != "METATDATA" and "latitude" not in list(
            xarrays[dtype].variables.keys()
        ):
            LOG.info("No data read for dataset %s, removing from xarray list", dtype)
            continue
        if dtype != "METADATA":
            for varname in list(xarrays[dtype].variables.keys()):
                xarrays[dtype][varname] = xarrays[dtype][varname].where(
                    ~cumulative_mask[dtype][varname]
                )

        LOG.info("Adding xarrays[%s]", dtype)
        xarray_returns[dtype] = xarrays[dtype]

    if len(list(xarray_returns.values())) == 0:
        raise IOError("No data found for requested channels %s", chans)

    xarray_returns["METADATA"] = list(xarray_returns.values())[0][[]]

    return xarray_returns
