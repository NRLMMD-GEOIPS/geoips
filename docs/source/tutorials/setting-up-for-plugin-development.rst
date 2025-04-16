.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _plugin-development-setup:

Setting up for Plugin Development
=================================

1. To develop a new GeoIPS plugin, first :ref:`install GeoIPS<installing-geoips>` and ensure
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
