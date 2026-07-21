.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _sector_metadata_generators_functionality:

Sector Metadata Generators in GeoIPS
************************************

A sector metadata generator is a class-based GeoIPS plugin that parses an external source —
such as a tropical-cyclone b-deck/f-deck file or a volcano track file — into the metadata
GeoIPS uses to build :ref:`dynamic sectors <create-a-dynamic_sector>`. Examples include the
``bdeck_parser``, ``fdeck_parser``, and ``volc_parser`` plugins.

For the built-in generators, see the `sector_metadata_generators directory
<https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/classes/sector_metadata_generators>`_.
