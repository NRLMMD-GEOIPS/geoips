:orphan:

Documentation for Product Pluign Development by Extending GeoIPS
=================================================================

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

.. _plugin-extend:

****************************************
Product Creation by Extending GeoIPS
****************************************

This tutorial elaborates on product creation using GeoIPS. We will create three products
using CLAVR-x: **Cloud-Top-Height**, **Cloud-Base-Height**, and **Cloud-Depth**. Products
are the cornerstone plugin for GeoIPS, as they define how to produce a specific product as
a combination of other plugins. Products use other plugins, such as an algorithm, colormapper,
interpolater, etc. to generate the intended output.

GeoIPS is almost entirely composed of plugins and can be extended by developing new plugins in
external python packages. The ability to extend GeoIPS using plugins means that there is no
need to edit the main GeoIPS code to add new functionality.  Most types of functionality in
GeoIPS can be extended. If you encounter something that you would like to be able to extend
but are unable to, please contact the GeoIPS team or create an issue on GitHub.

Developing a new plugin for GeoIPS requires developing a new Python package that GeoIPS
terms a "plugin package". The plugin package can contain one or more plugins. It is
configured in a special way such that, when it is installed, it registers itself and its plugins
with GeoIPS.

.. _plugin-vocabulary:

GeoIPS Plugin Vocabulary
************************

Plugin
------
A GeoIPS plugin is used to develop a new product by using/extending GeoIPS through a Python module or a
YAML file. By product we mean development of a new functionality using GeoIPS as a base.
The type (Python module / YMAL) of the product plugin is determined by its interface.

Plugins are stored in installable Python packages that register their payload with
GeoIPS through the use of
`entrypoints <https://packaging.python.org/en/latest/specifications/entry-points/>`_.

#. Module-based Plugin

   A module-based plugin is a plugin that extends GeoIPS by adding new
   functionality that is capable of performing an action (e.g. apply an algorithm,
   read data, apply formatting, etc.).  Module-based plugins are defined as a
   single python module that contains a handful of required top-level variables and
   a single function that performs the action of the plugin. Examples of
   module-based plugins include ``algorithms``, ``readers``, and various types of
   formatters.

#. YAML-based Plugin

   A YAML-based plugin is a plugin that extends GeoIPS by adding a new set of
   static configuration options for GeoIPS.  Examples of YAML-based plugins include
   ``sectors``, ``products``, and ``feature-annotators``.

.. _required-attributes:

Plugin Attributes:
------------------

The following are the top level attributes required while defining a new product plugin:

#. Interface

   An ``interface`` defines a class of GeoIPS plugins that extend the same type of
   functionality within GeoIPS. For example, some commonly used interfaces include the
   ``algorithms``, ``colormappers``, and ``sectors`` interfaces.

#. Family

   A ``family`` is a subset of an interface's plugins which accept specific sets of
   arguments/properties. Module-based plugins of the same ``family`` have similar call
   signatures. YAML-based plugins of the same ``family`` are validated against the same
   schema (i.e. they contain the same properties).

#. Docstring

   A ``docstring`` is a chunk of documentation which describes what your plugin does. This
   property is required for every GeoIPS plugin created, module-based or YAML-based. We
   require this property for proper documentation of created plugins, and it will also be
   a useful feature later on when the GeoIPS Command Line Interface (CLI) is created, as
   you will be able to see what each plugin does provided the ``docstring`` for that plugin
   is filled.

.. _plugin-development-setup:

Product Plugin Development Initial Setup
****************************************

Before creating a new product for CLAVR-x Cloud-Top-Height, let's get the initial setup done:

#. To develop a new GeoIPS plugin, install :ref:`GeoIPS<linux-installation>` and make sure that
   you have ``geoips`` Python environment enabled throughout this tutorial using

   .. code-block:: shell

    mamba activate geoips # activating python envrionment

   You will know if geoips environment is enabled if it shows up ahead of your username in your command prompt.

