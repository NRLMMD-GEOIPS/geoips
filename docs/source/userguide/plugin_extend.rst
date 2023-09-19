 | # # # Distribution Statement A. Approved for public release. Distribution unlimited.
 | # # #
 | # # # Author:
 | # # # Naval Research Laboratory, Marine Meteorology Division
 | # # #
 | # # # This program is free software: you can redistribute it and/or modify it under
 | # # # the terms of the NRLMMD License included with this program. This program is
 | # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 | # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
 | # # # for more details. If you did not receive the license, for more information see:
 | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

.. _plugin-extend:

**************************
Extend GeoIPS with Plugins
**************************

GeoIPS is almost entirely composed of plugins and can be extended by developing
new plugins in external python packages. The ability to extend GeoIPS using
plugins means that there is no need to edit the main GeoIPS code to add new
functionality.  Most types of functionality in GeoIPS can be extended. If you
encounter something that you would like to be able to extend but are unable to,
please contact the GeoIPS team or create an issue on GitHub.

Developing a new plugin for GeoIPS requires developing a new Python package that GeoIPS
terms a "plugin package". The plugin package can contain one or more plugins. It is
configured in a special way such that, when it is installed,
it registers itself and its plugins with GeoIPS.

An example repository `Template Basic Plugin <https://github.com/NRLMMD-GEOIPS/template_basic_plugin/tree/main>`_
is provided that can guide you through the process of creating a new plugin package
containing one or more custom plugins.

GeoIPS Plugin Vocabulary
========================

Plugin
------
A GeoIPS plugin may be either a Python module or a YAML file that extends GeoIPS with
new functionality. Whether a plugin is a Python module or a YAML file is determined by
its interface.

Plugins are stored in installable Python packages that register their payload with
GeoIPS through the use of `entrypoints<entry-points>`.

Module-based Plugin
-------------------
A module-based plugin is a plugin that extends GeoIPS by adding new
functionality that is capable of performing an action (e.g. apply an algorithm,
read data, apply formatting, etc.).  Module-based plugins are defined as a
single python module that contains a handful of required top-level variables and
a single function that performs the action of the plugin. Examples of
module-based plugins include ``algorithms``, ``readers``, and various types of
formatters.

YAML-based Plugin
-----------------
A YAML-based plugin is a plugin that extends GeoIPS by adding a new set of
static configuration options for GeoIPS.  Examples of YAML-based plugins include
``sectors``, ``products``, and ``feature-annotators``.

Interface
---------
An ``interface`` defines a class of GeoIPS plugins that extend the same type of
functionality within GeoIPS. For example, some commonly used interfaces include the
``algorithms``, ``colormappers``, and ``sectors`` interfaces.

Family
------
A ``family`` is a subset of an interface's plugins which accept specific sets of
arguments/properties. Module-based plugins of the same ``family`` have similar call
signatures. YAML-based plugins of the same ``family`` are validated against the same
schema (i.e. they contain the same properties).

.. _plugin-development-setup:

Setting up for Plugin Development
=================================

1. To develop a new GeoIPS plugin, first :ref:`install GeoIPS<complete_install>` and ensure
   that you have your environment enabled and all environment variables set as described in
   the installation instructions.

2. Then, choose a name for your package. By contention the package name should:

   * be all lower case
   * start with a letter
   * contain only letters, numbers, and underscores

   From here on, anywhere ``@package@`` is used should be replaced with your chosen package
   name.

3. Clone the ``template_basic_plugin`` repository, rename it, and remove the link to github.
   ::

       cd $GEOIPS_PACKAGES_DIR
       git clone --no-tags --single-branch https://github.com/NRLMMD-GEOIPS/template_basic_plugin.git

       # Replace @package@ with your package name, removing the @s
       mv template_basic_plugin @package@
       cd $MY_PKG_NAME
       git remote remove origin template_basic_plugin.git

4. Update readme.md

   The ``readme.md`` file describes your plugin package and should be updated to match your
   package. To do this, edit ``README.md`` to:

   * Replace all instances of ``@package@`` with your package name.
   * Search for all remaining ``@`` within the file and follow the included instructions to
     update the readme appropriately.
   * Remove all lines containing ``@``.

5. Update pyproject.toml

   Installing a Python package requires metadata that describes the package and how to
   install it. GeoIPS uses ``pyproject.toml`` to define this information. We, additionally,
   make GeoIPS aware of plugin packages using ``entry-points``.

   To update ``pyproject.toml`` for your package, edit the file to:

   * Update ``@package@`` to your package name.
   * Update ``my_package`` to your package name.
   * Add any python package depenencies to the ``install_requires`` section.

6. Add and commit your changes.
   ::

      git add README.md pyproject.toml
      git commit -m "Updated name of template plugin package to mine"

7. Install your package using the changes you just made.

   Note: Any time you edit ``pyproject.toml``, you must reinstall your package. Without
   doing this, GeoIPS will not be aware of your new changes, since it will be in the
   previous install state, which doesn't include any new updates to this file.

   ::

      pip install -e $MY_PKG_DIR

   The ``-e`` portion of the command above means 'editable', so we can edit the package
   after it is installed and changes will be reflected in the installed package. Again,
   the only time you must reinstall is when you edit ``pyproject.toml``, which
   generally only occurs when you create new module based plugins, and must add them as
   entry-points to ``pyproject.toml``. This is further discussed in the
   :ref:`Algorithms Section<add-an-algorithm>`.

