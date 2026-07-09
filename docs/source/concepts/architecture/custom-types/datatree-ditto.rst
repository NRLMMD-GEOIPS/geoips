DataTreeDitto
=============

DataTreeDitto is a subclass of xarray's DataTree that allows you to store and work with hierarchical tree structures
where each node can contain not only xarray objects but also other types of data (like NumPy arrays, lists, or custom
types). It automatically converts these types to xarray.Dataset and preserves enough metadata to recover the original
object later.

The ``DataTreeDitto`` class extends :class:`xarray.DataTree` to support automatic conversion of non-xarray objects into
xarray datasets. This allows users to store data types such as NumPy arrays or lists in a hierarchical tree format while
preserving enough metadata for reversible conversion.

The name "Ditto" is inspired by the Pokémon character that mimics others — similarly, this class mimics ``DataTree``,
with added functionality for type handling.

Usage Example::

    >>> import numpy as np
    >>> from geoips.utils.types.datatree_ditto import DataTreeDitto
    >>> arr = np.array([[1, 2], [3, 4]])
    >>> dt = DataTreeDitto(arr)
    >>> dt.ds.data.values.tolist()
    [[1, 2], [3, 4]]
    >>> dt.get_original().tolist()
    [[1, 2], [3, 4]]

DataTreeDitto internally relies on xarray's DataTrees. Metadata required for
round-trip conversion to/from non-xarray objects is stored in dataset attributes
prefixed with ``_ditto_``.

Custom converters can be registered using ``.register_converter()`` for full extensibility and some basic converters
(e.g., for numpy nd-arrays) are provided.

Supported Data Types
====================

Built-in converters are registered for the following types:

* ``numpy.ndarray`` — stored as a single-variable ``xarray.Dataset`` with auto-generated dimension names

Additional types can be supported by registering custom converters via
``DataTreeDitto.register_converter(type, to_dataset_func, from_dataset_func)``.

Type Resolution Priority
------------------------

When converting an object, ``DataTreeDitto`` first checks for an exact type
match. If none is found, it falls back to ``isinstance``-based matching,
selecting the most specific registered type (deepest in the object's MRO).
For example, if only ``numpy.ndarray`` is registered, a ``numpy.masked_array``
will match the ``numpy.ndarray`` converter since ``masked_array`` is a
subclass of ``ndarray``.

Operations on Converted Data
============================

DataTreeDitto preserves its type across tree operations. Methods that would
normally return a plain ``DataTree`` return ``DataTreeDitto`` instead:

.. code-block:: python

    >>> dt = DataTreeDitto(np.array([[1, 2], [3, 4]]), name="root")
    >>> sliced = dt.isel(dim_0=slice(0, 1))
    >>> isinstance(sliced, DataTreeDitto)
    True

    >>> filtered = dt.filter(lambda n: n.name == "root")
    >>> isinstance(filtered, DataTreeDitto)
    True

    >>> averaged = dt.mean()
    >>> isinstance(averaged, DataTreeDitto)
    True

Note that accessing a child node via ``__getitem__`` (``dt["child"]``) always
returns a ``DataTreeDitto``, even when the child contains a single data variable
(as opposed to native ``DataTree`` which may return a ``DataArray`` in that case).

Using DataTreeDitto
===================

Because DataTreeDittos are xarray DataTrees,
you can use DataTreeDitto to do anything you can do with an :class:`xarray.DataTree`:

.. code-block:: python

    >>> import xarray
    >>> dtd = DataTreeDitto()
    >>> dt = xarray.DataTree()
    >>> isinstance(dt, xarray.DataTree) # A DataTree is a DataTree
    True
    >>> isinstance(dt, DataTreeDitto) # A DataTree is NOT a DataTreeDitto
    False
    >>> isinstance(dtd, DataTreeDitto) # A DataTreeDitto is a DataTreeDitto
    True
    >>> isinstance(dtd, xarray.DataTree) # A DataTreeDitto IS a DataTree
    True

Automatic Conversion of Children
--------------------------------

.. code-block:: python

   tree = DataTreeDitto()
   tree["child_1"] = np.array([10, 20])
   tree["child_2"] = {"a": "b"}  # Will raise TypeError unless converter is registered

   # Get child as DataTreeDitto instance:
   child = tree["child_1"]
   assert isinstance(child, DataTreeDitto)

Hierarchical Tree Structure:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   tree["sub"]["nested"] = np.ones((2,))
   print(tree.to_datatree())  # Returns standard xarray.DataTree version for compatibility.

Round-trip Recovery:
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   recovered = tree.get_original("sub/nested")
   assert isinstance(recovered, np.ndarray)

Advanced Usage: Custom Converters
---------------------------------

You can register custom converters for your own data types.

Example: Handling Lists
^^^^^^^^^^^^^^^^^^^^^^^

Suppose you want to allow lists to be stored in a tree node.

Define conversion functions:

.. code-block:: python

   def list_to_dataset(lst, name="data", **kwargs):
       return DataTreeDitto._numpy_to_dataset(np.array(lst), name=name)

   def dataset_to_list(ds: xr.Dataset):
       return ds[list(ds.data_vars)[0]].values.tolist()

Register the converter:

.. code-block:: python

   DataTreeDitto.register_converter(list, list_to_dataset, dataset_to_list)

Use it like this:

.. code-block:: python

   dt = DataTreeDitto([1, 2, 3])
   print(dt.get_original())  # [1, 2, 3]

Inspecting Converted Nodes
--------------------------

To see which nodes have been converted from non-xarray objects:

.. code-block:: python

   converted_info = dt.list_converted_nodes()
   for path_str, orig_type in converted_info.items():
       print(f"{path_str}: {orig_type}")

Interoperability with Standard xarray Trees
-------------------------------------------

If needed for downstream compatibility (e.g., saving or visualization), convert back using ``.to_datatree()``:

.. code-block:: python

   import xarray as xr
   standard_tree = dt.to_datatree()
   assert isinstance(standard_tree, xr.DataTree)

Debugging Tips:
---------------

- Always provide a unique name when creating or assigning new nodes.
- Use ``get_original(path)`` instead of directly accessing ``.ds`` if working with converted data.
- Avoid registering overly generic converters (e.g., ``object``) — this could make debugging difficult.
- You can override or remove previously registered converters by re-calling ``register_converter()``.

If you try to assign an unsupported type without registering a converter::

    TypeError: No converter registered for type <class 'dict'>

To debug representation info at any time::

    >>> print(repr(tree))  # assuming 'tree' is a DataTreeDitto instance

This will include paths and original types of all converted nodes.
