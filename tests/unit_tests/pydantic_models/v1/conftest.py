# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Fixtures for testing the Order-based procflow pydantic models."""

# cspell:ignore knmi
# cspell:ignore wfabba
# cspell:ignore ewsg

# Third-Party Libraries
import pytest
import datetime as dt

# GeoIPS Libraries
from geoips.interfaces import sectors


@pytest.fixture
def valid_step_data():
    """Fixture to provide sample valid plugin data for testing."""
    return {
        "kind": "reader",
        "name": "abi_netcdf",
        "arguments": {
            "area_def": sectors.get_plugin("denver").area_definition,
            "variables": ["None"],
            "metadata_only": False,
            "self_register": "LOW",
        },
    }


@pytest.fixture
def valid_interfaces(valid_plugin_kinds):
    """Fixture to provide list of valid GeoIPS interfaces."""
    return {f"{plugin_kind}s" for plugin_kind in valid_plugin_kinds}


@pytest.fixture
def file_generated_from_pytest_fixture(tmp_path):
    """Fixture to create a temporary file for testing."""
    file_generated_from_pytest_fixture = tmp_path / "exits.nc"
    file_generated_from_pytest_fixture.touch()
    return file_generated_from_pytest_fixture


@pytest.fixture
# def valid_reader_arguments_model_data(tmp_path):
def valid_reader_arguments_model_data(file_generated_from_pytest_fixture):
    """Fixture to provide sample valid Reader arguments for testing."""
    # file_generatied_from_pytest_fixture = tmp_path / "exits.nc"
    # file_generatied_from_pytest_fixture.touch()
    return {
        "area_def": sectors.get_plugin("denver").area_definition,
        "variables": ["None"],
        "metadata_only": True,
        "self_register": "LOW",
        "fnames": [file_generated_from_pytest_fixture],
    }


@pytest.fixture
def valid_plugin_kinds():
    """Fixture to provide the list of valid plugin kinds."""
    VALID_PLUGIN_KINDS = [
        "algorithm",
        "procflow",
        "database",
        "sector_adjuster",
        "output_checker",
        "output_formatter",
        "reader",
        "gridline_annotator",
        "product_default",
        "sector_metadata_generator",
        "product",
        "sector_spec_generator",
        "title_formatter",
        "coverage_checker",
        "feature_annotator",
        "colormapper",
        "sector",
        "interpolator",
        "filename_formatter",
        "workflow",
    ]
    return VALID_PLUGIN_KINDS


# test_bases.py
@pytest.fixture
def valid_plugin_data():
    """Fixture providing valid sample data for Plugin model."""
    return {
        "interface": "workflows",
        "family": "geoips_family",
        "name": "read_test_v1",
        "docstring": "This is a valid numpy docstring.",
        "description": "This is a valid numpy docstring.",
        "package": "geoips",
        "relpath": "geoips/tests/unit_tests/pydantic",
        "abspath": "/home/kumar/geoips/geoips/tests/unit_tests/pydantic",
    }


@pytest.fixture
def pluign_types_and_plugins():
    """Fixture providing valid plugin types & corresponding plugin names."""
    return {
        "reader": [
            "scat_knmi_winds_netcdf",
            "abi_netcdf",
            "mimic_netcdf",
            "geoips_netcdf",
            "seviri_hrit",
            "amsub_mirs",
            "atms_hdf5",
            "amsr2_remss_winds_netcdf",
            "modis_hdf4",
            "wfabba_ascii",
            "saphir_hdf5",
            "ssmis_binary",
            "ewsg_netcdf",
            "viirs_sdr_hdf5",
            "amsr2_netcdf",
            "amsub_hdf",
            "gmi_hdf5",
            "viirs_netcdf",
            "windsat_remss_winds_netcdf",
            "scat_noaa_winds_netcdf",
            "windsat_idr37_binary",
            "smos_winds_netcdf",
            "imerg_hdf5",
            "ahi_hsd",
            "ascat_uhr_netcdf",
            "sar_winds_netcdf",
            "ami_netcdf",
            "ssmi_binary",
            "cygnss_netcdf",
            "abi_l2_netcdf",
            "sfc_winds_text",
            "smap_remss_winds_netcdf",
            "clavrx_netcdf4",
            "clavrx_hdf4",
        ],
    }


@pytest.fixture
def valid_title_formatter_arguments():
    """Fixture providing valid data for TitleFormatterArgumentsModel."""
    return {
        "area_def": "test_string",
        "product_name_title": "tc_copyright",
        "product_datatype_title": "test_string",
        "bg_product_name_title": "test_string",
        "bg_datatype_title": "test_string",
        "title_copyright": "Data copyright 2021 EUMETSAT, Imagery NRL-MRY",
    }


@pytest.fixture
def valid_output_checker_arguments(file_generated_from_pytest_fixture):
    """Fixture providing valid data OutputCheckerArgumentsModel tests."""
    return {
        "compare_path": file_generated_from_pytest_fixture,
        "output_products": [file_generated_from_pytest_fixture],
    }


@pytest.fixture
def valid_workflow_spec_model_data():
    """Fixture providing valid data testing WorkflowSpecModel fields."""
    return {
        "global_arguments": {
            "presector": False,
            "product_db": True,
            "product_db_writer": "postgres_database",
            "product_db_writer_kwargs": {
                "overwrite": True,
                "schema": "products",
            },
            "product_name": "Infrared-Gray",
            "reader_defined_area_def": True,
            "sector_list": ["TC2024"],
            "window_start_time": dt.datetime(2024, 9, 26, 18, 0, 0),
            "window_end_time": dt.datetime(2024, 9, 27, 3, 0, 0),
        },
        "steps": {
            "read_data": {
                "kind": "reader",
                "name": "abi_netcdf",
                "arguments": {},
            }
        },
    }


@pytest.fixture
def valid_interpolator_arguments():
    """Fixture providing valid data for InterpolatorArgumentsModel tests."""
    return {
        "area_def": "North Pole Region",
        "varlist": ["B09BT", "B10BT", "B07BT"],
        "sigmaval": 1000,
        "drop_nan": True,
        "method": "linear",
    }


@pytest.fixture
def valid_algorithm_arguments():
    """Fixture providing valid data for AlgorithmArgumentsModel."""
    return {
        "output_data_range": [-90.0, 30.0],
        "input_units": "Kelvin",
        "output_units": "celsius",
        "min_outbounds": "crop",
        "max_outbounds": "crop",
        "norm": False,
        "inverse": False,
        "pressure_level_range": [None, None],
        "time_key": "atime",
        # "norm": None,
        # "inverse": None,
    }
