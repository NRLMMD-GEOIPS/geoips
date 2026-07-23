.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _product_defaults_functionality:

Product Templates (Defaults) in GeoIPS
**************************************

A product template (also referred to as a product default) is a YAML-based
GeoIPS plugin that defines the default setup, or template, for a group of
related GeoIPS products.

Product default plugins are not strictly necessary to produce a GeoIPS product,
but they are useful for reducing duplication when creating multiple products
with similar processing steps (e.g. multiple plugins with the same interpolator
and algorithm).

For example, suppose that you have multiple products that consist of a difference
between two channels. These products may all use the same interpolator and
algorithm, but you may wish to use different colormappers with them. The
product_default would contain the interpolator and algorithm, and then could
be referenced in the product definition. Each product definition would use
this product_default, but would specify a different colormapper.

See the
:ref:`product defaults tutorial <create-product-defaults>`
for instruction on setting up a new product template (and its related product).

Product defaults are defined in a YAML file, as shown in the tutorial above.
They can then be reused in a product specification, such as in the below
example, which uses a product default called "Cloud-Height".

   .. code-block:: yaml

      spec:
        products:
          - name: My-Cloud-Top-Height
            source_names: [clavrx]
            docstring: |
              CLAVR-x Cloud Top Height
            product_defaults: Cloud-Height  # Use the Cloud-Height product template
            spec:
              variables: ["cld_height_acha", "latitude", "longitude"]
