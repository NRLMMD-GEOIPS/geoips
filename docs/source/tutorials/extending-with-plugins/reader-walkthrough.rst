.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _reader-walkthrough:

Build a Reader: a hands-on walkthrough
**************************************

This tutorial builds two complete, class-based readers from scratch and runs them through
:ref:`Order-Based Processing <order-based-processing>`. It complements the conceptual
:ref:`reader reference <describe-readers>` with a step-by-step example.

We build:

#. **A single-file reader** — for data delivered in one file (as geostationary sensors
   often are).
#. **A multi-file reader** — for data spread across many files (as polar-orbiter passes
   often are).

To keep the focus on the reader itself, both examples use a small fictional sensor whose
data are stored in HDF5. Apply the same patterns to your own data.

.. contents::
   :local:

What a reader does
==================

A reader does two jobs:

* It reads a data file (or files) into the GeoIPS internal representation — a dictionary of
  ``xarray.Dataset`` objects.
* It reports the **metadata** GeoIPS needs to decide whether and how to process the data
  (data source, start/end times, geolocation).

At minimum, a reader must return datasets containing:

* ``latitude`` and ``longitude`` (2-D, matching the data),
* your data variable(s), named however you like,
* and the required attributes ``source_name``, ``start_datetime``, and ``end_datetime``.

.. important::

   Variable names and capitalization matter. The variable names your reader produces must
   match the names your :ref:`product <create-a-product>` requests.

Where readers fit in
====================

In :ref:`Order-Based Processing <order-based-processing>`, a reader is a ``reader`` step
in a workflow. GeoIPS may call your reader **twice**: first with ``metadata_only=True`` to
read just the metadata (so it can decide whether the run is worth doing and set up the
area definition), then again to read the full data. Always honor ``metadata_only`` — see
:ref:`challenge #1 <reader-challenge-1>`.

.. note::

   A reader's ``call`` method keeps the argument names ``fnames`` and ``chans``. When a
   reader runs as an OBP workflow step, GeoIPS supplies these as ``filenames`` and
   ``variables`` and renames them for you — so author your reader with ``fnames`` /
   ``chans`` (as all GeoIPS readers do) and reference ``filenames`` / ``variables`` in the
   workflow YAML.

Know your data first
====================

Before writing a reader, understand your file's contents — its variables, dimensions, and
metadata attributes. Documentation, ``ncdump``/``HDFView`` (NetCDF4/HDF5), or ``wgrib``
(GRIB) all help. A quick throwaway script also works for NetCDF4/HDF5:

.. code-block:: python

    import xarray

    xobj = xarray.open_dataset("myfile.h5")

    print("FILE METADATA ATTRIBUTES")
    for attr in xobj.attrs:
        print(attr, ":", xobj.attrs[attr])

    print("\nVARIABLES + METADATA ATTRIBUTES")
    for var in xobj:
        print(var, ":", xobj[var].attrs or "No attributes")

Reader #1 — all data in one file
================================

Create the reader in your package's class-based readers directory:

::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/classes/readers

Create a file named ``fl89_value_hdf5.py``. The naming convention is
``<source>_<datatype>_<format>`` (recommended, not required).

Plugin header and class
-----------------------

Start with a module docstring, imports, the logger, and the class attributes that tell
GeoIPS what this plugin is:

.. code-block:: python

    """Reader for the single-file FL-89 sensor (HDF5)."""

    # Python standard libraries
    import datetime
    import logging

    # Third-party libraries
    import numpy
    import xarray

    from geoips.interfaces.class_based.readers import BaseReaderPlugin

    LOG = logging.getLogger(__name__)


    class GreatValueHDF5ReaderPlugin(BaseReaderPlugin):
        """Read FL-89 data from a single HDF5 file."""

        interface = "readers"
        family = "standard"
        name = "fl89_value_hdf5"
        source_names = ["fl89"]

``interface``/``family``/``name`` identify the plugin; ``source_names`` declares which data
sources it can read (products reference the same source name).

The ``call`` method
-------------------

``call`` is what GeoIPS invokes to use your reader. Readers receive a standard set of
arguments:

