.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _class-based-plugins:

Class-Based Plugins in GeoIPS
=============================

In order to better support the :ref:`Order-Based Procflow (OBP) <order-based-procflow>`
currently in development, we are reshaping the way ``module-based plugins`` will work.

Instead of generating a plugin object via a class factory from a given module, we will
transform all module-based plugins to be true python classes. This accomplishes a few
things.

1. Transparency to the user/developer
2. Removes any 'black magic' related to how module-based plugins are transformed into an
   object
3.