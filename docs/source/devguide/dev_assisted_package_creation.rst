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

Developer Assisted Package Creation
===================================

Why We Assist With Package Creation
-----------------------------------

The GeoIPS Development team is committed to integrating a variety of geospatial
processing routines into GeoIPS, or as a standalone packages that can interact with
GeoIPS. Specifically we developers at CIRA are tasked with integrating proprietary
software developed by researchers to work alongside GeoIPS. If you have access, see the
`GeoIPS GLM Package <https://bear.cira.colostate.edu/overcast/geoips_glm>`_ for an
example of a standalone package that implements GREMLIN and GLM
(Global Lightning Mapper) routines working alongside GeoIPS.

The purpose of integrating software like this is to elevate GeoIPS as a package that can
process nearly any type of geospatial data, and output it in a variety of formats. For
each standalone package that we create, we only elevate the capabilities of GeoIPS as a
whole. Eventually, we'd like to see GeoIPS be the only package you need to handle your
geospatial data routines.

Use Cases That We'll Support
----------------------------

If you are a user, developer, or researcher that has software related to geospatial data
processing and are unable to integrate that functionality into GeoIPS, you've come to
the right place. We first request that the data processing you've implemented doesn't
already exist in GeoIPS, or any of its corresponding packages. For a full list of public
repositories that NRLMMD-GEOIPS supports, see
`GeoIPS Repositories <https://github.com/orgs/NRLMMD-GEOIPS/repositories>`_.

If the data routines you've created don't match any of the repositories linked above,
then we've likely found a use case worth creating a separate GeoIPS package for.
Assuming you've found a developer able to help you to get your processing routines
integrated alongside GeoIPS, here's what we'll need from you.

Information Needed for Developers
---------------------------------

In order to create a standalone GeoIPS Package implementing your routines, we'll need
the following information to produce your expected output. This output could take on a
variety of formats, but for this documentation, we'll assume it's some type of imagery,
GeoTIFF, or NetCDF / HDF5 file.

#. ``Data``

   a. We'll take on any and all data that is needed to produce your expected output. The
      more data you provide, the better chance we have at testing and producing accurate
      outputs that match your current routines.

#. ``Code``

   a. The code provided should encapsulate every thing you've indiviually created to get
      your processing routines working. This does not include code from dependent 3rd
      party software packages, but a list of software dependencies would be appreciated
      so we know what to install. Code included could be any of the following bullet
      points.
   b. Algorithms
   c. Colormaps
   d. Readers
   e. Utility Modules
   f. Any other code you wrote that's required to produce the expected output

#. ``List of Input Variables`` needed to produce the desired output

   a. Since the data you're using is geospatial, we'll need some context of what
      variables we'll be dealing with. Please provide us with a list of variables needed
      to produce your expected output. It should look something like what is shown below.
   b. [``cloud_height_acha``, ``relative_humidity``, ``cloud_water_content``, ...]

#. ``Examples of Accurate Outputs`` from your current routines.

   a. Included alongside these outputs, please provide the data used to generate these
      outputs. This way, we have a concrete test example to compare alongside to make
      sure what we've implemented matches what you expect. Could Include:
   b. Imagery
   c. GeoTIFFs
   d. NetCDF / HDF5 Files
   e. Any other output that could assist with testing

#. ``Description of your Geospatial Processing Routines``

   a. In this description, you should include the following information:
   b. What this software achieves
   c. What outputs it creates
   d. Why it's needed

Once we have the aforementioned information, us developers will be able to venture
forward in creating your standalone GeoIPS package based translated from your current
geospatial processing routines. Once this package has been created, you'll be able to
work alongside the GeoIPS environment to produce your personally tailored outputs.
