import pytest
import numpy as np
import xarray as xr
from xarray import DataTree
import pandas as pd
from typing import Any
import copy

# Import the module
from geoips.utils.types.datatree_ditto import DataTreeDitto


class TestDataTreeDittoCore:
    """Test core functionality of DataTreeDitto."""

    def test_initialization_empty(self):
        """Test creating empty DataTreeDitto."""
        dt = DataTreeDitto()
        assert isinstance(dt, DataTreeDitto)
        assert isinstance(dt, DataTree)
        # DataTree automatically creates an empty dataset when initialized without data
        assert dt.ds is not None
        assert len(dt.ds.data_vars) == 0
        assert len(dt.ds.dims) == 0

    def test_initialization_with_dataset(self):
        """Test creating DataTreeDitto with xarray Dataset."""
        ds = xr.Dataset({"temp": (["x", "y"], np.random.rand(2, 3))})
        dt = DataTreeDitto(dataset=ds)
        # ds property returns a view, so we check the underlying data
        assert "temp" in dt.ds.data_vars
        assert isinstance(dt, DataTreeDitto)

    def test_initialization_with_numpy_array(self):
        """Test creating DataTreeDitto with numpy array."""
        arr = np.random.rand(3, 4)
        dt = DataTreeDitto(dataset=arr)
        assert isinstance(dt.ds, xr.Dataset)
        # Check the underlying dataset for attributes
        actual_ds = dt.ds._dataset if hasattr(dt.ds, "_dataset") else dt.ds
        assert "_ditto_original_type" in actual_ds.attrs
        assert actual_ds.attrs["_ditto_original_type"] == "numpy.ndarray"

    def test_initialization_with_unsupported_type(self):
        """Test creating DataTreeDitto with unsupported type raises error."""
        with pytest.raises(TypeError, match="No converter registered"):
            DataTreeDitto(dataset="unsupported string")


class TestConverterSystem:
    """Test the converter registration and functionality."""

    def test_builtin_numpy_converter_exists(self):
        """Test that numpy converter is registered by default."""
        assert np.ndarray in DataTreeDitto._converters
        assert "to_dataset" in DataTreeDitto._converters[np.ndarray]
        assert "from_dataset" in DataTreeDitto._converters[np.ndarray]

    def test_register_custom_converter(self):
        """Test registering a custom converter."""

        def list_to_dataset(obj, name="data", dims=None, **kwargs):
            arr = np.array(obj)
            if dims is None:
                dims = ["dim_0"]
            da = xr.DataArray(arr, dims=dims, name=name)
            ds = da.to_dataset()
            ds.attrs.update(
                {
                    "_ditto_original_type": "builtins.list",
                    "_ditto_var_name": name,
                    "_ditto_dims": dims,
                }
            )
            return ds

        def dataset_to_list(dataset, **kwargs):
            var_name = dataset.attrs.get("_ditto_var_name", "data")
            return dataset[var_name].values.tolist()

        DataTreeDitto.register_converter(list, list_to_dataset, dataset_to_list)

        # Test the converter works
        dt = DataTreeDitto()
        test_list = [1, 2, 3, 4, 5]
        dt["list_data"] = test_list

        assert isinstance(dt["list_data"].ds, xr.Dataset)
        assert dt.get_original("list_data") == test_list

        # Cleanup
        del DataTreeDitto._converters[list]

    def test_numpy_to_dataset_conversion(self):
        """Test numpy array to dataset conversion details."""
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        ds = DataTreeDitto._numpy_to_dataset(arr, name="test_data")

        assert isinstance(ds, xr.Dataset)
        assert "test_data" in ds.data_vars
        assert ds.attrs["_ditto_original_type"] == "numpy.ndarray"
        assert ds.attrs["_ditto_original_shape"] == (2, 3)
        assert ds.attrs["_ditto_var_name"] == "test_data"
        assert ds.attrs["_ditto_dims"] == ["dim_0", "dim_1"]

    def test_dataset_to_numpy_conversion(self):
        """Test dataset to numpy array conversion."""
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        ds = DataTreeDitto._numpy_to_dataset(arr, name="test_data")
        converted_back = DataTreeDitto._dataset_to_numpy(ds)

        np.testing.assert_array_equal(arr, converted_back)

    def test_custom_dims_numpy_conversion(self):
        """Test numpy conversion with custom dimensions."""
        arr = np.random.rand(2, 3, 4)
        custom_dims = ["time", "lat", "lon"]
        ds = DataTreeDitto._numpy_to_dataset(arr, dims=custom_dims)

        assert ds.attrs["_ditto_dims"] == custom_dims
        assert list(ds["data"].dims) == custom_dims


