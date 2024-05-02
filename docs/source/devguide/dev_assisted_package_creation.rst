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

If you are a user, developer, or researcher that has software related to geospatial data
processing and are unable to integrate that functionality into GeoIPS, you've come to
the right place. Some of our developers for GeoIPS (specifically CIRA-based), might be
able to help you integrate your functionality into GeoIPS. Please continue reading if
you think this may be of use!

Why We Assist With Package Creation
-----------------------------------

The GeoIPS Development team is committed to integrating a variety of geospatial
processing routines into GeoIPS, or as standalone packages that can interact with
GeoIPS. This can be as simple as adding your algorithm or reader to the main GeoIPS
code, or it can be more complex in creating a completely separate GeoIPS plugin-package
specific for your use case. If you have access, see the
`GeoIPS GLM Package <https://bear.cira.colostate.edu/overcast/geoips_glm>`_ for an
example of a standalone package that implements GREMLIN and GLM
(Global Lightning Mapper) routines working alongside GeoIPS.

If you don't have access to that, please feel free to view any of our
`public repositories <https://github.com/orgs/NRLMMD-GEOIPS/repositories>`_ for a
general idea of what we can help you with.

The purpose of integrating software like this is to elevate GeoIPS as a package that can
process nearly any type of satellite, in-situ, geo-located -derived data, and output it
in a variety of formats. For each standalone package that we create, we only elevate the
capabilities of GeoIPS as a whole. Eventually, we'd like to see GeoIPS be one, if not
the package you need to handle your geospatial processing routines.

Use Cases That We'll Support
----------------------------

We first request that the data processing you've implemented doesn't already exist in
GeoIPS, or any of its corresponding packages. If you have processing routines that are
similar, it is likely you'll just have to reformat your inputs to integrate correctly
with the GeoIPS system. We are happy to help with that if needed. For a full list of
public repositories that NRLMMD-GEOIPS supports, see
`GeoIPS Repositories <https://github.com/orgs/NRLMMD-GEOIPS/repositories>`_.

If the data routines you've created don't match any of the repositories linked above,
then we've likely found a use case worth creating a separate GeoIPS package for.

Please either submit an issue `here <https://github.com/NRLMMD-GEOIPS/geoips/issues/new/choose>`_,
or contact us at ``geoips@nrlmry.navy.mil`` specifying your use case and the assistance
needed. Here's what we'll need from you for either method.

Information Needed for Developers
---------------------------------

In order to create a standalone GeoIPS Package implementing your routines, we'll need
the following information to produce your expected output. This output could take on a
variety of formats, but for this documentation, we'll assume it's some type of imagery,
GeoTIFF, or NetCDF / HDF5 file.

#. ``Data``

   a. We'll take on most datasets that iares needed to produce your expected output. The
      more data and types of data which you provide, the better chance we have at
      testing and producing accurate outputs that match your current routines. Please
      don't provide us with Terabytes of data, only that which is necessary to produce
      your product in its entirety.

#. ``Code``

   a. The code provided should encapsulate everything you or your group created to get
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

Once we have the aforementioned information, we'll be able to move foward in creating
your standalone GeoIPS package, translated from your current geospatial processing
routines. Once this package has been created, you'll be able to work alongside the
GeoIPS environment to produce your personally tailored outputs.
