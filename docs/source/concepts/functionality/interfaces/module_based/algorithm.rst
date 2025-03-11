.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _algorithm_functionality:

********************
Algorithms in GeoIPS
********************

An algorithm is a GeoIPS plugin designed to manipulate and convert datasets. Algorithms
cannot operate independently; they take raw meteorological data and transform them.
These manipulations may include quality control, time and location filtering, and
derived variable calculations.

For example, an algorithm could scale data to a specific range useful for plotting.

Algorithms vary in complexity based on requirements.

A simple example is the
`wind barb algorithm <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/modules/algorithms/sfc_winds/windbarbs.py>`_,
which primarily converts wind speed units and optionally applies data bounds.

More complex algorithms include the
`single channel algorithm <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/modules/algorithms/single_channel.py>`_,
which involves masking, solar zenith corrections, scaling, normalization, and unit conversion.
The `stitched data fusion algorithm <https://github.com/NRLMMD-GEOIPS/data_fusion/blob/main/data_fusion/plugins/modules/algorithms/stitched.py>`_
is another complex algorithm. It combines overlapping satellite data, adjusting for
satellite zenith angle and parallax correction in the overlap zones.

Algorithms can be executed in two ways:

1. **Direct Invocation:** Call the algorithm from within a program:

   .. code-block:: python

      from geoips.interfaces import algorithms
      algorithm_name = "single_source"
      algorithms.get_plugin(algorithm_name)

2. **Inclusion in Product Specifications:** Include the algorithm in a product or
product default specification, which can be executed via the command line or a test
script using a GeoIPS procflow.

For examples of including an algorithm in a product implementation, see the
:ref:`product defaults <create-product-defaults>`
and
:ref:`products <create-a-product>`
tutorials.
