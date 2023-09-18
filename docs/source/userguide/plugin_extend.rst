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

An example repository **add a link here** is provided that can guide you through
the process of creating a new plugin package containing one or more custom
plugins.

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

3. Clone the ``template_basic_plugin`` repository and rename it:
   ::

       cd $GEOIPS_PACKAGES_DIR
       git clone --no-tags --single-branch https://github.com/NRLMMD-GEOIPS/template_basic_plugin.git

       # Replace @package@ with your package name, removing the @s
       mv template_basic_plugin @package@

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
   * Add any python package depenencies to the ``install_requires`` section.

6. Add more subsections

   Add more subsections to complete the setup

Defining pyproject.toml
-----------------------

* Installing Python packages requires metadata that describes the package and how to
  install it.

* pyproject.toml defines this information for pip, including:
    * Package name, version, description, license, etc.
    * Which files should be contained in the package when installed
    * How to build the package

* We make GeoIPS aware of our package using the “geoips.plugin_packages” namespace
  (allows GeoIPS to find YAML-based plugins)

* And makes it aware of our module-based plugins using one namespace per interface
  (e.g. “geoips.algorithms”).

Building a Custom GeoIPS Package
------------------------------------------------

* Note, this section assumes you have completed either the :ref:`complete_install`,
  the :ref:`mac_install`, or the :ref:`expert_install`. If you havent, please complete
  those steps before moving forward.

* Setup
    * Activate your GeoIPS conda environment (You'll know if it's active if (geoips) shows up ahead of your command prompt)
        * conda activate geoips
    * For convenience, let's set a couple of environmental variables in your terminal session up front.
        * # Choose a name for your package (cool_plugins is recommended for
          this tutorial)
        * # Your package name can be anything so long as it doesn’t have dashes
            * export MY_PKG_NAME=cool_plugins
            * export MY_PKG_DIR=$GEOIPS_PACKAGES_DIR/$MY_PKG_NAME
    * Back in your terminal window, run the series of following commands:
        * # Clone the template repository from GitHub
            * cd $GEOIPS_PACKAGES_DIR
            * git clone --no-tags --single-branch $GEOIPS_REPO_URL/template_basic_plugin.git
        * # Rename your package
            * mv template_basic_plugin/ $MY_PKG_NAME
            * cd $MY_PKG_NAME
            * git remote remove origin  # No longer point to github.com template_basic_plugin.git
        * # Update Package name
            * cd $MY_PKG_DIR
            * git mv my_package $MY_PKG_NAME
        * # Update Pertinent files
            #. Update README.md (vim README.md)
                * Find/replace all occurrences of @package@ with your package name
                * Note: The @ symbols are for ease of searching, take them out when you
                  put your package name in!
            #. Update pyproject.toml (vim pyproject.toml, more on this in the next slide)
                * Find/replace all occurrences of my_package with your package name
            #. Add and commit your changes
                * git add README.md pyproject.toml
                * git commit -m "Updated name of template plugin package to mine"
            #. Install your package (-e means “editable” so we can edit the package after it is installed and changes will be reflected in the installed package)
	            * pip install -e $MY_PKG_DIR
* We will now go hands on in creating a Product for your custom GeoIPS Package.

Developing Module-based plugin
==============================

Developing YAML-based plugin
============================

Example Module-based Plugins
============================


Algorithnms
-----------
:ref:`algorithms<add-an-algorithm>`

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

Products
--------

Dynamic Sectors
---------------

Static Sectors
--------------

* First off, copy this GeoIPS Static Sector YAML File to edit.
    * mkdir -pv $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/sectors/static
    * cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/sectors/static
    * cp $GEOIPS_PACKAGES_DIR/geoips/geoips/plugins/yaml/sectors/static/australia.yaml
      my_conus_sector.yaml
    * vim my_conus_sector.yaml

.. code-block:: yaml

    interface: sectors
    family: area_definition_static
    name: australia
    docstring: "Australian Continent"
    metadata:
    region:
        continent: Australia
        country: x
        area: Continental
        subarea: x
        state: x
        city: x
    spec:
        area_id: australia
        description: Australian Continent
        projection:
            a: 6371228.0
            lat_0: -26.5
            lon_0: 134.0
            proj: stere
            units: m
        resolution:
            - 2000
            - 2000
        shape:
            height: 2100
            width: 2400
        center: [0, 0]

.. code-block:: yaml

    interface: sectors
    family: area_definition_static
    name: my_conus_sector
    docstring: "My CONUS Sector"
    metadata:
    region:
        continent: NorthAmerica
        country: UnitedStates
        area: x
        subarea: x
        state: x
        city: x
    spec:
        area_id: my_conus_sector
        description: CONUS
        projection:
            a: 6371228.0
            lat_0: 37.0
            lon_0: -96.0
            proj: eqc # Describes the Projection Type (from PROJ Projections)
            units: m
        resolution:
            - 3000 # The resolution of each pixel in meters (x, y)
            - 3000
        shape:
            height: 1000
            width: 2200
        center: [0, 0]

* The code blocks above depict the changes you will need to make to create a custom
  conus sector plugin. While you can leave the metadata untouched, it is very helpful to
  have additional information about the sector being displayed, not only for the backend
  of GeoIPS, but also for people using this sector plugin.

* Once you’ve made the appropriate changes, you will be ready to use your custom sector
  plugin with CLAVR-x data.

* The commands you ran in the previous slide create a custom conus sector.
  my_conus_sector.yaml will be an example plugin, showing you that you can create
  sectors just like conus.yaml, to your own specifications.

* To quickly check whether or not you like the shape and resolution of your custom sector, you can use the command line function create_sector_image.
* This will plot and save images containing the borders and coastlines of the inputted sectors. For example, to test your custom sector, run the following:
    * cd $MY_PKG_DIR/$MY_PKG_NAME/
    * create_sector_image my_conus_sector

* Once completed, open the my_conus_sector.png image to see what your sector will look
  like.

.. image:: ../images/command_line_examples/my_conus_sector.png
   :width: 800

* Using Your Custom Static Sector
    * To use my_conus_sector.yaml in your test script, simply replace *‘--sector_list
      conus’* with *‘--sector_list my_conus_sector’*. This change means that
      clavrx.conus_annotated.my-cloud-top-height.sh will use the sector you just
      created, rather than the GeoIPS conus sector we’ve been using previously.
    * cd $MY_PKG_DIR/tests/scripts
    * cp clavrx.conus_annotated.my-cloud-top-height.sh clavrx.my_conus_sector.my-cloud-top-height.sh
    * vim clavrx.my_conus_sector.my-cloud-top-height.sh
    * $MY_PKG_DIR/tests/scripts/clavrx.my_conus_sector.my-cloud-top-height.sh

* Output

.. image:: ../images/command_line_examples/my_conus_sector_cth.png
   :width: 800


ProcFlow Configurations
-----------------------

.. _entry-points: https://packaging.python.org/en/latest/specifications/entry-points/
