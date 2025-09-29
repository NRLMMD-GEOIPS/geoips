from collections.abc import Callable
from functools import wraps
from typing import Any, Union

import numpy as np
import xarray as xr
from xarray import DataTree

from collections.abc import (
    Callable,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
)


class DataTreeDitto(DataTree):
    """A DataTree subclass that automatically converts non-xarray objects to datasets.

    DataTreeDitto extends xarray's DataTree to automatically handle conversion of
    various data types (numpy arrays, etc.) to xarray Datasets while preserving
    metadata needed for round-trip conversion back to original types.

    Pokemon, the world's most valuable intellectual property,
    has a pokemon named "ditto" that duplicates its opponents behavior and structure
    with only slight difference. This class - DataTreeDitto - behaves like to xarray
    DataTrees with slight differences to accommodate a wider variety of data types.

    Examples
    --------
    >>> import numpy as np
    >>> arr = np.array([[1, 2], [3, 4]])
    >>> dt = DataTreeDitto(arr)
    >>> dt.ds.data.values.tolist()
    [[1, 2], [3, 4]]
    >>> dt.get_original().tolist()
    [[1, 2], [3, 4]]
    """

    def __init__(self, dataset=None, children=None, name=None):
        """Initialize a DataTreeDitto instance.

        Parameters
        ----------
        data : array-like, xarray.Dataset, xarray.DataArray, or None, optional
            Data to store in this node. Non-xarray objects are automatically
            converted to xarray.Dataset using registered converters.
        parent : DataTreeDitto, optional
            Parent node in the tree structure.
        children : dict, optional
            Dictionary of child nodes.
        name : str, optional
            Name of this node.

        Examples
        --------
        >>> arr = np.array([1, 2, 3])
        >>> dt = DataTreeDitto(arr, name="test")
        >>> dt.name
        'test'
        >>> dt.ds.data.values.tolist()
        [1, 2, 3]
        """
        # Initialize class-level converter registry if it does not exist
        if not hasattr(DataTreeDitto, "_converters"):
            DataTreeDitto._converters = {}
            DataTreeDitto._register_builtin_converters()

        # Convert data if the data is not an xarray DataSet
        if dataset is not None:
            # if isinstance(dataset, xr.DataArray):
            #    # Convert DataArray to Dataset
            #    dataset = dataset.to_dataset()
            if not isinstance(
                dataset,
                (
                    xr.Dataset,
                    xr.DataArray,
                    xr.core.coordinates.DataTreeCoordinates,
                    xr.DataTree,
                ),
            ):
                # Convert non-xarray object
                dataset = self._convert_to_dataset(dataset)

        super().__init__(dataset=dataset, children=children, name=name)

    def _convert_output_to_DataTreeDitto(f):
        def f_that_returns_datatree_ditto(*args, **kwargs):
            result = f(*args, **kwargs)
            if isinstance(result, DataTree) and not isinstance(result, DataTreeDitto):
                return DataTreeDitto._convert_datatree_to_ditto(result)
            return result

        return f_that_returns_datatree_ditto

    @classmethod
    def _register_builtin_converters(cls):
        """Register built-in converters for common types.

        Registers converters for numpy arrays automatically when the class
        is first instantiated.
        """
        cls.register_converter(np.ndarray, cls._numpy_to_dataset, cls._dataset_to_numpy)

    @classmethod
    def register_converter(
        cls,
        obj_type: type,
        to_dataset_func: Callable,
        from_dataset_func: Callable,
    ) -> None:
        """Register a converter for a specific object type.

        Parameters
        ----------
        obj_type : type
            The type of object to convert.
        to_dataset_func : callable
            Function to convert object to xarray.Dataset. Must accept the object
            as first argument and return an xarray.Dataset.
        from_dataset_func : callable
            Function to convert xarray.Dataset back to original object. Must
            accept an xarray.Dataset and return an object of obj_type.

        Examples
        --------
        >>> def list_to_dataset(lst, name="data", **kwargs):
        ...     arr = np.array(lst)
        ...     return DataTreeDitto._numpy_to_dataset(arr, name, **kwargs)
        >>> def dataset_to_list(ds, **kwargs):
        ...     return DataTreeDitto._dataset_to_numpy(ds, **kwargs).tolist()
        >>> DataTreeDitto.register_converter(list, list_to_dataset, dataset_to_list)
        """
        # if not hasattr(DataTreeDitto, "_converters"):
        #    DataTreeDitto._converters = {}
        #    DataTreeDitto._register_builtin_converters()
        cls._converters[obj_type] = {
            "to_dataset": to_dataset_func,
            "from_dataset": from_dataset_func,
        }

    @staticmethod
    def _numpy_to_dataset(
        obj: np.ndarray,
        name: str = "data",
        dims: list | None = None,
        **kwargs,
    ) -> xr.Dataset:
        """Convert numpy array to xarray Dataset.

        Parameters
        ----------
        obj : numpy.ndarray
            The numpy array to convert.
        name : str, default "data"
            Name for the data variable in the resulting dataset.
        dims : list of str, optional
            Dimension names. If None, generates names like "dim_0", "dim_1", etc.
        **kwargs
            Additional keyword arguments (currently unused).

        Returns
        -------
        xarray.Dataset
            Dataset containing the array data with metadata for round-trip conversion.

        Examples
        --------
        >>> arr = np.array([[1, 2], [3, 4]])
        >>> ds = DataTreeDitto._numpy_to_dataset(arr)
        >>> ds.data.values.tolist()
        [[1, 2], [3, 4]]
        >>> ds.attrs['_ditto_original_type']
        'numpy.ndarray'
        """
        if dims is None:
            dims = [f"dim_{i}" for i in range(obj.ndim)]

        data_array = xr.DataArray(obj, dims=dims, name=name)
        dataset = data_array.to_dataset()

        # Store metadata for round-trip conversion
        dataset.attrs.update(
            {
                "_ditto_original_type": "numpy.ndarray",
                "_ditto_original_shape": obj.shape,
                "_ditto_original_dtype": str(obj.dtype),
                "_ditto_var_name": name,
                "_ditto_dims": dims,
            },
        )

        return dataset

    @staticmethod
    def _dataset_to_numpy(dataset: xr.Dataset, **kwargs) -> np.ndarray:
        """Convert xarray Dataset back to numpy array.

        Parameters
        ----------
        dataset : xarray.Dataset
            Dataset to convert back to numpy array.
        **kwargs
            Additional keyword arguments (currently unused).

        Returns
        -------
        numpy.ndarray
            The numpy array extracted from the dataset.

        Examples
        --------
        >>> arr = np.array([1, 2, 3])
        >>> ds = DataTreeDitto._numpy_to_dataset(arr)
        >>> recovered = DataTreeDitto._dataset_to_numpy(ds)
        >>> recovered.tolist()
        [1, 2, 3]
        """
        var_name = dataset.attrs.get("_ditto_var_name", "data")
        if var_name not in dataset.data_vars:
            # Fallback: use first data variable
            var_name = next(iter(dataset.data_vars.keys()))

        return dataset[var_name].values

    def _convert_to_dataset(self, obj: Any, **kwargs) -> xr.Dataset:
        """Convert an object to xarray Dataset using registered converters.

        Parameters
        ----------
        obj : Any
            Object to convert to xarray Dataset.
        **kwargs
            Additional keyword arguments passed to the converter function.

        Returns
        -------
        xarray.Dataset
            Dataset representation of the input object.

        Raises
        ------
        TypeError
            If no converter is registered for the object's type.

        Examples
        --------
        >>> dt = DataTreeDitto()
        >>> arr = np.array([1, 2, 3])
        >>> ds = dt._convert_to_dataset(arr)
        >>> ds.data.values.tolist()
        [1, 2, 3]
        """
        obj_type = type(obj)

        if obj_type not in self._converters:
            raise TypeError(
                f"No converter registered for type {obj_type}. "
                f"Available converters: {list(self._converters.keys())}",
            )

        converter = self._converters[obj_type]["to_dataset"]
        return converter(obj, **kwargs)

    def _convert_from_dataset(self, dataset: xr.Dataset) -> Any:
        """Convert a dataset back to its original type if metadata exists.

        Parameters
        ----------
        dataset : xarray.Dataset
            Dataset to convert back to original type.

        Returns
        -------
        Any
            Original object type if conversion metadata exists, otherwise
            returns the dataset unchanged.

        Examples
        --------
        >>> arr = np.array([1, 2, 3])
        >>> ds = DataTreeDitto._numpy_to_dataset(arr)
        >>> dt = DataTreeDitto()
        >>> recovered = dt._convert_from_dataset(ds)
        >>> recovered.tolist()
        [1, 2, 3]
        """
        original_type = dataset.attrs.get("_ditto_original_type")

        if original_type is None:
            return dataset

        # Find converter by original type string
        for obj_type, converter_dict in self._converters.items():
            if f"{obj_type.__module__}.{obj_type.__name__}" == original_type:
                return converter_dict["from_dataset"](dataset)

        # Fallback: return dataset if converter not found
        return dataset

    def _intercept_assignment(func):
        """Decorator to intercept and convert assignments.

        Parameters
        ----------
        func : callable
            Function to wrap (typically __setitem__).

        Returns
        -------
        callable
            Wrapped function that automatically converts assigned values.
        """

        @wraps(func)
        def wrapper(self, key, value):
            if isinstance(
                value,
                (
                    DataTreeDitto,
                    xr.Dataset,
                    xr.DataArray,
                    xr.core.variable.Variable,
                    xr.core.coordinates.DataTreeCoordinates,
                ),
            ):
                return func(self, key, value)
            elif isinstance(value, DataTree):
                # Convert DataTree to DataTreeDitto
                new_ditto = DataTreeDitto(dataset=value.ds, name=key)
                # Recursively convert children
                for child_name, child in value.children.items():
                    new_ditto[child_name] = child
                return func(self, key, new_ditto)
            else:
                # Convert non-xarray object
                try:
                    dataset = self._convert_to_dataset(value)
                    new_ditto = DataTreeDitto(dataset=dataset, name=key)
                    return func(self, key, new_ditto)
                except TypeError:
                    raise TypeError(
                        f"Cannot assign object of type {type(value)} to DataTreeDitto. "
                        f"No converter registered for this type.",
                    )

        return wrapper

    @_intercept_assignment
    def __setitem__(self, key: str, value: Any) -> None:
        """Override setitem to handle automatic conversion.

        Parameters
        ----------
        key : str
            Name for the child node.
        value : Any
            Value to assign. Will be automatically converted to DataTreeDitto
            if it's not already an xarray object.

        Examples
        --------
        >>> dt = DataTreeDitto()
        >>> dt["child"] = np.array([1, 2, 3])
        >>> dt["child"].ds.data.values.tolist()
        [1, 2, 3]
        """
        super().__setitem__(key, value)

    @_convert_output_to_DataTreeDitto
    def __getitem__(self, key: str) -> Union["DataTreeDitto", Any]:
        """Override getitem to return DataTreeDitto instances.

        Parameters
        ----------
        key : str
            Name of the child node to retrieve.

        Returns
        -------
        DataTreeDitto
            The child node, converted to DataTreeDitto if necessary.

        Examples
        --------
        >>> dt = DataTreeDitto()
        >>> dt["child"] = np.array([1, 2, 3])
        >>> child = dt["child"]
        >>> isinstance(child, DataTreeDitto)
        True
        """
        return super().__getitem__(key)

    # @classmethod
    # def from_dict(cls, data=None, name=None):
    #    # Pass keyword arguments directly, without the '*'
    #    result = super().from_dict(data, name=name)
    #    if isinstance(result, DataTree) and not isinstance(result, DataTreeDitto):
    #        return cls._convert_datatree_to_ditto(result)
    #    return result

    @_convert_output_to_DataTreeDitto
    def map_over_datasets(
        self,
        func: Callable[..., Any],
        *args: Any,
        kwargs: Mapping[str, Any] | None = None,
    ) -> DataTree | tuple[DataTree, ...]:
        return super().map_over_datasets(func, *args, kwargs=kwargs)

    @_convert_output_to_DataTreeDitto
    def _unary_op(self, f, *args, **kwargs) -> DataTree:
        return super()._unary_op(f, *args, **kwargs)

    @_convert_output_to_DataTreeDitto
    def _binary_op(self, other, f, reflexive=False, join=None) -> DataTree:
        return super()._binary_op(other, f, reflexive, join)

    @_convert_output_to_DataTreeDitto
    def filter(self: DataTree, filterfunc: Callable[[DataTree], bool]) -> DataTree:
        return super().filter(filterfunc)

    @_convert_output_to_DataTreeDitto
    def match(self, pattern: str) -> DataTree:
        return super().match(pattern)

    @_convert_output_to_DataTreeDitto
    def mean(
        self,
        dim=None,
        *,
        skipna=None,
        keep_attrs=None,
        **kwargs,
    ):
        return super().mean(dim, skipna=skipna, keep_attrs=keep_attrs, **kwargs)

    @staticmethod
    def _convert_datatree_to_ditto(dt: DataTree) -> "DataTreeDitto":
        """Convert a DataTree to DataTreeDitto recursively.

        Parameters
        ----------
        tt : DataTree
            DataTree instance to convert.

        Returns
        -------
        DataTreeDitto
            Converted DataTreeDitto with all children also converted.
        """
        new_ditto = DataTreeDitto(dataset=dt.ds, name=dt.name)
        for child_name, child in dt.children.items():
            new_ditto[child_name] = DataTreeDitto._convert_datatree_to_ditto(child)
        return new_ditto

    def get_original(self, path: str = ".") -> Any:
        """Get the original object (before conversion) at the specified path.

        Parameters
        ----------
        path : str, default "."
            Path to the node. Use "." for current node, or child names
            separated by "/" for nested nodes.

        Returns
        -------
        Any
            Original object if conversion metadata exists, otherwise the dataset.
            Returns None if the node contains no data.

        Examples
        --------
        >>> arr = np.array([1, 2, 3])
        >>> dt = DataTreeDitto(arr)
        >>> original = dt.get_original()
        >>> original.tolist()
        [1, 2, 3]
        >>> dt["child"] = np.array([4, 5, 6])
        >>> dt.get_original("child").tolist()
        [4, 5, 6]
        """
        node = self if path == "." else self[path]

        if node.ds is None:
            return None

        # Get the actual dataset, not the view
        actual_dataset = node.ds._dataset if hasattr(node.ds, "_dataset") else node.ds

        return self._convert_from_dataset(actual_dataset)

    def to_datatree(self) -> DataTree:
        """Convert to a standard DataTree with all nodes as xarray objects.

        Returns
        -------
        DataTree
            A standard DataTree instance with all converted objects as datasets.
            Conversion metadata is preserved in dataset attributes.

        Examples
        --------
        >>> arr = np.array([1, 2, 3])
        >>> dt = DataTreeDitto(arr, name="test")
        >>> standard_dt = dt.to_datatree()
        >>> isinstance(standard_dt, DataTree)
        True
        >>> standard_dt.ds.data.values.tolist()
        [1, 2, 3]
        """
        # Get the actual dataset, not the view
        dataset = None
        if self.ds is not None:
            dataset = self.ds._dataset if hasattr(self.ds, "_dataset") else self.ds

        # Create new DataTree with current data
        new_dt = DataTree(dataset=dataset, name=self.name)

        # Recursively convert children
        for child_name, child in self.children.items():
            if isinstance(child, DataTreeDitto):
                new_dt[child_name] = child.to_datatree()
            else:
                new_dt[child_name] = child

        return new_dt

    def list_converted_nodes(self) -> dict[str, str]:
        """List all nodes that contain converted objects and their original types.

        Returns
        -------
        dict of str to str
            Mapping of node paths to original object type names. Paths use "/"
            as separator, with "/" representing the root node.

        Examples
        --------
        >>> dt = DataTreeDitto(np.array([1, 2, 3]))
        >>> dt["child"] = np.array([4, 5, 6])
        >>> converted = dt.list_converted_nodes()
        >>> "/" in converted
        True
        >>> "child" in converted
        True
        >>> converted["/"]
        'numpy.ndarray'
        """
        converted = {}

        def _check_node(node, path=""):
            if node.ds is not None:
                # Get the actual dataset, not the view
                actual_dataset = node.ds
                if hasattr(actual_dataset, "_dataset"):
                    actual_dataset = actual_dataset._dataset

                original_type = actual_dataset.attrs.get("_ditto_original_type")
                if original_type:
                    converted[path or "/"] = original_type

            for child_name, child in node.children.items():
                child_path = f"{path}/{child_name}" if path else child_name
                _check_node(child, child_path)

        _check_node(self)
        return converted

    def __repr__(self) -> str:
        """Enhanced representation showing conversion info.

        Returns
        -------
        str
            String representation including information about converted nodes
            and their original types.

        Examples
        --------
        >>> dt = DataTreeDitto(np.array([1, 2, 3]))
        >>> repr_str = repr(dt)
        >>> "Converted nodes:" in repr_str
        True
        >>> "numpy.ndarray" in repr_str
        True
        """
        base_repr = super().__repr__()

        # Add conversion information
        converted_nodes = self.list_converted_nodes()
        if converted_nodes:
            conversion_info = "\nConverted nodes:\n"
            for path, orig_type in converted_nodes.items():
                conversion_info += f"  {path}: {orig_type}\n"
            base_repr += conversion_info

        return base_repr