.. code-block:: python

        def call(self, fnames, metadata_only=False, chans=None, area_def=None,
                 self_register=False):
            """Read FL-89 data from a list of filenames.

            Parameters
            ----------
            fnames : list of str
                Full paths to the files to read.
            metadata_only : bool, default=False
                Return after reading metadata only, if True.
            chans : list of str, default=None
                Channels/variables requested by the product; read all if None.
            area_def : pyresample.AreaDefinition, default=None
                Region to constrain the read (if the reader implements it).
            self_register : str or bool, default=False
                Return unprojected/self-registered data (if implemented).

            Returns
            -------
            dict of xarray.Dataset
                Keyed by descriptive dataset ids, plus a ``"METADATA"`` entry.

            See Also
            --------
            :ref:`xarray_standards`
            """

.. note::

   ``area_def``, ``self_register``, ``chans``, and any other argument only do something if
   *your reader* acts on them. They are part of the standard signature, but honoring them
   is up to you.

Read the metadata
-----------------

This sensor delivers a single file, so read it and set the required attributes:

.. code-block:: python

            fname = fnames[0]  # this sensor delivers a single file
            LOG.interactive("Reading %s", fname)

            # xarray reads HDF5/NetCDF4 without importing the backend directly
            xobj = xarray.open_dataset(fname)

            sdt = datetime.datetime.strptime(
                xobj.attrs["time_data_start"], "%Y-%m-%dT%H:%M:%SZ"
            )
            edt = datetime.datetime.strptime(
                xobj.attrs["time_data_end"], "%Y-%m-%dT%H:%M:%SZ"
            )

            xobj.attrs["start_datetime"] = sdt
            xobj.attrs["end_datetime"] = edt
            xobj.attrs["source_name"] = "fl89"
            xobj.attrs["platform_name"] = "fl89"
            xobj.attrs["data_provider"] = "Frito-Lay"

Return early for the metadata-only pass
---------------------------------------

.. _reader-challenge-1:

.. admonition:: Challenge #1 — readers are called twice
   :class: tip

   Because GeoIPS calls your reader once with ``metadata_only=True`` and again with
   ``metadata_only=False``, a large dataset (ABI, VIIRS, …) will be read **twice** if you
   don't return early — doubling the memory and time cost. Always return after the metadata
   pass:

.. code-block:: python

            if metadata_only is True:
                LOG.info("metadata_only requested. Returning")
                return {"METADATA": xobj}

.. _reader-challenge-2:

Build 2-D geolocation
---------------------

.. admonition:: Challenge #2 — 1-D geolocation
   :class: tip

   Some datasets store 1-D latitude/longitude to save space, but GeoIPS expects
   ``latitude``/``longitude`` to be 2-D, matching the data. Build a 2-D grid with
   ``numpy.meshgrid``:

.. code-block:: python

            LOG.info("Obtaining lat/lon from xarray")
            lat = xobj.variables["Latitude"][...]
            lon = xobj.variables["Longitude"][...]

            LOG.info("Creating 2D lat/lon grid")
            lon_final, lat_final = numpy.meshgrid(lon, lat)

            xobj["latitude"] = xarray.DataArray(
                numpy.ma.array(lat_final), dims=("lat", "lon")
            )
            xobj["longitude"] = xarray.DataArray(
                numpy.ma.array(lon_final), dims=("lat", "lon")
            )

            # Drop the original 1-D coordinates now that we have 2-D versions
            xobj = xobj.drop_vars(["Latitude", "Longitude"])

Return the data
---------------

Return a dictionary of xarray datasets — one (or more) named datasets plus a ``METADATA``
entry — and declare ``PLUGIN_CLASS`` so the registry can find your reader:

.. code-block:: python

            return {"FL89": xobj, "METADATA": xobj[[]]}


    PLUGIN_CLASS = GreatValueHDF5ReaderPlugin

Your first reader is complete. Check your indentation: everything from ``class …`` is
indented three spaces, everything from ``def call…`` an additional three, and
``PLUGIN_CLASS`` has no indentation.

Reader #2 — data spread across many files
=========================================

Polar-orbiter passes are often delivered as many files. This reader reads one *or* many
files and stitches them together. Create ``fl98_value_hdf5.py`` in the same directory,
with the same header pattern:

