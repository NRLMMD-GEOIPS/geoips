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
import pytest
from geoips.commandline.log_setup import setup_logging
from geoips.interfaces import readers


LOG = setup_logging()


class TestReaders:
    """Unit tests every reader."""

    available_readers = [
        ("abi_l2_netcdf"),
        ("abi_netcdf"),
        ("ahi_hsd"),
        ("amsr2_netcdf"),
        ("amsr2_remss_winds_netcdf"),
        ("amsub_hdf"),
        ("amsub_mirs"),
        ("ascat_uhr_netcdf"),
        ("atms_hdf5"),
        ("ewsg_netcdf"),
        ("geoips_netcdf"),
        ("gmi_hdf5"),
        ("imerg_hdf5"),
        ("mimic_netcdf"),
        ("modis_hdf4"),
        ("saphir_hdf5"),
        ("sar_winds_netcdf"),
        ("scat_knmi_winds_netcdf"),
        ("scat_noaa_winds_netcdf"),
        ("seviri_hrit"),
        ("sfc_winds_text"),
        ("smap_remss_winds_netcdf"),
        ("smos_winds_netcdf"),
        ("ssmi_binary"),
        ("ssmis_binary"),
        ("viirs_netcdf"),
        ("wfabba_ascii"),
        ("windsat_idr37_binary"),
        ("windsat_remss_winds_netcdf"),
    ]

    def verify_plugin(self, plugin):
        """Yeild test xarray and parameters."""
        test_xr = plugin.module.gen_test_files()
        test_param = plugin.module.gen_test_parameters()
        self.verify_xarray(test_xr, test_param)

    def verify_xarray(self, inxr, test_parameters):
        """Test every parameter."""
        # could add more parameters; lon_max, lat_max, etc
        data_key = test_parameters
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

    @pytest.mark.parametrize("reader_name", available_readers)
    def test_reader_plugins(self, reader_name):
        """Unit test every plugin, xfail for ones with no unit tests."""
        reader = readers.get_plugin(reader_name)
        if not hasattr(reader.module, "gen_test_files") or not hasattr(
            reader.module, "gen_test_parameters"
        ):
            pytest.xfail(reader_name + " has no test modules")
        self.verify_plugin(reader)