#. Next, let's install GeoIPS CLAVR-x package and test the installation. This is needed as we are developing products
for GeoIPS CLAVR-x.

   .. code-block:: shell

    git clone https://github.com/NRLMMD-GEOIPS/geoips_clavrx $GEOIPS_PACKAGES_DIR/geoips_clavrx # download the remote
    repository
    pip install -e $GEOIPS_PACKAGES_DIR/geoips_clavrx # installing the geoips_clavrx

    $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_clavrx      # Install the clavrx
    test data repo
    $GEOIPS_PACKAGES_DIR/geoips_clavrx/tests/test_all.sh  # Run tests to verify geoips-clavrx installation

#. Now, set the following additonal environment variables which are specific to your product plugin development

   .. code-block:: shell

      export MY_PKG_NAME=<your package name>    #read the note below for your package name,
      export MY_PKG_DIR=$GEOIPS_PACKAGES_DIR/$MY_PKG_NAME    #your package directory
      export MY_PKG_URL=<your package’s URL on version control platform(GitLab)> #your package VCS url

   .. NOTE::
    Choose a name for your package making sure that it is in lower case, starting with a letter,
    and only contains letters, numbers, and underscores.

#. Navigate to your product plugin directory and clone the example repository of customized plugin development,
`Template Basic Plugin <https://github.com/NRLMMD-GEOIPS/template_basic_plugin/tree/main>`_
   that would guide us through the process of creating a new plugin package containing one or more custom plugins.

   .. code-block:: shell

      cd $GEOIPS_PACKAGES_DIR         #Go to your package directory
      git clone --no-tags --single-branch $GEOIPS_REPO_URL/template_basic_plugin.git

   .. NOTE::
    If you're not able to move into the directory listed in the above code-block. Verify if the values of
    environment variable(s) is/are set using the command shown below otherwise check the step three again
    and if needed take help, we will be using these environment variables again in the development

    .. code-block:: shell

      echo $MY_PKG_NAME : should reflect your package name
      echo $MY_PKG_DIR  : should reflect merged path of $GEOIPS_PACKAGES_DIR/$MY_PKG_NAME

#.  Owning tutorial template package: change it's name, set the git branch to main, change it's remote repo URL, and
push

    .. code-block:: shell

       mv template_basic_plugin/ $MY_PKG_NAME
       cd $MY_PKG_NAME
       git remote set-url origin $MY_PKG_URL
       git branch -m main
       git push -u origin main

#. Navigate to your Plugins directory and look around. Also, we will change the repo name from ``my_package`` to your
own package name

   .. code-block:: shell

      cd $MY_PKG_DIR
      git mv my_package $MY_PACKAGE_NAME

#. Update Pertinent files

   #. Installing a Python package requires metadata that describes the package and how to
      install it. GeoIPS uses ``pyproject.toml`` to define this information. Open ``pyproject.toml``
      in your ``$MY_PKG_DIR`` and replace the following:

      * Update ``@package@`` to your package name.
      * Update ``my_package`` to your package name.

   #. Update README.md

      * Find and replace all occurrences of @package@ with your package name

   #. Add, commit, and push your changes

      .. code-block:: shell

         git add README.md pyproject.toml
         git commit -m "Updated name of template plugin package to mine"
         git push

Plugin Product Custom Definition & Development
***********************************************

Now that initial setup is done, we will first start with installing your bare bones version of your plugin.
After that we will go hands on in creating a product CLAVR-x Cloud-Top-Height.

We are now going to dive into hands-on experience by creating a product for CLAVR-x Cloud-Top-Height:

#. Install your package using the command below. The flag -e means “editable” which lets us edit the package after it is
installed.
   The subsequent edits will be reflected in the installed package

   .. code-block:: python

      pip install -e .  # remember there is a period character at the end

#. Copy the template product plugin definition file to new file to modify:

   .. code-block:: shell

      cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products
      cp amsr2_product_defaults.yaml my_clavrx_products.yaml

#. Navigate to your product plugins directory and create a file called ``my_clavrx_products.yaml``

   .. code-block:: shell

      cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products
      touch ``my_clavrx_products.yaml``

