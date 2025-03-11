.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _static_sectors_functionality:

************************
Static Sectors in GeoIPS
************************

A static sector is a YAML-based GeoIPS plugin that defines the geographic
region for which data will be plotted. Static sectors provide information to
GeoIPS about how to plot data in a particular geographic area, including the
location, projection, and resolution of the data. Static sectors, unlike
dynamic sectors, do not calculate any location information at runtime.

GeoIPS has many built-in
`static sectors <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/yaml/sectors/static>`_
covering regions across the globe.

See the
:ref:`static sector tutorial <create-a-static_sector>`
for instruction on setting up a new static sector.

Static sectors are defined in a YAML file, as shown in the tutorial above.
They are then included as arguments at the command line. For example:

   .. code-block:: bash

        --sector_list conus

Note that GeoIPS can run the same product for multiple geographic sectors by
passing multiple sectors to the ``sector_list`` argument:

   .. code-block:: bash

        --sector_list conus canada