.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _sector_spec_generators_functionality:

Sector Spec Generators in GeoIPS
********************************

A sector spec generator is a class-based GeoIPS plugin that turns sector metadata into a
concrete sector specification (an :class:`~pyresample.geometry.AreaDefinition`) — for
example, building an area definition from a center latitude/longitude, resolution, and
size. These are used when generating :ref:`dynamic sectors <create-a-dynamic_sector>`.

For the built-in generators, see the `sector_spec_generators directory
<https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/classes/sector_spec_generators>`_.