class TestAssignmentAndRetrieval:
    """Test assignment and retrieval operations."""

    def test_setitem_numpy_array(self):
        """Test assigning numpy array via setitem."""
        dt = DataTreeDitto()
        arr = np.random.rand(3, 4)
        dt["numpy_node"] = arr

        assert "numpy_node" in dt.children
        assert isinstance(dt["numpy_node"], DataTreeDitto)
        assert isinstance(dt["numpy_node"].ds, xr.Dataset)

    def test_setitem_xarray_dataset(self):
        """Test assigning xarray dataset via setitem."""
        dt = DataTreeDitto()
        ds = xr.Dataset({"temp": (["x", "y"], np.random.rand(2, 3))})
        dt["xarray_node"] = ds

        assert "xarray_node" in dt.children
        assert isinstance(dt["xarray_node"], DataTreeDitto)
        assert "temp" in dt["xarray_node"].ds.data_vars

    def test_setitem_unsupported_type(self):
        """Test assigning unsupported type raises error."""
        dt = DataTreeDitto()
        with pytest.raises(TypeError, match="Cannot assign object of type"):
            dt["bad_node"] = "unsupported string"

    def test_getitem_returns_datatree_ditto(self):
        """Test that getitem returns DataTreeDitto instances."""
        dt = DataTreeDitto()
        arr = np.random.rand(2, 3)
        dt["test_node"] = arr

        retrieved = dt["test_node"]
        assert isinstance(retrieved, DataTreeDitto)

    def test_nested_assignment(self):
        """Test nested assignment of various types."""
        dt = DataTreeDitto()

        # Create nested structure
        arr1 = np.random.rand(2, 3)
        arr2 = np.random.rand(4, 5)
        ds = xr.Dataset({"temp": (["x", "y"], np.random.rand(3, 4))})

        dt["level1"] = DataTreeDitto()
        dt["level1"]["numpy1"] = arr1
        dt["level1"]["numpy2"] = arr2
        dt["level1"]["xarray1"] = ds

        assert isinstance(dt["level1"]["numpy1"], DataTreeDitto)
        assert isinstance(dt["level1"]["xarray1"], DataTreeDitto)
        np.testing.assert_array_equal(dt.get_original("level1/numpy1"), arr1)


