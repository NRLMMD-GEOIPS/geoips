# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests on all the readers."""
import numpy as np
import pytest
from geoips.commandline.log_setup import setup_logging
from geoips.interfaces import readers
from os import environ

LOG = setup_logging()


class TestReaders:
    """Unit tests every reader."""

    available_readers = [reader_type.name for reader_type in readers.get_plugins()]

    def verify_plugin(self, plugin):
        """Yield test xarray and parameters."""
        test_xr = plugin.module.get_test_files(environ["GEOIPS_TESTDATA_DIR"])
        test_param = plugin.module.get_test_parameters()
        self.verify_xarray(test_xr, test_param)

    def verify_xarray(self, inxr, test_parameters):
        """Test every parameter."""
        for test_parameter in test_parameters:
            data_key = test_parameter["data_key"]
            data_var = test_parameter["data_var"]
            if "mean" in test_parameter:
                mean = test_parameter["mean"]
                assert np.isclose(inxr[data_key].variables[data_var].mean(), mean)

            assert inxr
            assert inxr[data_key]
            assert inxr[data_key].longitude.max()
            assert inxr[data_key].longitude.min()
            assert inxr[data_key].latitude.max()
            assert inxr[data_key].latitude.min()
            assert inxr[data_key].variables[data_var].mean()
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
        if not hasattr(reader.module, "get_test_files") or not hasattr(
            reader.module, "get_test_parameters"
        ):
            pytest.xfail(reader_name + " has no test modules")
        try:
            self.verify_plugin(reader)
        except FileNotFoundError:
            pytest.xfail(reader_name + "is missing test data")
        except ValueError as e:
            if "Input files inconsistent." in str(e):
                pytest.xfail(reader_name + "is missing test data")
            else:
                raise e
