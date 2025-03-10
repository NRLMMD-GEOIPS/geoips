.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _using-plugin-registries:

Using Plugin Registries
***********************

Plugin registries are a cache used by GeoIPS to speed up start up times. By default
GeoIPS automates the creation of the plugin registry, but this can be turned off if
desired by changing an environment variable.

Automatic creation of the plugin registry occurs if a requested plugin could not be
found in the registry. GeoIPS will attempt to build the registry once if this failure
occurs. However, if the missing plugin persists after the registry has been
automatically created, an error will be raised informing the user how to fix this
problem.

If using manual plugin registry creation, please follow the sections
below.

Turning Off Automatic Creation of Plugin Registries
---------------------------------------------------

By default, GeoIPS automates the creation of plugin registries. If manual creation is
preferred, all the user has to do is create an evironment variable called
``GEOIPS_REBUILD_REGISTRIES`` and set it to false. When creating this variable, there
are two options:

1. Single Session Manual Creation
---------------------------------
Use this method if you only want automatic creation of the plugin registry to be turned
off for a single terminal session.

.. code:: bash

    export GEOIPS_REBUILD_REGISTRIES=0

2. Sesson Persisting Manual Creation
------------------------------------
Use this method if you want automatic creation of the plugin registry to be turned off
for all of your terminal sessions. Note you can also manually update your ``.bashrc``
by including the quoted portion of the code below.

.. code:: bash

    echo "export GEOIPS_REBUILD_REGISTRIES=0" >> ~/.bashrc
    source ~/.bashrc
    conda activate geoips

When to Create/Update Plugin Registries
---------------------------------------
The plugin registries must be created/updated any time one of the following
occurs:

* GeoIPS is installed or reinstalled
* A new plugin package is installed or reinstalled
* A plugin package is uninstalled
* An individual plugin is added, edited, or removed

How to Create/Update the Plugin Registries
------------------------------------------
``create_plugin_registries`` executable can be called to create or update the
plugin registries.

This executable will create a separate registry for each installed GeoIPS
plugin package. Each registry will contain a dictionary of all available
plugins provided by that package. The registry will be written in the
top-level directory of the installed plugin package and will, by default, be
written in JSON and named ``registered_plugins.json``.

The executable can be called with the ``-s yaml`` option to specify the output
format as YAML rather than JSON. This is useful for debugging since YAML is,
arguably, easier to read than JSON. The YAML registries will be ignored by
GeoIPS, though, because they are significantly slower to load than JSON.

.. admonition:: Usage: create_plugin_registries

    .. autoprogram:: geoips.create_plugin_registries:get_parser()
        :prog: create_plugin_registries
