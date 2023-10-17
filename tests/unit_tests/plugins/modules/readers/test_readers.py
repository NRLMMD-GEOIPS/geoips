# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Unit tests on all the readers."""

import os
from glob import glob
import pytest
from geoips.commandline.log_setup import setup_logging
from geoips.interfaces import readers


LOG = setup_logging()


class TestReaders:
    """Tests all reader, checking GEOIPS standards and keywords."""

    data_dir = os.environ["GEOIPS_TESTDATA_DIR"]
    available_readers = [
        ("abi_l2_netcdf", "", ""),
        ("abi_netcdf", "", ""),
        ("ahi_hsd", "", ""),
        (
            "amsr2_netcdf",
            "/test_data_amsr2/data/AMSR2*.nc",
            "Brightness_Temperature_10_GHzH",
        ),
        ("amsr2_remss_winds_netcdf", "/test_data_amsr2/data/RSS*.nc", "WINDSPEED_1"),
        ("amsub_hdf", "", ""),
        ("amsub_mirs", "", ""),
        ("ascat_uhr_netcdf", "", ""),
        ("atms_hdf5", "", ""),
        ("ewsg_netcdf", "", ""),
        ("geoips_netcdf", "", ""),
        ("gmi_hdf5", "/test_data_gpm/data/*.RT-H5", "GMI"),
        ("imerg_df5", "", ""),
        ("mimic_netcdf", "", ""),
        ("modis_hdf4", "", ""),
        ("saphir_hdf5", "", ""),
        ("sar_winds_netcdf", "/test_data_sar/data/*.nc", "WINDSPEED"),
        (
            "scat_knmi_winds_netcdf",
            "/test_data_scat/data/metopc*knmi*/*coa*.nc",
            "WINDSPEED",
        ),
        (
            "scat_noaa_winds_netcdf",
            "/test_data_scat/data/20230524_metopc_noaa*/*.nc",
            "WINDSPEED",
        ),
        ("seviri_hrit", "", ""),
        ("sfc_winds_text", "", ""),
        ("smap_remss_winds_netcdf", "/test_data_smap/data/*.nc", "WINDSPEED_1"),
        ("smos_winds_netcdf", "", ""),
        ("ssmi_binary", "", ""),
        ("ssmis_binary", "", ""),
        ("viirs_netcdf", "", ""),
        ("wfabba_ascii", "", ""),
        ("windsat_idr37_binary", "", ""),
        ("windsat_remss_winds_netcdf", "", ""),
    ]

    def check_xr(self, inxr, data_key):
        """Check the input array with GEOIPS xarray standards."""
        assert inxr
        assert inxr[data_key]
        assert inxr[data_key].longitude.max()
        assert inxr[data_key].longitude.min()
        assert inxr[data_key].latitude.max()
        assert inxr[data_key].latitude.min()
        assert inxr["METADATA"].attrs["source_name"]
        assert inxr["METADATA"].attrs["platform_name"]
        assert inxr["METADATA"].attrs["data_provider"]
        assert inxr["METADATA"].attrs["start_datetime"]
        assert inxr["METADATA"].attrs["end_datetime"]
        assert inxr["METADATA"].attrs["interpolation_radius_of_influence"]

    @pytest.mark.parametrize("key,files,data_key", available_readers)
    def test_reader_plugins(self, key, files, data_key):
        """Test all reader plugins, xfails for readers that don't have files.

        Parameters
        ----------
        key : string
           Reader plugin key
        files : string
           Wildcard path to data for reader
        data_key : string
           Key for data values in xarray dictionary

        Returns
        -------
        None
        """
        file_path = self.data_dir + files
        filelist = glob(file_path)
        if files == "" or len(filelist) == 0:
            pytest.xfail("No files given")

        tmp_reader = readers.get_plugin(key)
        inxr = tmp_reader(filelist[:2])
        self.check_xr(inxr, data_key)
