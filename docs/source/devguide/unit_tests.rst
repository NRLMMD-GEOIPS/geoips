 | # # # Distribution Statement A. Approved for public release. Distribution unlimited.
 | # # #
 | # # # Author:
 | # # # Naval Research Laboratory, Marine Meteorology Division
 | # # #
 | # # # This program is free software: you can redistribute it and/or modify it under
 | # # # the terms of the NRLMMD License included with this program. This program is
 | # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 | # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
 | # # # for more details. If you did not receive the license, for more information see:
 | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

.. _unit_tests:

###################
GeoIPS Unit Testing
###################

Follow these steps when making new readers, to conform to 
geoips unit testing structure.


*****************************
GeoIPS Unit Testing Structure
*****************************
Unit testing in GeoIPS provide a quick and simple way to check
conformity and validity in GeoIPS. Unit tests are performed through
pytest, and check for xarray conformity (See: :ref:`xarray_standards`),
reader functionality (See: :ref:`describe-readers`), and test data validity. 
Unit testing is preformed through functionality tests (test_all) and 
github workflows. 

*******************************
GeoIPS Unit Testing for Readers
*******************************
When desiging a new reader, it is highly recommended that users
include two functions to allow for unit testing. These functions are 
called from the unit testing framework for each reader. Both of these 
functions are described below, with the reader sar_winds_netcdf as an example:

.. code-block:: python

    def get_test_files(test_data_dir):
        """Generate testing xarray from test data."""
        # filepath is the locaiton of test data in $GEOIPS_TESTDATA_DIR
        filepath = test_data_dir + "/test_data_sar/data/*.nc"
        filelist = glob.glob(filepath)
        
        if len(filelist) == 0:
            # check that the filelist is non-empty
            raise NameError("No files found")
        # Call the reader
        tmp_xr = call(filelist)
        return tmp_xr


    def get_test_parameters():
        """Generate test data key for unit testing."""
        # Return a key and variable with data in them to check contents
        return [{"data_key": "WINDSPEED", "data_var": "wind_speed_kts"}]
