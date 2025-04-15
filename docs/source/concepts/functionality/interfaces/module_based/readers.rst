.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _readers_functionality:

*****************
Readers in GeoIPS
*****************

A reader is a module-based GeoIPS plugin that reads data from a specific
source, such as, for example, Level 1b data from the GOES ABI sensor.
GeoIPS has a wide array of 
`built-in readers <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/modules/readers>`_
available for use, which are primarily focused on satellite-based meteorological data,
but can support nearly any type of environmental data.

Note that when developing readers, some variables and attributes are required
to be set to ensure compatibility with other components of GeoIPS. See the
:ref:`reader plugin development <describe-readers>`
tutorial for the list of required variables and attributes, as well as
information on developing and using a new reader.

Readers can be called in two ways:

1. **Specification at the Command Line:** Readers are specified as arguments at
the command line. For example, the ABI Level 1b NetCDF reader is called as follows:

   .. code-block:: bash

      --reader_name abi_netcdf

The
`ABI Infrared <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/tests/scripts/abi.static.Infrared.imagery_annotated.sh>`_
test script serves as an example of command line call utilizing the abi_netcdf reader.

2. **Direct Invocation:** Readers can be called within another program:

   .. code-block:: python

      from geoips.interfaces import readers
      reader_name = "abi_netcdf"
      data = readers.get_plugin(reader_name)
