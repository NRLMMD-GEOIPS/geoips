Guide to Writing a GeoIPS Reader
================================

Overview
--------
A GeoIPS reader is a module-based plugin that reads data from specific sources (satellite data, environmental data, etc.) and formats it for use within the GeoIPS framework.

Reader Structure
---------------
1. **Call Function** (Required)
   
   - Main driver that processes input files
   - Accepts file names and control parameters
   - Returns dictionary of xarray Datasets

2. **Read Functions** (Recommended)
   
   - Handle actual data reading from files
   - Convert data into xarray format

3. **Utility Functions** (Optional)
   
   - Help with data conversion/manipulation
   - Format time, coordinates, etc.

Required Output Components
-------------------------

Xarray Variables
~~~~~~~~~~~~~~
- ``latitude``, ``longitude`` (REQUIRED): 2D arrays matching data variables
- ``time`` (OPTIONAL): 2D array for temporal information
- Variables of interest: Should match names used in downstream plugins

Xarray Standard Attributes
~~~~~~~~~~~~~~~~~~~~~~~~
**Required Attributes**

- ``source_name``: Identifier used by downstream plugins
- ``platform_name``: Data platform
- ``data_provider``: Source of the data
- ``start_datetime``: Time of first observation
- ``end_datetime``: Time of final observation
- ``interpolation_radius_of_influence``: Used for pyresample-based interpolation

**Optional Attributes**

- ``source_file_names``: List of files used (use base paths or paths with GeoIPS environment variables)
- ``source_file_attributes``: Dictionary with file names as keys and their attributes as values
- ``source_file_datetimes``: List of datetime objects for each source file
- ``area_definition``: Area definition if dataset is registered to one
- ``registered_dataset``: True if registered to a specific area_definition, False otherwise
- ``minimum_coverage``: Minimum coverage threshold for product generation
- ``sample_distance_km``: Used to produce minimal sized imagery for external viewers

Implementation Tips
------------------
1. Handle 1D vs 2D variables consistently
2. Convert time formats to datetime objects
3. Only read required channels when possible
4. Implement ``metadata_only`` option for efficiency
5. Return a dictionary of xarrays with human-readable keys
6. Handle missing or invalid data appropriately with masks
7. Apply proper scaling factors and offsets to raw data
8. Consider memory usage for large datasets

Example Usage
-------------
.. code-block:: bash

   # Command line usage
   geoips run --reader_name my_reader_name

.. code-block:: python

   # Direct invocation
   from geoips.interfaces import readers
   reader_name = "my_reader_name"
   reader = readers.get_plugin(reader_name)

Reader Parameters
-----------------
- ``metadata_only``: When True, only read metadata without loading full dataset
- ``chans``: List of specific channels/variables to read (for efficiency)
- ``area_def``: Specify region to read (spatial subsetting)
- ``self_register``: Specify a dataset name to use as a point of reference for interpolate/convert all other arrays to be the same shape.

Reader Template
---------------
.. code-block:: python

   """
   Template for a GeoIPS reader.
   """

   import logging
   import numpy as np
   import xarray as xr
   from datetime import datetime
   from geoips.interfaces import readers

   # Define required plugin attributes
   interface = "readers"
   family = "standard"
   name = "my_reader_name"

   LOG = logging.getLogger(__name__)

   def read_data_file(fname, chans=None, metadata_only=False):
       """Read data from a single file.
       
       Parameters
       ----------
       fname : str
           Path to the data file
       chans : list, optional
           List of channels/variables to read
       metadata_only : bool, optional
           If True, only read metadata
           
       Returns
       -------
       xarray.Dataset
           Dataset containing the data
       """
       # Create empty dataset
       dataset = xr.Dataset()
       
       # Read file and extract metadata
       # YOUR CODE HERE
       
       # Set required attributes
       dataset.attrs["source_name"] = "your_source"
       dataset.attrs["platform_name"] = "your_platform"
       dataset.attrs["data_provider"] = "your_provider"
       dataset.attrs["start_datetime"] = datetime(2023, 1, 1)  # Replace with actual time
       dataset.attrs["end_datetime"] = datetime(2023, 1, 1)    # Replace with actual time
       dataset.attrs["interpolation_radius_of_influence"] = 3000  # in meters
       
       # Optional attributes
       dataset.attrs["source_file_names"] = [fname]
       dataset.attrs["sample_distance_km"] = 2.0  # Example resolution
       
       # Return early if only metadata is requested
       if metadata_only:
           LOG.debug("metadata_only requested, returning without reading data")
           return dataset
       
       # Read actual data
       # YOUR CODE HERE
       
       # Create latitude and longitude arrays (required)
       # dataset["latitude"] = ...
       # dataset["longitude"] = ...
       
       # Add variables of interest
       # dataset["variable_name"] = ...
       
       return dataset

   def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
       """Read data from one or more files.
       
       Parameters
       ----------
       fnames : list
           List of strings, full paths to files
       metadata_only : bool, default=False
           Return before reading data if True
       chans : list, default=None
           List of desired channels/variables
       area_def : pyresample.AreaDefinition, default=None
           Specify region to read
       self_register : bool, default=False
           Register all data to a specified dataset
           
       Returns
       -------
       dict
           Dictionary of xarray.Dataset objects
       """
       return readers.read_data_to_xarray_dict(
           fnames,
           _call_single_time,
           metadata_only,
           chans,
           area_def,
           self_register,
       )

   def _call_single_time(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
       """Process a single file or group of files for one time period.
       
       Parameters are the same as the main call function.
       """
       fname = fnames[0]  # For single file processing
       
       # Read the data
       dataset = read_data_file(fname, chans=chans, metadata_only=metadata_only)
       
       # Return dictionary with dataset
       return {"DATA": dataset, "METADATA": dataset[[]]}


Testing Your Reader
-------------------
1. Create unit and/or integration tests to verify your reader works correctly
2. Test with various input files
3. Verify all required attributes and variables are present
4. Check that data values are properly scaled and masked
5. Validate time and coordinate information

Common File Formats and Libraries
--------------------------------
- NetCDF: Use ``xarray`` or ``netCDF4``
- HDF4/HDF5: Use ``h5py`` or ``pyhdf``
- GRIB: Use ``pygrib``
- Binary: Use ``numpy`` with appropriate data types
- CSV/Text: Use ``pandas``

Remember to define top-level attributes: ``interface``, ``family``, and ``name`` in your reader module.