class TestOriginalObjectRetrieval:
    """Test retrieval of original objects."""

    def test_get_original_current_node(self):
        """Test getting original object from current node."""
        arr = np.random.rand(3, 4)
        dt = DataTreeDitto(dataset=arr)

        original = dt.get_original(".")
        np.testing.assert_array_equal(original, arr)

    def test_get_original_child_node(self):
        """Test getting original object from child node."""
        dt = DataTreeDitto()
        arr = np.random.rand(2, 5)
        dt["child"] = arr

        original = dt.get_original("child")
        np.testing.assert_array_equal(original, arr)

    def test_get_original_xarray_object(self):
        """Test getting original xarray object returns dataset."""
        dt = DataTreeDitto()
        ds = xr.Dataset({"temp": (["x", "y"], np.random.rand(2, 3))})
        dt["xarray_node"] = ds

        original = dt.get_original("xarray_node")
        # Since xarray objects don't have conversion metadata, we get back the dataset
        assert isinstance(original, xr.Dataset)
        assert "temp" in original.data_vars

    def test_get_original_none_data(self):
        """Test getting original from node with no data."""
        dt = DataTreeDitto()
        dt["empty"] = DataTreeDitto()

        original = dt.get_original("empty")
        # DataTree automatically creates an empty dataset, so we get that back
        assert isinstance(original, xr.Dataset)
        assert len(original.data_vars) == 0
        assert len(original.dims) == 0

    def test_roundtrip_conversion(self):
        """Test perfect roundtrip conversion."""
        original_arrays = [
            np.array([1, 2, 3]),
            np.array([[1, 2], [3, 4]]),
            np.random.rand(2, 3, 4),
            np.array(["a", "b", "c"]),  # string array
        ]

        dt = DataTreeDitto()
        for i, arr in enumerate(original_arrays):
            dt[f"arr_{i}"] = arr
            retrieved = dt.get_original(f"arr_{i}")
            np.testing.assert_array_equal(retrieved, arr)
            assert retrieved.dtype == arr.dtype


class TestDataTreeConversion:
    """Test conversion to standard DataTree."""

    def test_to_datatree_simple(self):
        """Test converting simple DataTreeDitto to DataTree."""
        dt = DataTreeDitto()
        arr = np.random.rand(2, 3)
        dt["numpy_data"] = arr

        standard_dt = dt.to_datatree()

        assert isinstance(standard_dt, DataTree)
        assert not isinstance(standard_dt, DataTreeDitto)
        assert "numpy_data" in standard_dt.children
        assert isinstance(standard_dt["numpy_data"].ds, xr.Dataset)

    def test_to_datatree_nested(self):
        """Test converting nested DataTreeDitto to DataTree."""
        dt = DataTreeDitto()
        dt["level1"] = DataTreeDitto()
        dt["level1"]["numpy_data"] = np.random.rand(2, 3)
        dt["level1"]["xarray_data"] = xr.Dataset(
            {"temp": (["x", "y"], np.random.rand(3, 4))}
        )

        standard_dt = dt.to_datatree()

        assert isinstance(standard_dt, DataTree)
        assert isinstance(standard_dt["level1"], DataTree)
        assert not isinstance(standard_dt["level1"], DataTreeDitto)

    def test_to_datatree_preserves_data(self):
        """Test that conversion to DataTree preserves all data."""
        dt = DataTreeDitto()
        arr = np.array([[1, 2], [3, 4]])
        dt["test"] = arr

        standard_dt = dt.to_datatree()

        # Data should be preserved as dataset
        assert isinstance(standard_dt["test"].ds, xr.Dataset)
        # Original conversion metadata should be preserved
        actual_ds = (
            standard_dt["test"].ds._dataset
            if hasattr(standard_dt["test"].ds, "_dataset")
            else standard_dt["test"].ds
        )
        assert "_ditto_original_type" in actual_ds.attrs


