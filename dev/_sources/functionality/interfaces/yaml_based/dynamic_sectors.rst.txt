.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _dynamic_sectors_functionality:

Dynamic Sectors in GeoIPS
*************************

A dynamic sector is a YAML-based GeoIPS plugin that contains the information
needed to generate a geographic sector for which data will be plotted. Dynamic
sectors include information about the intended size, resolution, and projection
of the resulting geographic sector, but leave the specific location to be
calculated at run time based on the data being used.

Dynamic sectors are most commonly used when plotting tropical cyclone imagery,
as they allow for a sector that can "follow along" with the storm. Note,
however, that they can be used for any type of intermittent environmental or
atmospheric event, such as active volcanoes, atmospheric rivers, or pyrocumulonimbus.

The built-in dynamic sectors in GeoIPS focus on building a sector around a
center coordinate, but this is not intended to limit the variety of dynamic
sectors that can be developed. A dynamic sector could also, for example,
specify resolution or latitude and longitude boundaries rather than the center
coordinate (this may, however, require additional plugin development).

For examples of dynamic sectors and dynamic sector templates, reference any of
the built-in dynamic sector templates
`built-in dynamic sectors <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/yaml/sectors/dynamic>`_.
available within GeoIPS.

Dynamic sectors are defined in a YAML file and are then included as arguments
at the command line. For example, the ``tc_web_ascatuhr_barbs`` sector is
defined in a YAML file within the list of
`dynamic sectors
<https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/yaml/sectors/dynamic/tc_web_ascatuhr_barbs_template.yaml>`_
as follows:

   .. code-block:: yaml

      spec:
      sector_spec_generator:
         name: center_coordinates
         arguments:
            projection: eqc
            pixel_width: 50
            pixel_height: 50
            num_lines: 1400
            num_samples: 1400

This sector can then be used as a command line argument.

   .. code-block:: bash

        --tc_spec_template tc_web_ascatuhr_barbs

See the
`ASCAT UHR
<https://github.com/NRLMMD-GEOIPS/geoips/blob/main/tests/scripts/ascat_uhr.tc.windbarbs.imagery_windbarbs.sh>`_
test script for a more complete picture
