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
from os.path import exists
from os import scandir
from importlib.resources import files

import pytest
from geoips.commandline.log_setup import setup_logging
from geoips.interfaces import readers
from geoips.geoips_utils import get_entry_point_group


LOG = setup_logging()


class TestReaders:
    """Unit tests every reader."""

    plugin_packages = get_entry_point_group("geoips.plugin_packages")
    available_readers = []
    for pkg in plugin_packages:
        dir_path = str(files(pkg.value) / "plugins/modules/readers/")
        if exists(dir_path):
            for reader_path in scandir(dir_path):
                if reader_path.is_file() and "__init__" not in reader_path.name:
                    available_readers.append(reader_path.name.split(".")[0])

    def verify_plugin(self, plugin):
        """Yeild test xarray and parameters."""
        test_xr = plugin.module.gen_test_files()
        test_param = plugin.module.gen_test_parameters()
        self.verify_xarray(test_xr, test_param)

    def verify_xarray(self, inxr, test_parameters):
        """Test every parameter."""
        data_key = test_parameters["data_key"]
        data_var = test_parameters["data_var"]

        assert inxr
        assert inxr[data_key]
        assert inxr[data_key].longitude.max()
        assert inxr[data_key].longitude.min()
        assert inxr[data_key].latitude.max()
        assert inxr[data_key].latitude.min()
        assert getattr(inxr[data_key], data_var).mean()
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
        print("\n", reader_name)
        self.verify_plugin(reader)