class TestMetadataAndIntrospection:
    """Test metadata preservation and introspection methods."""

    def test_list_converted_nodes_empty(self):
        """Test listing converted nodes on empty tree."""
        dt = DataTreeDitto()
        converted = dt.list_converted_nodes()
        assert converted == {}

    def test_list_converted_nodes_with_conversions(self):
        """Test listing converted nodes with actual conversions."""
        dt = DataTreeDitto()
        dt["numpy1"] = np.random.rand(2, 3)
        dt["level1"] = DataTreeDitto()
        dt["level1"]["numpy2"] = np.random.rand(4, 5)
        dt["level1"]["xarray1"] = xr.Dataset(
            {"temp": (["x", "y"], np.random.rand(2, 2))}
        )

        converted = dt.list_converted_nodes()

        assert "numpy1" in converted
        assert "level1/numpy2" in converted
        assert converted["numpy1"] == "numpy.ndarray"
        assert converted["level1/numpy2"] == "numpy.ndarray"
        # xarray objects shouldn't appear in converted list
        assert "level1/xarray1" not in converted

    def test_list_converted_nodes_root_conversion(self):
        """Test listing when root node itself is converted."""
        arr = np.random.rand(3, 3)
        dt = DataTreeDitto(dataset=arr)

        converted = dt.list_converted_nodes()
        assert "/" in converted
        assert converted["/"] == "numpy.ndarray"

    def test_enhanced_repr(self):
        """Test enhanced string representation."""
        dt = DataTreeDitto()
        dt["numpy_data"] = np.random.rand(2, 3)

        repr_str = repr(dt)
        assert "Converted nodes:" in repr_str
        assert "numpy_data: numpy.ndarray" in repr_str

    def test_repr_no_conversions(self):
        """Test repr when no conversions exist."""
        dt = DataTreeDitto()
        dt["xarray_data"] = xr.Dataset({"temp": (["x", "y"], np.random.rand(2, 3))})

        repr_str = repr(dt)
        assert "Converted nodes:" not in repr_str


class TestInheritance:
    """Test that DataTree functionality is preserved."""

    def test_is_datatree_subclass(self):
        """Test that DataTreeDitto is a DataTree subclass."""
        dt = DataTreeDitto()
        assert isinstance(dt, DataTree)
        assert isinstance(dt, DataTreeDitto)

    def test_datatree_methods_available(self):
        """Test that DataTree methods are available."""
        dt = DataTreeDitto()

        # Test some DataTree methods exist
        assert hasattr(dt, "subtree")
        assert hasattr(dt, "filter")
        assert hasattr(dt, "match")
        assert hasattr(dt, "map_over_datasets")

    def test_datatree_properties_available(self):
        """Test that DataTree properties are available."""
        dt = DataTreeDitto()

        # Test some DataTree properties exist
        assert hasattr(dt, "parent")
        assert hasattr(dt, "children")
        assert hasattr(dt, "siblings")
        assert hasattr(dt, "root")

    def test_mixed_tree_operations(self):
        """Test operations on trees with mixed content."""
        dt = DataTreeDitto()

        # Add mixed content
        dt["numpy"] = np.random.rand(2, 3)
        dt["xarray"] = xr.Dataset({"temp": (["x", "y"], np.random.rand(2, 3))})
        dt["empty"] = DataTreeDitto()

        # Test tree navigation works
        assert len(dt.children) == 3
        assert dt["numpy"].parent is dt
        assert dt.root is dt


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_converter_not_found_fallback(self):
        """Test fallback when converter metadata exists but converter is missing."""
        # Create a dataset with conversion metadata but no actual converter
        ds = xr.Dataset({"data": (["x", "y"], np.random.rand(2, 3))})
        ds.attrs["_ditto_original_type"] = "nonexistent.FakeType"

        dt = DataTreeDitto(dataset=ds)
        original = dt.get_original(".")

        # Should fallback to returning the dataset
        assert isinstance(original, xr.Dataset)
        assert "data" in original.data_vars

    def test_empty_numpy_array(self):
        """Test handling empty numpy arrays."""
        arr = np.array([])
        dt = DataTreeDitto()
        dt["empty_array"] = arr

        retrieved = dt.get_original("empty_array")
        np.testing.assert_array_equal(retrieved, arr)

    def test_scalar_numpy_array(self):
        """Test handling scalar numpy arrays."""
        arr = np.array(42)
        dt = DataTreeDitto()
        dt["scalar"] = arr

        retrieved = dt.get_original("scalar")
        assert retrieved == arr
        assert retrieved.shape == arr.shape

    def test_complex_numpy_arrays(self):
        """Test handling complex numpy arrays."""
        arr = np.array([1 + 2j, 3 + 4j, 5 + 6j])
        dt = DataTreeDitto()
        dt["complex"] = arr

        retrieved = dt.get_original("complex")
        np.testing.assert_array_equal(retrieved, arr)
        assert retrieved.dtype == arr.dtype

    def test_dataset_without_var_name_metadata(self):
        """Test converting dataset back when var_name metadata is missing."""
        arr = np.array([1, 2, 3])
        ds = DataTreeDitto._numpy_to_dataset(arr)

        # Remove the var_name metadata
        del ds.attrs["_ditto_var_name"]

        # Should still work by using first data variable
        retrieved = DataTreeDitto._dataset_to_numpy(ds)
        np.testing.assert_array_equal(retrieved, arr)


