:orphan:

2023 Tutorial
=============

Assigned to: Kumar
Due for review: June 3rd

Done looks like:
 - Work done on a feature branch, eg. documentation-2023-tutorial
 - Readable and followable, please use a grammar checker + spell checker
 - Passes doc8 checks, see the `sphinx RST Primer
   <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#restructuredtext-primer>`_`
   and checkout this tool I wrote for auto-formatting RST files:
   `pink <https://github.com/biosafetylvl5/pinkrst/tree/main>`_

   - Does NOT include

     - New tutorial components
     - Information on how GeoIPS works, this is "how to bake a pie", not "what is a pie".
       For more information, please
       read `this primer on tutorials <https://docs.divio.com/documentation-system/tutorials/>`

   - Does include

     - All of the information from the 2023 tutorial
     - Edits where nessesary if GeoIPS functionality has changed since 2023

 - A PR from your feature branch to ``main`` 😊

.. _create-a-product:

**********************************
Extend GeoIPS with new Products
**********************************

This section discusses how to create multiple products for CLAVR-x data, specifically
Cloud-Top-Height, Cloud-Base-Height, and Cloud-Depth. Products are the cornerstone
plugin for GeoIPS, as they define how to produce a specific product as a combination of
other plugins. Products use other plugins, such as an algorithm, colormapper,
interpolater, etc. to generate the correct result.

We will now go hands on in creating a product for CLAVR-x Cloud-Top-Height.

#. First off, change directories to your product plugins directory.
   ::

        cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products

#. Now, create a file called ``my_clavrx_products.yaml``, which we'll fill in soon.
   Before we add any code let's discuss some of the top level attributes that are
   required in any GeoIPS plugin:
   ``interface``, ``family``, and ``docstring``.

Please see documentation for
:ref:`additional info on these GeoIPS required attributes<required-attributes>`

Creating a GeoIPS Product Plugin
--------------------------------

The code snippet shown below shows properties required in every GeoIPS plugin, YAML or
Module-based. These properties help GeoIPS define what type of plugin you are developing
and also defines what schema your plugin will be validated against.

Copy and paste the code shown below into my_clavrx_products.yaml.

.. code-block:: yaml

    interface: products
    family: list
    name: my_clavrx_products
    docstring: |
      CLAVR-x imagery products
