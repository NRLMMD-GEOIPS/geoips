.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _interpolators_functionality:

***********************
Interpolators in GeoIPS
***********************

An interpolator is a module-based GeoIPS plugin that takes data in its native
resolution and interpolates it to a grid with a different resolution. This
interpolation can be done either before or after running an algorithm, or
independently of running any algorithm.

Interpolators can be executed in two ways:

1. **Inclusion in Product Specifications:** Include the interpolator in a product
or product default specification, which can be executed via the command line or
a test script using a GeoIPS procflow.

For examples of including an interpolator in a product implementation, see the
`product defaults <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/docs/source/userguide/plugin_development/product_default.rst>`_
and
`products <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/docs/source/userguide/plugin_development/product.rst>`_
tutorials.

2. **Direct Invocation:** Interpolators can also be called directly from within a program:

   .. code-block:: python

      from geoips.interfaces import interpolators
      interp_name = "interp_nearest"
      interpolator = interpolators.get_plugin(interp_name)