.. code-block:: python

    """Reader for the multi-file FL-98 sensor (HDF5)."""

    import datetime
    import logging

    import numpy
    import xarray

    from geoips.interfaces.class_based.readers import BaseReaderPlugin

    LOG = logging.getLogger(__name__)


    class Fl98ReaderPlugin(BaseReaderPlugin):
        """Read FL-98 data from one or more HDF5 files."""

        interface = "readers"
        family = "standard"
        name = "fl98_value_hdf5"
        source_names = ["fl98"]

Metadata from the first and last files
--------------------------------------

With multiple files, derive the start/end times from the first and last files. Read only
what you need for the metadata pass:

.. code-block:: python

        def call(self, fnames, metadata_only=False, chans=None, area_def=None,
                 self_register=False):
            """Read FL-98 data from a list of filenames."""
            xobj_metadata = xarray.Dataset()

            xobj_temp = xarray.open_dataset(fnames[0])
            sdt = datetime.datetime.strptime(
                xobj_temp.attrs["time_data_start"], "%Y-%m-%dT%H:%M:%SZ"
            )
            xobj_temp.close()

            xobj_temp = xarray.open_dataset(fnames[-1])
            edt = datetime.datetime.strptime(
                xobj_temp.attrs["time_data_end"], "%Y-%m-%dT%H:%M:%SZ"
            )
            xobj_temp.close()

            xobj_metadata.attrs["start_datetime"] = sdt
            xobj_metadata.attrs["end_datetime"] = edt
            xobj_metadata.attrs["source_name"] = "fl98"
            xobj_metadata.attrs["platform_name"] = "fl98"
            xobj_metadata.attrs["data_provider"] = "Frito-Lay"

            if metadata_only is True:
                return {"METADATA": xobj_metadata}

.. note::

   Using ``fnames[0]`` and ``fnames[-1]`` assumes the file list is sorted. Verify the
   ordering for your own data rather than relying on it.

A dedicated read function
-------------------------

There are many valid ways to structure a reader. Here we factor the per-file read into a
helper method that reads geolocation and only the requested channels. Add it to the class,
above ``call``:

.. code-block:: python

        def read_fl98_data(self, fname, chans=None):
            """Read one FL-98 file; return a dict of xarray datasets."""
            import h5py

            datain = h5py.File(fname)
            return_dict = {}
            temp_xarray = xarray.Dataset()

            # Geolocation → 2-D (see Challenge #2)
            lat = datain["Latitude"][:]
            lon = datain["Longitude"][:]
            coordict = dict(
                num_lats=range(lat.shape[0]), num_lons=range(lon.shape[0])
            )
            dims = ("num_lats", "num_lons")
            lon_final, lat_final = numpy.meshgrid(lon, lat)
            temp_xarray["latitude"] = xarray.DataArray(
                lat_final, coords=coordict, dims=dims
            )
            temp_xarray["longitude"] = xarray.DataArray(
                lon_final, coords=coordict, dims=dims
            )

            # Read ONLY the requested channels
            for chan in chans:
                temp_xarray[chan] = xarray.DataArray(
                    datain[chan][:, :], coords=coordict, dims=dims
                )

            datain.close()
            return_dict["DATA"] = temp_xarray
            return return_dict

.. admonition:: Challenge #3 — awkward variable names
   :class: tip

   Some sensors name variables in ways that are unwieldy as GeoIPS variables (e.g. AMSR2's
   ``Brightness_Temperature_89_GHz_AH``). Map source names to GeoIPS names as you read:

   .. code-block:: python

       varnames = {"Brightness_Temperature_89_GHz_AH": "tb89hA", ...}
       for src_name, geoips_name in varnames.items():
           sub_xarray[geoips_name] = full_xarray[src_name]

.. tip::

   Reading only the channels the product requested (``chans``) keeps memory and I/O down —
   don't read variables nobody asked for.

Loop, stack, and concatenate
----------------------------

Back in ``call`` (after the ``metadata_only`` return), read every file, stack each
variable along a new dimension, then concatenate:

