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

Bug Fixes
=========

Update error messages in "bad" product_defaults tests
-----------------------------------------------------

*From NRLMMD-GEOIPS/geoips#255: 2023-08-09, Fix error matching regex*

* jsonschema changed their error messages to add additional quotes. This just modifies
  our test regex to ignore more of the error.

::

    modified: tests/test_plugin_schema/bad/product_defaults/algorithm_colormapper.yaml
    modified: tests/test_plugin_schema/bad/product_defaults/algorithm_interpolator_colormapper.yaml

