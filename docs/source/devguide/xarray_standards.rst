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

.. _xarray_standards:

Xarray and NetCDF Metadata Standards
======================================

All GeoIPS readers read data into xarray Datasets - a separate dataset for
each shape/resolution of data - and contain standard metadata information for
standardized processing.

Readers should return a dictionary of the resulting xarray Datasets,
with human readable keys for the different datasets
(no standard for dictionary key names).


Xarray Standard Variables
-------------------------

Internal to GeoIPS, our xarray standards include the following variables for
automated temporal and spatial sectoring.

* 'latitude' - REQUIRED 2d array the same shape as data variables
* 'longitude' - REQUIRED 2d array the same shape as data variables
* 'timestamp' - OPTIONAL 2d array the same shape as data variables

*NOTE: Additional methods of storing spatial and temporal information
will be implemented in the future for efficiency, but currently latitude
and longitude arrays are strictly required, and timestamp array is required
for automated temporal sectoring*

Xarray Standard Attributes
--------------------------

The following standard attributes are used internally to GeoIPS for consistent
generation of titles, legends, regridding, etc

* 'source_name' - REQUIRED
* 'platform_name' - REQUIRED
* 'data_provider' - REQUIRED
* 'start_datetime' - REQUIRED
* 'end_datetime' - REQUIRED
* 'interpolation_radius_of_influence' - REQUIRED
  used for pyresample-based interpolation

The following optional attributes can be used within processing if available.

* 'original_source_filenames' - OPTIONAL

  * list of strings containing names of all files that went into
    the current dataset. To ensure consistent output between users,
    these file names can either be

    * base paths, including only the filename and excluding the path
      altogether, or
    * full paths with GeoIPS environment variables replacing specific paths
      (ie, $GEOIPS_OUTDIRS, $GEOIPS_TESTDATA_DIR, etc)

* 'filename_datetimes' - OPTIONAL

  * list of datetime objects corresponding to the datetime listed in
    each of the 'original_source_filenames'. List must be same
    length as 'original_source_filenames'
* 'area_definition' - OPTIONAL

  * specify area_definition current dataset is registered to, if applicable
* 'registered_dataset' - OPTIONAL

  * True if current dataset is registered to a specific area_definition,
    False otherwise
* 'minimum_coverage' - OPTIONAL

  * if specified, products will not be generated with
    coverage < minimum_coverage
* 'sample_distance_km' - OPTIONAL

  * if specified, sample_distance_km can be used to produce
    a "minimum" sized image.  Web images are often up sampled to
    provide a conveniently sized image for viewing with titles/legends,
    this allows producing minimal sized "clean" imagery for overlaying
    in external viewers (such as the Automated Tropical Cyclone
    Forecasting System)


NetCDF CF Standards
--------------------------
All additional attributes should follow the
**NetCDF Climate and Forecast (CF) Conventions**.

Attributes and metadata on output NetCDF files should follow the
**CF Metadata Conventions**

* http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html

Names of attributes describing individual products and variables in output
NetCDF files should use
**CF Standard Names** when available

* http://cfconventions.org/Data/cf-standard-names/76/build/cf-standard-name-table.html
