# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests on all the readers."""

from glob import glob
from os import environ
from os.path import dirname, exists

import numpy as np
import pytest
import yaml

from geoips.commandline.log_setup import setup_logging
from geoips.errors import PluginError
from geoips.interfaces import readers

LOG = setup_logging()


def get_reader_tests():
    """List of readers and associated test parameters.

    All tests included in this list have been implemented for unit testing.
    """
    with open(
        f"{dirname(__file__)}/reader_dataset_variable_mappings.yaml"
    ) as file_stream:
        reader_test_mapping = yaml.safe_load(file_stream)

    reader_tests = [
        {key: val}
        for key, val in reader_test_mapping["implemented_tests_for_readers"].items()
    ]

    return reader_tests


class TestReaders:
    """Unit tests every reader."""

    test_data_dir = environ["GEOIPS_TESTDATA_DIR"]

    def generate_id(test_entry):
        """Generate an id for the provided test entry.

        Parameters
        ----------
        test_entry: dict
            - A dictionary representing all of the parameters and information needed
              to perform a unit test for a given reader.
        """
        return list(test_entry.keys())[0]

    def read_data(self, plugin, filepath):
        """Read data from 'plugin' using the provided filepaths.

        Parameters
        ----------
        plugin: GeoIPS ReaderPlugin object
            - The object of a GeoIPS reader plugin
        filepath: str
            - A string representing one or more filepaths of dataset(s) to read.
        """
        filelist = glob(f"{self.test_data_dir}/{filepath}")
        if len(filelist) == 0:
            raise FileNotFoundError("No files found")
        for file in filelist:
            if not exists(file):
                raise FileNotFoundError(f"File {file} does not exist")
        tmp_xr = plugin(filelist)

        return tmp_xr

    def verify_plugin(self, plugin, test_info):
        """Yield test xarray and parameters.

        Parameters
        ----------
        plugin: GeoIPS ReaderPlugin object
            - The object of a GeoIPS reader plugin
        test_info: dict
            - A dictionary representing all of the parameters and information needed
              to perform a unit test for a given reader.
        """
        filepath = test_info["data_path"]
        test_xr = self.read_data(plugin, filepath)

        test_params = test_info["test_parameters"]
        self.verify_xarray(test_xr, test_params)

    def verify_xarray(self, inxr, test_parameters):
        """Test every parameter.

        Parameters
        ----------
        inxr: xarray.Dataset
            - The produced xarray.Dataset from the reader plugin
        test_parameters: list[dict]
            - A list of dictionaries representing parameters to test that are contained
              in 'inxr'
        """
        for parameter_dict in test_parameters:
            for test_parameter in parameter_dict.values():
                data_key = test_parameter["data_key"]
                data_var = test_parameter["data_var"]
                if "mean" in test_parameter:
                    mean = test_parameter["mean"]
                    try:
                        assert np.isclose(
                            inxr[data_key].variables[data_var].mean(), mean
                        )
                    except AssertionError:
                        LOG.error(
                            f"{data_key} {data_var} mean "
                            f"{inxr[data_key].variables[data_var].mean()} != {mean}"
                        )
                        raise

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

    @pytest.mark.parametrize("test_entry", get_reader_tests(), ids=generate_id)
    def test_reader_plugins(self, test_entry):
        """Unit test every plugin, xfail for ones with no unit tests."""
        reader_name = list(test_entry.keys())[0]
        test_info = test_entry[reader_name]

        try:
            reader = readers.get_plugin(reader_name)
        except PluginError:
            pytest.xfail(f"Could not find reader plugin named '{reader_name}.")

        try:
            self.verify_plugin(reader, test_info)
        except FileNotFoundError:
            pytest.xfail(reader_name + " is missing test data")
        except ValueError as e:
            if "Input files inconsistent." in str(e):
                pytest.xfail(reader_name + "is missing test data")
            else:
                raise e