Defining pyproject.toml
-----------------------

Installing Python packages requires metadata that describes the package and how to
install it.

pyproject.toml defines this information for pip, including:
    * Package name, version, description, license, etc.
    * Which files should be contained in the package when installed
    * How to build the package

We make GeoIPS aware of our package using the “geoips.plugin_packages” namespace
(allows GeoIPS to find YAML-based plugins)

And makes it aware of our module-based plugins using one namespace per interface
(e.g. “geoips.algorithms”).

Building a Custom GeoIPS Package
--------------------------------

Note, this any section below assumes you have completed either the :ref:`complete_install`,
the :ref:`mac_install`, or the :ref:`expert_install`. If you havent, please complete
those steps before moving forward.

We will now go hands on in creating a :ref:`Product<create-a-product>` for your custom
GeoIPS Package.

Developing Module-based plugin
==============================

Developing YAML-based plugin
============================

Example Module-based Plugins
============================


Algorithms
-----------

:ref:`Create an Algorithm<add-an-algorithm>`

Colormaps
---------

Filename formatters
-------------------

Interpolators
-------------

Output Formatters
-----------------

ProcFlows
---------

Readers
-------

Title Formatters
----------------

Example YAML-based Plugins
==========================

Boundary Annotators
-------------------

Gridline Annotators
-------------------

Product Defaults
----------------

* A word about product defaults
* GeoIPS has a number of product_defaults plugins defined to help you not reinvent the wheel, but:
    * You can override any of the product defaults within your product definition
    * You can absolutely define all of the available options within your product plugin
* `Pre-defined CLAVR-x product defaults <https://github.com/NRLMMD-GEOIPS/geoips_clavrx/tree/main/geoips_clavrx/plugins/yaml/product_defaults>`_
  (part of the CLAVR-x plugin)
* `Pre-defined GeoIPS product defaults <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/yaml/product_defaults>`_
* If you have product definition parameters that you want to reuse (i.e. if you're copy/pasting product definition parameters!),
  consider creating a product default for your plugin

* Shown below is the geoips_clavrx Cloud-Height product defaults yaml file.

.. code-block:: yaml

    interface: product_defaults
    family: interpolator_algorithm_colormapper
    name: Cloud-Height
    docstring: |
      The Cloud-Height product_defaults geoips_clavrx configuration.
    spec:
      interpolator:
        plugin:
          name: interp_nearest
          arguments: {}
          algorithm:
            plugin:
              name: single_channel
              arguments:
                output_data_range: [0, 20]
                scale_factor: 0.001
                min_outbounds: "crop"
                max_outbounds: "crop"
                norm: False
                inverse: False
          colormapper:
            plugin:
              name: cmap_cldHeight
              arguments:
                data_range: [0, 20]

* In your product you can use the product_defaults verbatim.

.. code-block:: yaml

    spec:
      products:
        - name: My-Cloud-Top-Height
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Top Height
          product_defaults: Cloud-Height
          spec:
            variables: ["cld_height_acha", "latitude", "longitude"]

* You can also override just some parts of the product_defaults.
* In this example, we override the algorithm plugin contained in the Cloud-Height
  product_defaults, with our own specification.

.. code-block:: yaml

    interface: products
    family: list
    name: clavrx
    docstring: |
      The Products geoips_clavrx default configuration
    spec:
      products:
        - name: Cloud-Top-Height
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Top Height
          product_defaults: Cloud-Height
          spec:
            variables: ["cld_height_acha", "latitude", "longitude"]
            algorithm:
              plugin:
                name: single_channel
                arguments:
                  output_data_range: [0, 20]
                  scale_factor: 0.001
                  min_outbounds: "mask"
                  max_outbounds: "mask"
                  norm: True
                  inverse: False

* We also have the option to define a product without using product_defaults.
* To do this:
    * Remove the ‘product_defaults’ property
    * Add the ‘family’ property
    * This is shown in the code block below.

.. code-block:: yaml

    interface: products
    family: list
    name: clavrx
    docstring: |
      The Products geoips_clavrx default configuration
    spec:
      products:
        - name: Cloud-Top-Height
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Top Height
          family: interpolator_algorithm_colormapper
          spec:
            variables: ["cld_height_acha", "latitude", "longitude"]
            interpolator:
              plugin:
                name: interp_nearest
                arguments: {}
            algorithm:
              plugin:
                name: single_channel
                arguments:
                  output_data_range: [0, 20]
                  scale_factor: 0.001
                  min_outbounds: "mask"
                  max_outbounds: "mask"
                  norm: True
                  inverse: False
            colormapper:
              plugin:
                name: cmap_cldHeight
                arguments:
                  data_range: [0, 20]

Products
--------

:ref:`Create New Products<create-a-product>`

Dynamic Sectors
---------------

Static Sectors
--------------

:ref:`Create a Static Sector<create-a-static_sector>`

ProcFlow Configurations
-----------------------

.. _entry-points: https://packaging.python.org/en/latest/specifications/entry-points/
