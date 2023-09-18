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
            * # Note, you can also add these to your .bashrc if you plan on using these references often.
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
            #. Update pyproject.toml (vim pyproject.toml)
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

* The following steps will teach you how to create a custom algorithm plugin.
* Copy the existing algorithm plugin to a new file to modify
    * cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/modules/algorithms
    * cp pmw_89test.py my_cloud_depth.py
* Edit my_cloud_depth.py (see below)

* Module plugins are required to have several top-level variables:
    * name
    * interface
    * family
* It is additionally required to have a docstring.
* To convert this algorithm to “my_cloud_depth”:
    * Update the docstring.
    * Update “name” to “my_cloud_depth”.

.. code-block:: python

    """Sample algorithm plugin, duplicate of "89pct".

    Duplicate of Passive Microwave 89 GHz Polarization Corrected Temperature.
    Data manipulation steps for the "89test" product, duplicate of "89pct".
    This algorithm expects Brightness Temperatures in units of degrees Kelvin
    """
    import logging
    from xarray import DataArray

    LOG = logging.getLogger(__name__)

    interface = "algorithms"  # The same for all algorithm plugins
    family = "xarray_to_xarray"  # In English: this plugin takes an Xarray dataset containing all required variables, and returns an Xarray dataset with a new variable holding the output from the algorithm
    name = "pmw_89test"

* Update the code block above with the changes shown below.

.. code-block:: python

    """Cloud depth product.

    Difference of cloud top height and cloud base height.
    """
    import logging
    from xarray import DataArray

    LOG = logging.getLogger(__name__)

    interface = "algorithms"
    family = "xarray_to_xarray"
    name = "my_cloud_depth"  # Conventionally matches the name of the plugin definition file, but can be anything that does not contain hyphens.

* Each module-based plugin is required to have a 'call' function. This is how geoips
  will interact with the module-based plugins. See below for the call signature of the
  pmw_89test.py plugin.

.. code-block:: python

    def call(
        xobj,  # Xarray dataset holding xarrays
        variables,  # list of required input variables for algorithm. Note: Python lists are ordered, so you can count on your list of variables being in the order in which you define them in your product plugin variables
        product_name,
        output_data_range,
        min_outbounds="crop",
        max_outbounds="mask",
        norm=False,
        inverse=False,
    ):
        """89pct product algorithm data manipulation steps."""

* Update the code block above to the code block below. These changes will help us create
  a cloud-depth algorithm.

.. code-block:: python

    def call(
        xobj,
        variables,
        product_name,
        output_data_range,
        scale_factor,  # Adding a scale factor here for use in converting input meters to output kilometers
        min_outbounds="crop",
        max_outbounds="crop",
        norm=False,
        inverse=False,
    ):
        """My cloud depth product algorithm manipulation steps."""

* This is where the actual data manipulation occurs. Make sure to index the variable
  list to the order of the variables you defined in your product, then make the
  following changes.

.. code-block:: python

    h89 = xobj[variables[0]]
    v89 = xobj[variables[1]]

    out = (1.7 * v89) - (0.7 * h89)

    from geoips.data_manipulations.corrections import apply_data_range

    data = apply_data_range(
        out,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )
    xobj[product_name] = DataArray(data)

    return xobj

* Update the code above to the code below. This is how cloud-depth will be calculated.

.. code-block:: python

    cth = xobj[variables[0]]
    cbh = xobj[variables[1]]

    out = (cth - cbh) * scale_factor

    from geoips.data_manipulations.corrections import apply_data_range

    data = apply_data_range(
        out,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )
    xobj[product_name] = DataArray(data)

    return xobj

* Now that we've created our custom algorithm, we need to add an entry point for it in
  pyproject.toml so that GeoIPS can locate it during runtime. This must be done anytime
  a new module-based plugin is created.
* Module-based plugins must be registered to an entry-point namespace. This allows
  GeoIPS to find your plugin, even though it is in a different package!
* The namespaces are named for their interface (e.g. “geoips.algorithms”, “geoips.interpolators”, etc.).
* Add your entrypoint:
    * cd $MY_PKG_DIR
	* Edit pyproject.toml

.. code-block:: toml

    [project.entry-points."geoips.algorithms"]
    pmw_89test = "cool_plugins.plugins.modules.algorithms.pmw_89test"
    my_cloud_depth = "cool_plugins.plugins.modules.algorithms.my_cloud_depth"

* Reinstall your package
    * pip install -e $MY_PKG_DIR
    * # This is required anytime pyproject.toml is edited!

* Let's revisit our My-Cloud-Depth product definition to use the algorithm we just created
    * Note: If you haven't yet created this product, see the *Products* section.
    * cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products

Edit my_clavrx_products.yaml (see below)

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

* Creating a Product for CLAVR-x Cloud Top Height

#. Copy the existing product plugin to a new file to modify
    * cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products
    * cp amsr2_using_product_defaults.yaml my_clavrx_products.yaml
#. Edit my_clavrx_products.yaml properties (vim my_clavrx_products.yaml)
    * # (Feel free to remove all lines preceded by “# @”)

.. code-block:: yaml

    interface: products
    family: list
    name: amsr2_using_product_defaults
    docstring: |
      AMSR-2 products using product_defaults

* Change the above code block to the code listed below

.. code-block:: yaml

    interface: products
    family: list
    name: my_clavrx_products
    docstring: |
      CLAVR-x imagery products

* Now we'll update the 'spec' portion of the yaml file to support our new product plugin

.. code-block:: yaml

    spec:
      products:
        - name: 89-PCT-Using-Product-Defaults
          source_names: [amsr2]
          docstring: |
            89 MHz Polarization Corrected Brighness Temperature Implementation
            using the 89-PCT-Test product defaults in the product definition.
          product_defaults: 89-PCT-Test
          spec:
            variables: ["tb89hA", "tb89vA"]

