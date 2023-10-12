#!/usr/bin/env python

import pytest
from geoips.commandline.log_setup import setup_logging
from geoips.interfaces import readers
from glob import glob

LOG = setup_logging()

# @pytest.fixture


@pytest.mark.parametrize(
    "key,files",
    [
        ("abi_l2_netcdf", ""),
        ("abi_netcdf", ""),
        ("ahi_hsd", ""),
        ("amsr2_netcdf", "geoips/test_data/test_data_amsr2/data/AMSR2*.nc"),
        ("amsr2_remss_winds_netcdf", "geoips/test_data/test_data_smap/data/RSS*.nc"),
        ("amsub_hdf", ""),
        ("amsub_mirs", ""),
        ("ascat_uhr_netcdf", ""),
        ("atms_hdf5", ""),
        ("ewsg_netcdf", ""),
        ("geoips_netcdf", ""),
        ("gmi_hdf5", "geoips/test_data/test_data_gpm/data/*.RT-H5"),
        ("imerg_df5", ""),
        ("mimic_netcdf", ""),
        ("modis_hdf4", ""),
        ("saphir_hdf5", ""),
        ("sar_winds_netcdf", "geoips/test_data/test_data_sar/data/*.nc"),
        ("scat_knmi_winds_netcdf", ""),
        ("scat_noaa_winds_netcdf", ""),
        ("seviri_hrit", ""),
        ("sfc_winds_text", ""),
        ("smap_remss_winds_netcdf", "geoips/test_data/test_data_smap/data/*.nc"),
        ("smos_winds_netcdf", ""),
        ("ssmi_binary", ""),
        ("ssmis_binary", ""),
        ("viirs_netcdf", ""),
        ("wfabba_ascii", ""),
        ("windsat_idr37_binary", ""),
        ("windsat_remss_winds_netcdf", ""),
    ],
)
def test_standards(key, files):
    """Takes the input xarray and tests for conformity with internal standards"""
    if 
    tmp_reader = readers.get_plugin(key)
    inxr = tmp_reader(glob(files)[:2])  # sometimes get core dumps?
    assert inxr  # how would we test the data key??
    assert inxr["METADATA"].attrs["source_name"]
    assert inxr["METADATA"].attrs["platform_name"]
    assert inxr["METADATA"].attrs["data_provider"]
    assert inxr["METADATA"].attrs["start_datetime"]
    assert inxr["METADATA"].attrs["end_datetime"]
    assert inxr["METADATA"].attrs["interpolation_radius_of_influence"]
