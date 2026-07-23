.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _sector_adjusters_functionality:

Sector Adjusters in GeoIPS
**************************

A sector adjuster is a class-based GeoIPS plugin that modifies a sector's
:class:`~pyresample.geometry.AreaDefinition` at runtime based on the data being processed.
The most common use is recentering a tropical cyclone sector on the storm's actual center
(for example, from an archer or best-track fix) before the data is registered to it.

For the built-in sector adjusters, see the `sector_adjusters directory
<https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/classes/sector_adjusters>`_.
