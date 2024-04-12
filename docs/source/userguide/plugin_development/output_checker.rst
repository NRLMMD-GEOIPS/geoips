 .. dropdown:: Distribution Statement

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

.. _learn-about-output-checkers:

***************************************
Learn more about GeoIPS Output Checkers
***************************************

For any output that GeoIPS produces, we want to ensure that the output created is in a
correct state. For example, if a NetCDF file was outputted, we'd want to ensure that
this file has the correct data variables, comes from the correct date range, covers a
certain geospatial region, has the expected metadata, etc. For an image, we could check
that each pixel of the image matches a corresponding pixel from an output that we know
is correct. No matter the output, we want to ensure that whatever GeoIPS produces is
correct in its final state.

To implement this testing process, we have created an ``output_checkers`` interface
which checks the state of GeoIPS outputs. ``output_checker`` plugins at their core are
testing infrastructure for ensuring that output of a GeoIPS procflow matches what we
expect it to look like. This infrastructure requires two things:

#. A pre-generated output that we know is correct
#. Newly created GeoIPS output that should match that pre-generated output.

This way, we can compare the newly created output to an output that already know is
completely accurate.

While it's not feasible to have a pre-generated output for everything GeoIPS, and its
other plugin packages can create, we can set up a fairly large suite of pre-generated
outputs to ensure that each type of output is covered by a specific output checker
plugin. Currently, GeoIPS has output_checker plugins for four types of outputs:

#. geotiff
#. image
#. netcdf
#. text

GeoIPS has the capabilty to produce outputs different from what's listed above, however
currently we only support those types of output checkers, as those outputs cover just
about everything we've implemented in GeoIPS and it's corresponding plugin packages so
far.

The methods in which we check the output of a GeoIPS :ref:`Procflow<understanding-process-workflows>`
depends on the type of output that was produced. For ``geotiff`` output, we run a
``diff`` command between the produced geotiff file and it's corresponding pre-generated
accurate file. One a line-by-line basis, we check that each line of the produced geotiff
matches that of the pre-generated geotiff. We also have implemented unit-tests which
check that the data contained in a geotiff match what is contained in a pre-generated
geotiff.

For image outputs, we use the PIL ``pixelmatch`` library to ensure