# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Fixtures for testing the Order-based procflow pydantic models."""

# Third-Party Libraries
import pytest


@pytest.fixture
def valid_step_data():
    """Fixture to provide sample valid plugin data for testing."""
    return {
        "kind": "reader",
        "name": "abi_netcdf",
        "arguments": {
            "area_def": "None",
            "variables": ["None"],
            "metadata_only": False,
            "self_register": ["None"],
        },
    }


@pytest.fixture
def valid_interfaces(valid_plugin_types):
    """Fixture to provide list of valid GeoIPS interfaces."""
    return {f"{plugin_type}s" for plugin_type in valid_plugin_types}


@pytest.fixture
def valid_reader_arguments_model_data():
    """Fixture to provide sample valid Reader arguments for testing."""
    return {
        "area_def": "None",
        "variables": ["None"],
        "metadata_only": True,
        "self_register": ["None"],
        "fnames": ["None"],
    }


@pytest.fixture
def valid_plugin_types():
    """Fixture to provide the list of valid plugin types."""
    VALID_PLUGIN_TYPES = [
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
    return VALID_PLUGIN_TYPES


# test_bases.py
@pytest.fixture
def valid_plugin_data():
    """Fixture providing valid sample data for Plugin model."""
    return {
        "interface": "workflows",
        "family": "geoips_family",
        "name": "read_test",
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
