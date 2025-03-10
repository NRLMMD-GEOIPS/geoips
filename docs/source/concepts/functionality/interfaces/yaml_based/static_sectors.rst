:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _static_sectors:

************************
Static Sectors in GeoIPS
************************

A static sector is a yaml-based GeoIPS plugin that defines the geographic
region for which data will be plotted. Static sectors provide information to
GeoIPS about how to plot data in a particular geographic area, including the
location, projection, and resolution of the data. Static sectors, unlike
dynamic sectors, do not calculate any location information at run time.

GeoIPS has many built-in static sectors, which can be accessed
`here <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/yaml/sectors/static>`_.

See the
`static sector tutorial <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/docs/source/tutorials/extending-with-plugins/static_sector/index.rst>`_
for instruction on setting up a new static sector.

Static sectors are defined in a YAML file, as shown in the tutorial above.
They are then included as arguments at the command line. For example:

   .. code-block:: bash

        --sector_list conus

Note that GeoIPS can run the same product for multiple geographic sectors by
passing multiple sectors to the `sector_list` argument:

   .. code-block:: bash

        --sector_list conus canada