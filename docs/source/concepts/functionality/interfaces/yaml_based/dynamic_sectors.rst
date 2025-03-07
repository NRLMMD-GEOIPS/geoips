:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _dynamic_sectors:

*************************
Dynamic Sectors in GeoIPS
*************************

A dynamic sector is a yaml-based GeoIPS plugin that contains the information
needed to generate a geographic sector for which data will be plotted. Dynamic
sectors include information about the intended size, resolution, and projection
of the resulting geographic sector, but leave the specific location to be
calculated at run time based on the data being used.

Dynamic sectors are most commonly used when plotting tropical cyclone imagery,
as they allow for a sector that can "follow along" with the storm.

GeoIPS has a several built-in dynamic sector templates, which can be accessed
`here <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/yaml/sectors/dynamic>`_.

Dynamic sectors are defined in a YAML file, and are then included as arguments
at the command line. For example:

`--tc_spec_template tc_web_ascatuhr_barbs`
