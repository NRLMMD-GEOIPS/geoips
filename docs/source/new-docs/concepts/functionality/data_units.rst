:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _data_units:

Common GeoIPS Data Units
************************

GeoIPS readers intake several common data processing levels, but
sources and units can vary. Within geoips, unit conversions, scale factors,
and data manipulation can occur, however several common units are expected per
data level. If ingesting similar products with different processing for the same
sensor (i.e. VIIRS L1 products from NASA versus CSPP), verify products and units rigorously.

When referring to data processing levels,
GeoIPS is referencing `EOSDIS Processing Levels <https://ghrc.nsstc.nasa.gov/home/proc_level>`_

Level 1 Data
------------

Technically, the lowest level of data that GeoIPS can read, ingest, and mainpulate, is
geolocated, calibrated data (Level 1). Standard units are the following:

- Brightness Temperature: Kelvin or Celcius
- Reflectance: Unitless, common range of 1-100
- Radiance: SI units (W/cm^2 per steradian)

Conversion can be made in brightness temperature, and scale factor, gamma corrections
can be used within product definitions for individual sensors.

Level 2 Data
------------

Level 2 data can range in variable type and format, but common
products include resampled level 1 data, and wind products.
Common variables and respective units include:

- Windspeed: Knots or Meters per second (conversions available)
- Wind Direction: Meterological convention

Level 3/4 Data
--------------

Level 3 and 4 products generally fall under GeoIPS data_fusion products, or
require additional processing, readers, or products to describe unique
variables. Users should refer to current products as guidance or create
seperate products for the data.