class TestPerformance:
    """Test performance-related aspects."""

    def test_large_array_conversion(self):
        """Test conversion of large numpy arrays."""
        # Create a reasonably large array
        large_arr = np.random.rand(100, 100, 10)
        dt = DataTreeDitto()

        # Should handle large arrays without issues
        dt["large_array"] = large_arr
        retrieved = dt.get_original("large_array")

        np.testing.assert_array_equal(retrieved, large_arr)

    def test_many_small_conversions(self):
        """Test many small conversions."""
        dt = DataTreeDitto()

        # Add many small arrays
        arrays = {}
        for i in range(50):
            arr = np.random.rand(5, 5)
            arrays[f"arr_{i}"] = arr
            dt[f"arr_{i}"] = arr

        # Verify all conversions work
        for name, original_arr in arrays.items():
            retrieved = dt.get_original(name)
            np.testing.assert_array_equal(retrieved, original_arr)


# Fixtures for testing
@pytest.fixture
def sample_datatree_ditto():
    """Create a sample DataTreeDitto for testing."""
    dt = DataTreeDitto()
    dt["numpy_data"] = np.random.rand(3, 4)
    dt["xarray_data"] = xr.Dataset(
        {
            "temperature": (["x", "y"], np.random.rand(2, 3)),
            "pressure": (["x", "y"], np.random.rand(2, 3)),
        }
    )
    dt["nested"] = DataTreeDitto()
    dt["nested"]["more_numpy"] = np.array([1, 2, 3, 4, 5])
    return dt


@pytest.fixture
def custom_converter_setup():
    """Setup and teardown for custom converter tests."""

    # Setup: register a string converter
    def string_to_dataset(obj, name="data", dims=None, **kwargs):
        # Convert string to char array
        char_array = np.array(list(obj))
        if dims is None:
            dims = ["char_dim"]
        da = xr.DataArray(char_array, dims=dims, name=name)
        ds = da.to_dataset()
        ds.attrs.update(
            {
                "_ditto_original_type": "builtins.str",
                "_ditto_var_name": name,
                "_ditto_dims": dims,
                "_ditto_original_string": obj,  # Store original for perfect recovery
            }
        )
        return ds

    def dataset_to_string(dataset, **kwargs):
        return dataset.attrs["_ditto_original_string"]

    DataTreeDitto.register_converter(str, string_to_dataset, dataset_to_string)

    yield

    # Teardown: remove the converter
    if str in DataTreeDitto._converters:
        del DataTreeDitto._converters[str]


class TestWithFixtures:
    """Tests using fixtures."""

    def test_sample_datatree_structure(self, sample_datatree_ditto):
        """Test the sample DataTreeDitto structure."""
        dt = sample_datatree_ditto

        assert "numpy_data" in dt.children
        assert "xarray_data" in dt.children
        assert "nested" in dt.children
        assert "more_numpy" in dt["nested"].children

    def test_custom_string_converter(self, custom_converter_setup):
        """Test custom string converter."""
        dt = DataTreeDitto()
        test_string = "Hello, World!"
        dt["string_data"] = test_string

        assert isinstance(dt["string_data"].ds, xr.Dataset)
        retrieved = dt.get_original("string_data")
        assert retrieved == test_string
        assert isinstance(retrieved, str)