#. Now, create a file called ``my_clavrx_products.yaml`` and add the following code into it

   .. code-block:: yaml

      interface: products
      family: list
      name: my_clavrx_products
      docstring: |
           CLAVR-x imagery products

   The code snippet shown above shows properties required in every GeoIPS plugin, YAML-based or
   Module-based. These properties help GeoIPS understand the type of plugin you are developing
   and also defines the schema your plugin will be validated against.

   It is recommended to go through the definitions of the top level attributes such as ``interface``,
   ``family``, and ``docstring`` that are required in any GeoIPS plugin.
   Click here
   :ref:`click here <required-attributes>`
   (page scrolls up) to go the related documentation.

Cloud Top Height Product:
-------------------------

Now we'll add the ``spec`` portion to the yaml file created in the last step to support our new product plugin.
``spec`` is a container for the 'specification' of your yaml plugin. In this case, it
contains a list of ``products``, as shown below. Denoted by the ``family: list``
property shown above, this yaml file will contain a list of products, which can be of
length 1 if you so desire.

Append the code below at the end of yaml file, under the docstring you wrote, with no tabs behind it. YAML is a
whitespace-based coding language, similar to Python in that aspect.

  .. code-block:: yaml

    spec:
      products:
        - name: My-Cloud-Top-Height      # name of the product you're defining
          source_names: [clavrx]         # defined as metadata in the corresponding reader
          docstring: |                   # Pipe says to YAML this will be a multiline comment
            CLAVR-x Cloud Top Height
          product_defaults: Cloud-Height # see the Product Defaults section for more info
          spec:
            # Variables are the required parameters needed for the product generation
            variables: ["cld_height_acha", "latitude", "longitude"]

Script to Visualize Your Product
--------------------------------

GeoIPS is called via a command line interface (CLI). The primary command that you will use is
``run_procflow`` which will process your data through the selected procflow using the specified
plugins. Scripts are stored in your plugin package's ``tests/`` directory as they can be later used
for regression test of package you're developing.

#. To use your product that you just created, you'll need to create a bash script that
   implements ``run_procflow`` (run-process-workflow). This script defines the
   *process-workflow* needed to generate your product. It can be used to specify how you want your product to be
   created, output format, and define the sector you'd like your data to be plotted on apart from
   enlisting comparison of the output product with a validated product(optional).

#. Check if you have the test data for the clavrx within ``$GEOIPS_TESTDATA_DIR`` and if not run the following.
   ::

       $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_clavrx

#. We'll now create a test script to generate an image for the product you just created. Change directories into your
scripts directory.
   ::

        cd $MY_PKG_DIR/tests/scripts

#. Create a bash bash file called clavrx.conus_annotated.my-cloud-top-height.sh and edit it
   to include the codeblock below.

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
       ss_retval=$?

   As shown above, we define which procflow we want to use, which reader,
   what product will be displayed, how to output it, which filename formatter will be used,
   the minimum coverage needed to create an output (% based), as well as the sector used to
   plot the data. Many more items can be added if wanted. If you'd like some examples of
   that, feel free to peruse the `GeoIPS Scripts Directory
   <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/tests/scripts>`_.

#. Run your test script as shown below to produce Cloud Top Height Imagery:
   ::

        $MY_PKG_DIR/tests/scripts/clavrx.conus_annotated.my-cloud-top-height.sh

This will write some log output. If your script succeeded it will end with INTERACTIVE:
Return Value 0. To view your output, look for a line that says SINGLESOURCESUCCESS. Open
the PNG file, it should look like the image below.

.. image:: ../../images/command_line_examples/my_cloud_top_height.png
   :width: 800

Okay! We've developed a plugin which produces CLAVR-x Cloud Top Height. This is nice,
but what if we want to extend our plugin to produce Cloud Base Height? What about Cloud
Depth? Using the method shown above, we're going to extend our my_clavrx_products.yaml
to produce just that.

Cloud Base Height Product:
--------------------------

Using your definition of My-Cloud-Top-Height as an example, create a product definition
for My-Cloud-Base-Height.
::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products