.. code-block:: python

            xarray_fl98 = {}  # dict to be returned

            for fname in fnames:
                temp_dict = self.read_fl98_data(fname, chans)
                for key in temp_dict:
                    stacked = temp_dict[key].stack(zed=temp_dict[key].dims)
                    if key in xarray_fl98:
                        xarray_fl98[key].append(stacked)
                    else:
                        xarray_fl98[key] = [stacked]

            for key in xarray_fl98:
                xarray_fl98[key] = xarray.concat(xarray_fl98[key], dim="zed")

            for dsname, curr_xarray in xarray_fl98.items():
                curr_xarray.attrs["start_datetime"] = sdt
                curr_xarray.attrs["end_datetime"] = edt
                curr_xarray.attrs["source_name"] = "fl98"
                curr_xarray.attrs["platform_name"] = "fl98"
                curr_xarray.attrs["data_provider"] = "Frito-Lay"

            xarray_fl98["METADATA"] = list(xarray_fl98.values())[0][[]]
            return xarray_fl98


    PLUGIN_CLASS = Fl98ReaderPlugin

.. admonition:: Challenge #4 — overlapping / masked data
   :class: tip

   ``stack`` uses the most recent file's mask, which can silently drop data where files
   overlap with masked space. Be careful with geographically overlapping files.

Testing your reader
===================

To produce imagery, GeoIPS needs a **product** (what to make from the data) and a
**workflow** (the ordered steps that make it).

1. Create a product
-------------------

::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products

Create ``fl89.yaml``. The variable names must match what your reader produced:

.. code-block:: yaml

    interface: products
    family: list
    name: fl89
    docstring: The fl89 products configuration.
    spec:
      products:
        - name: coupon
          source_names: ["fl89"]
          docstring: FL-89 coupon RGB.
          product_defaults: RGB-Default
          spec:
            variables: ["ChanRed", "ChanGrn", "ChanBlu"]
            scale_factor: 0.003

See the :ref:`products tutorial <create-a-product>` for more on product plugins.

2. Create a workflow
--------------------

::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/workflows

Create ``fl89_coupon.yaml`` — a workflow that reads the data with your new reader and
produces the ``coupon`` product:

.. code-block:: yaml

    apiVersion: geoips/v1
    interface: workflows
    family: order_based
    name: fl89_coupon
    docstring: FL-89 coupon RGB imagery.
    package: <your_package>
    spec:
      globals:
        product_name: coupon
      steps:
        sector:
          kind: sector
          name: global_cylindrical
        reader:
          kind: reader
          name: fl89_value_hdf5
          depends_on: [sector]
        fl89_coupon:
          kind: product
          name: [fl89, coupon]
          depends_on: [reader, sector]
        output_formatter:
          kind: output_formatter
          name: imagery_annotated
          depends_on:
            - fl89_coupon.algorithm
            - fl89_coupon.colormapper
            - sector

3. Register and run
-------------------

Install the package (only needed when you add new Python classes/modules) and rebuild the
registries (needed whenever you add a class/module or edit a YAML plugin):

.. code-block:: bash

    cd $GEOIPS_PACKAGES_DIR
    pip install -e $MY_PKG_NAME
    geoips config create-registries

Then run the workflow on your data file:

.. code-block:: bash

    geoips run order_based fl89_coupon /path/to/your/fl89_data.h5

On success the log ends with ``Return Value 0`` and prints the path to the output image.
The FL-98 reader is tested the same way — create an ``fl98`` product and an ``fl98_coupon``
workflow, then run it against your set of FL-98 files.

.. tip::

   When do you need to reinstall vs. rebuild registries?

   * ``pip install -e`` — after adding a **new** Python class or module.
   * ``geoips config create-registries`` — after adding a class/module *or* editing a YAML
     plugin.
   * Neither — when editing the body of an already-installed, already-registered plugin in
     place.

More challenges to keep in mind
===============================

* **Multiple file formats for one sensor.** Some sensors ship the same data in different
  formats (e.g. VIIRS from NASA as HDF5 vs. NOAA as NetCDF), often structured completely
  differently — you may need more than one reader.
* **L1–L3 products.** You can write one "super reader" or split across smaller readers per
  processing level.
* **Close your files.** Prefer context management (``with h5py.File(...) as f:``); if you
  open a file another way, make sure you ``close()`` it.

In conclusion
=============

Writing a reader is as much art as science — there are many valid approaches, and the
methods here won't fit every dataset. Choose what works for your data, and be mindful of
your users' computational resources as you go.

See also
========

* :ref:`describe-readers` — the reader interface reference.
* :ref:`writing-class-based-plugins` — the class-based plugin contract.
* :ref:`xarray_standards` — required variables and attributes.
* :ref:`order-based-processing` — the workflow model your reader runs in.