* Update the code block above to what is stored in the code block below. You don't need the comments included.

.. code-block:: yaml

    spec:
      products:
        - name: My-Cloud-Top-Height # The name of the product you're defining (can be anything)
          source_names: [clavrx] # Defined as metadata in the corresponding reader
          docstring: | # Pipe says to YAML this will be a multiline comment, can be anything
            CLAVR-x Cloud Top Height
          product_defaults: Cloud-Height # See the Product Defaults section for more info
          spec: # Variables are the neccessary variables which are needed to produce your product
            variables: ["cld_height_acha", "latitude", "longitude"]

* To use your product that you just created, you'll need to create a bash script that
  implements 'run_procflow'.
* GeoIPS is called via a command line interface
* The main command that you will use is run_procflow which will run your data through the
  specified procflow using the specified plugins
* It's easiest to do this via a script, and scripts are stored in your plugin package's
  tests/ directory because they can be used later to regression test your package
* Copy the existing test script into a new file to modify
    * cd $MY_PKG_DIR/tests/scripts
    * cp amsr2.global_clean.89-PCT-Using-Product-Defaults.sh clavrx.conus_annotated.my-cloud-top-height.sh
* Edit clavrx.conus_annotated.my-cloud-top-height.sh (see code blocks below)
    * vim clavrx.conus_annotated.my-cloud-top-height.sh

.. code-block:: bash

    run_procflow \
    $GEOIPS_TESTDATA_DIR/test_data_amsr2/data/AMSR2-MBT_v2r2_GW1_s202005180620480_e202005180759470_c202005180937100.nc \
        --procflow single_source \
        --reader_name amsr2_netcdf \
        --product_name 89-PCT-Using-Product-Defaults \
        --compare_path $GEOIPS_PACKAGES_DIR/template_basic_plugin/tests/outputs/amsr2.global_clean.89-PCT-Product-Defaults \
        --output_formatter imagery_clean \
        --filename_formatter geoips_fname \
        --minimum_coverage 0 \
        --sector_list global

* Change the code above to the code listed below. Note that the '--compare_path' line
  has been removed

.. code-block:: bash

    run_procflow \
    $GEOIPS_TESTDATA_DIR/test_data_clavrx/data/goes16_2023101_1600/clavrx_OR_ABI-L1b-RadF-M6C01_G16_s20231011600207.level2.hdf \
        --procflow single_source \
        --reader_name clavrx_hdf4 \
        --product_name My-Cloud-Top-Height \
        --output_formatter imagery_annotated \
        --filename_formatter geoips_fname \
        --minimum_coverage 0 \
        --sector_list conus

* Once these changes have been created, we can run our test script to produce Cloud Top
  Height Imagery.
* Run your script
    * $MY_PKG_DIR/tests/scripts/clavrx.conus_annotated.my-cloud-top-height.sh
* This will write some log output.
* If your script succeeded it will end with INTERACTIVE: Return Value 0
* To view your output, look for a line that says SINGLESOURCESUCCESS
* Open the PNG file, it should look like the image below.

.. image:: ../images/command_line_examples/my_cloud_top_height.png
   :width: 800

* Using your definition of My-Cloud-Top-Height as an example, create a product definition for My-Cloud-Base-Height
    * cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products
    * Edit my_clavrx_products.yaml
* Helpful Hints:
    * The relevant variable in the CLAVR-x output file (and the equivalent GeoIPS reader) is called "cld_height_base"
    * The Cloud-Height product_default can be used to simplify this product definition (or you can DIY or override if you'd like!)
* The correct products implementation for 'my_clavrx_products.yaml' is shown below.

.. code-block:: yaml

    interface: products
    family: list
    name: my_clavrx_products
    docstring: |
      CLAVR-x imagery products
    spec:
      products:
        - name: My-Cloud-Top-Height
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Top Height
          product_defaults: Cloud-Height
          spec:
            variables: ["cld_height_acha", "latitude", "longitude"]
        - name: My-Cloud-Base-Height
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Base Height
          product_defaults: Cloud-Height
          spec:
            variables: ["cld_height_base", "latitude", "longitude"]

* Using your definitions of My-Cloud-Top-Height and My-Cloud-Base-Height as examples, create a product definition for My-Cloud-Depth
    * cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products
    * Edit my_clavrx_products.yaml
* Helpful Hints:
    * We will define Cloud Depth for this tutorial as the difference between CTH and CBH

.. code-block:: yaml

    interface: products
    family: list
    name: my_clavrx_products
    docstring: |
      CLAVR-x imagery products
    spec:
      products:
        - name: My-Cloud-Top-Height
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Top Height
          product_defaults: Cloud-Height
          spec:
            variables: ["cld_height_acha", "latitude", "longitude"]
        - name: My-Cloud-Base-Height
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Base Height
          product_defaults: Cloud-Height
          spec:
            variables: ["cld_height_base", "latitude", "longitude"]
        - name: My-Cloud-Depth
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Depth
          product_defaults: Cloud-Height
          spec:
            variables: ["cld_height_acha", "cld_height_base", "latitude", "longitude"]

* We now have two variables, but if we examine the `Cloud-Height Product Defaults https://github.com/NRLMMD-GEOIPS/geoips_clavrx/blob/main/geoips_clavrx/plugins/yaml/product_defaults/Cloud-Height.yaml`_
  we see that it uses the “single_channel” algorithm.
* This algorithm just manipulates a single data variable and plots it.
* We need a new algorithm! See the *Algorithms* section.

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
