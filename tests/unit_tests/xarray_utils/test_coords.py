# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for GeoIPS xarray coordinate normalization helpers."""

import xarray as xr

from geoips.utils.types.converters import (
    dataset_dict_to_dataset,
    dataset_to_dataset_dict,
)
from geoips.utils.types.datatree_helpers import to_mutable_dataset
from geoips.utils.types.obp_conduits import _extract_ds
from geoips.xarray_utils.coords import normalize_geoips_dataset_coords


def _dataset_with_lat_lon_data_vars():
    """Return a dataset with geolocation stored as data variables."""
    return xr.Dataset(
        {
            "temperature": (("y", "x"), [[1, 2], [3, 4]]),
            "latitude": (("y", "x"), [[10, 10], [11, 11]]),
            "longitude": (("y", "x"), [[20, 21], [20, 21]]),
        }
    )


def test_normalize_geoips_dataset_coords_moves_lat_lon_to_coords():
    """Latitude and longitude are coords, not data variables, after normalize."""
    normalized = normalize_geoips_dataset_coords(_dataset_with_lat_lon_data_vars())

    assert "temperature" in normalized.data_vars
    assert "latitude" not in normalized.data_vars
    assert "longitude" not in normalized.data_vars
    assert "latitude" in normalized.coords
    assert "longitude" in normalized.coords
    assert "latitude" in normalized
    assert "longitude" in normalized


def test_dataset_dict_conversion_preserves_lat_lon_coords():
    """Dataset split/merge conversion keeps lat/lon as coordinates."""
    dataset_dict = dataset_to_dataset_dict(_dataset_with_lat_lon_data_vars())

    assert list(dataset_dict) == ["temperature"]
    assert "latitude" in dataset_dict["temperature"].coords
    assert "longitude" in dataset_dict["temperature"].coords

    merged = dataset_dict_to_dataset(dataset_dict)

    assert "temperature" in merged.data_vars
    assert "latitude" in merged.coords
    assert "longitude" in merged.coords
    assert "latitude" not in merged.data_vars
    assert "longitude" not in merged.data_vars


def test_extract_ds_normalizes_flattened_reader_tree():
    """Flattening reader-style DataTrees keeps lat/lon out of data_vars."""
    root = xr.DataTree(xr.Dataset(attrs={"source_name": "test"}), name="reader")
    root["DATA"] = xr.DataTree(_dataset_with_lat_lon_data_vars(), name="DATA")

    flattened = _extract_ds(root)

    assert flattened.attrs["source_name"] == "test"
    assert "temperature" in flattened.data_vars
    assert "latitude" in flattened.coords
    assert "longitude" in flattened.coords


def test_to_mutable_dataset_normalizes_coords():
    """Mutable dataset conversion keeps GeoIPS coordinate variables as coords."""
    root = xr.DataTree(name="multi_input")
    root["reader"] = xr.DataTree(_dataset_with_lat_lon_data_vars(), name="reader")

    converted = to_mutable_dataset(root)

    assert "temperature" in converted.data_vars
    assert "latitude" in converted.coords
    assert "longitude" in converted.coords