Now, edit my_clavrx_products.yaml. Here are some helpful hints:
  * The relevant variable in the CLAVR-x output file (and the equivalent GeoIPS reader) is called "cld_height_base"
  * The Cloud-Height product_default can be used to simplify this product definition (or you can DIY or override if
    you'd like!)

The correct products implementation for 'my_clavrx_products.yaml' is shown below.
Hopefully, you didn't have to make any changes after seeing this! Developing products,
and other types of plugins should be somewhat intuitive after completing this tutorial.

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

Cloud Depth Product:
--------------------

Now that we have products for both Cloud Top Height and Cloud Base Height, we can
develop a product that produces Cloud Depth. To do so, use your definitions of
My-Cloud-Top-Height and My-Cloud-Base-Height as examples, create a product definition
for My-Cloud-Depth.
::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products

Edit my_clavrx_products.yaml. Here is a helful hint to get you started:
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

We now have two variables, but if we examine the `Cloud-Height Product Defaults
<https://github.com/NRLMMD-GEOIPS/geoips_clavrx/blob/main/geoips_clavrx/plugins/yaml/product_defaults/Cloud-Height.yaml>`_
we see that it uses the ``single_channel`` algorithm. This doesn't work for our use case,
since the ``single_channel`` algorithm just manipulates a single data variable and
plots it. Therefore, we need a new algorithm! See the
:ref:`Algorithms Section<add-an-algorithm>` to keep moving forward with this turorial.

.. _cloud-depth-product1:

Using Your Cloud Depth Product
------------------------------

Note: Before moving forward in this section, make sure you've completed
:ref:`creating a new algorithm<add-an-algorithm>`. We are going to modify our Cloud
Depth product to use the algorithm we just created.

Now that we've created our cloud depth algorithm, we need to implement it in our cloud
depth product. As shown in the :ref:`Product Defaults Section<create-product-defaults>`,
we can override the product defaults specified to our own specification. To do so,
modify ``My-Cloud-Depth`` product in my_clavrx_products.yaml to the code block shown
below.

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
            algorithm:
              plugin:
                name: my_cloud_depth
                arguments:
                  output_data_range: [0, 20]
                  scale_factor: 0.001

The changes shown above modify My-Cloud-Depth to use our ``my_cloud_depth`` algorithm
that we created. If we left this portion unchanged, My-Cloud-Depth would use the
``single_channel`` algorithm, which is unfit for our purposes. We also added two other
arguments, ``output_data_range`` ands ``scale_factor``, which override the Cloud-Height
product defaults arguments for those two variables. Output data range of [0, 20] states
that our data will be in the range of zero to twenty, and the scale factor says that we
are scaling our data to be in kilometers.

To use this modified My-Cloud-Depth product, follow the series of commands. We will be
creating a new test script which implements our new changes.
::

    cd $MY_PKG_DIR/tests/scripts
    cp clavrx.conus_annotated.my-cloud-top-height.sh clavrx.conus_annotated.my-cloud-depth.sh

Now we need to edit ``clavrx.conus_annotated.my-cloud-depth.sh`` to implement
``My-Cloud-Depth`` rather than ``My-Cloud-Top-Height``. Your new test script should look
like the code shown below.

.. code-block:: bash

  run_procflow \
      $GEOIPS_TESTDATA_DIR/test_data_clavrx/data/goes16_2023101_1600/clavrx_OR_ABI-L1b-RadF-M6C01_G16_s20231011600207.level2.hdf \
      --procflow single_source \
      --reader_name clavrx_hdf4 \
      --product_name My-Cloud-Depth \
      --output_formatter imagery_annotated \
      --filename_formatter geoips_fname \
      --minimum_coverage 0 \
      --sector_list conus
  ss_retval=$?

Nice! Now all we need to do is run our script. This will display Cloud Depth over the
CONUS sector. To do so, run the command below.
::

    $MY_PKG_DIR/tests/scripts/clavrx.conus_annotated.my-cloud-depth.sh

This will output a bunch of log output. If your script succeeded it will end with INFO:
Return Value 0. To view your output, look for a line that says SINGLESOURCESUCCESS. Open
the PNG file to view your Cloud Depth Image! It should look like the image shown below.

.. image:: ../../images/command_line_examples/my_cloud_depth.png
   :width: 800
