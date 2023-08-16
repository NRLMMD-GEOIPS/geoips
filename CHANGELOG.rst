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

Enhancements
============

Replace xRITDecompress with pyPublicDecompWT for seviri_hrit reader
-------------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#264: 2023-08-16, Update seviri reader to use pyPublicDecompWT*

* We had previously been using xRITDecompress which needed to be complied and installed
  separately. This replaces xRITDecompress with pyPublicDecompWT which provides the same
  functionality but can be pip installed.

::

    modified: geoips/plugins/modules/readers/utils/hrit_reader.py

Installation Updates
====================

Add pyPublicDecompWT to dependencies and remove setup_seviri from setup script
------------------------------------------------------------------------------

*From NRLMMD-GEOIPS/geoips#264: 2023-08-16, Update seviri reader to use pyPublicDecompWT*

* Add pypublicdecompwt to install requirements
* Remove setup_seviri from setup.py
* Remove xRITDecompress environment variables from config_geoips

::

    modified: pyproject.toml
    modified: setup_seviri
    modified: config/config_geoips
