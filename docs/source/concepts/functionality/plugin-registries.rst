.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _using-plugin-registries:

Using Plugin Registries
***********************

Plugin registries are a cache used by GeoIPS to speed up start up times.

When to Create/Update Plugin Registries
---------------------------------------
The plugin registries must be created/updated any time one of the following
occurs:

* GeoIPS is installed or reinstalled
* A new plugin package is installed or reinstalled
* A plugin package is uninstalled
* An individual plugin is added, edited, or removed

.. note::
    We hope to automate the process of creating/updating the plugin registries
    in the future to avoid requiring the user to directly call
    ``create_plugin_registries``.

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
