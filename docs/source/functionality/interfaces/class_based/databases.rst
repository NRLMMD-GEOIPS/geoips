.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _databases_functionality:

Databases in GeoIPS
*******************

A database is a class-based GeoIPS plugin that reads from or writes to a product database —
for example, recording the outputs a processing run produced, or querying previously
generated products (such as when compositing). Database plugins let GeoIPS integrate with
external product-tracking systems without hard-coding a particular backend.

For the built-in database plugins, see the `databases directory
<https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/classes/databases>`_.
