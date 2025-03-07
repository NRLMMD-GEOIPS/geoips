:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _products:

******************
Products in GeoIPS
******************

A product is a yaml-based GeoIPS plugin that defines the information needed to
produce a particular output from a particular data source. This information
includes the source of the data that will be processed, which plugins are
needed to produce the output, what order they go in (via the `family`
attribute), and values to be passed to the arguments for those plugins.

Products are a key plugin for GeoIPS, as they define much of the information
GeoIPS needs to determine how to produce an output.

See the
`products tutorial <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/docs/source/tutorials/extending-with-plugins/product/index.rst>`_
for instruction on setting up a new product.

Products are defined in a YAML file, as shown in the tutorial above. They are
then included as arguments at the command line:

`--product_name My-Cloud-Top-Height`
