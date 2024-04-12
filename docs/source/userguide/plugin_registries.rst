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

.. _plugin-registries:


**********************************
GeoIPS Plugin Registries
**********************************

GeoIPS makes use of plugin registries to reduce start up time. The process of
locating, loading, and validating all of the plugins in GeoIPS is slow. To
mitigate that slowness, plugin registries are used to cache information about
each available plugin in the GeoIPS environment. The registries are then used
by the CLI and other parts of GeoIPS to quickly access information about the
available plugins as well as locate and load individual plugins.  Moving from
the legacy dynamic system to the current pre-built plugin registry cache
reduced startup time for the GeoIPS CLI twenty-fold.

When to Create/Update Plugin Registries
----------------------------------------
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

Plugin Registry Contents
------------------------

Each plugin registry contains a dictionary describing each plugin provided by
the registry's plugin package. The registry dictionary is organized into a
four-level structure where the levels are as follows:

1. Plugin Interface Type (i.e. module_based, yaml_based, text_based)
2. Interface Name (i.e. algorithms, products, sectors, etc.)
3. Plugin Name
4. Plugin Attributes (e.g. relpath, package, docstring, etc.)

.. note::
    The registry adds a fifth level in the case of compound plugins such as
    product plugins whose family is ``list``. In this case, the fourth level
    is the name of each sub-plugin in the compound plugin and the plugin
    attributes are moved to the fifth level.

This structure allows for efficient plugin locating, loading, and processing,
serving as a comprehensive catalog of all plugins across the GeoIPS packages.
For instance, to access a YAML plugin named ``denver``, one would navigate
through the registry using a structured path that reflects the plugin's
characteristics and location. For example, given the following sector
definition for ``denver``

.. code-block:: yaml

    interface: sectors
    family: area_definition_static
    name: denver
    docstring: "City of Denver"
    spec:
        etc: ...
    relpath: plugins/yaml/sectors/static/denver.yaml
    abspath: /local/home/user/geoips/geoips_packages/geoips/geoips/plugins/yaml/sectors/static/denver.yaml
    package: geoips

when 'create_plugin_registries' is ran, an entry representing sector-plugin
'denver' will be added to the registry at the path ``"yaml_based/sectors/denver"``
as shown below:

..
    the relevance of this example it obvious to the developer, but needs to be
    explained to the reader explicitly

.. code-block:: yaml

    module_based:
        algorithms:
            single_channel:
                relpath: /path/to/module/plugin
                package: geoips
                other_info: ...
    text_based:
        tpw_cimss:
            relpath: /path/to/text/plugin
            package: geoips
            other_info: ...
    yaml_based:
        products:
            source_name:
                sub_product:
                    relpath: /path/to/yaml/product/plugin
                    package: geoips
                    other_info: ...
        sectors:
                denver:
                    docstring: "City of Denver"
                    family: area_definition_static
                    interface: sectors
                    package: geoips
                    plugin_type: yaml_based
                    relpath: plugins/yaml/sectors/static/denver.yaml

With this information, we have accessible intel to locate, load, and process the plugins
without multiple calls. Having this registry cached for all of GeoIPS is extremely
impactful on startup time, as we no longer need to dynamically locate these plugins
during runtime to use their functionality.
In-depth Motivation for Plugin Registries
-----------------------------------------

The motivation for Plugin Registries stemmed from the inefficiencies observed
in the `geoips/geoips/geoips_utils.py:load_all_yaml_plugins` function. This
function was responsible for locating all YAML-based plugins in the GeoIPS
packages and merging them into a single, nested dictionary for access by the
YAML-based interfaces. Despite its good intentions, it was called multiple
times (5 times, one for each interface), significantly impacting GeoIPS
performance.

To address this, the new `PluginRegistry` class was introduced, utilizing the
`create_plugin_registries.py` script for its creation. It significantly
improves efficiency, requiring only a single load operation for any GeoIPS
import statement.  This efficiency is achieved by integrating it as a top-level
property, inherited across all interface types.

Benefits of a Plugin Registry
-----------------------------

The high efficiency of the new plugin registries led to a twenty-fold reduction
in startup time. In practice, this resulted in a reduction from >10 seconds to
0.5 seconds when importing GeoIPS or calling the CLI. Largely, this is
attributable to efficient json loading and waiting to instantiate the plugin
registry until a user requests a plugin. Before, we dynamically created the
yaml-registry for each yaml interface (5 in total) by searching entry points,
which was slower than creating a comprehensive plugin registry for all plugins
(per-plugin call vs entire cache generation).

Another benefit is the easily accessible information stored in the plugin registry. We
can search through the registry for every plugin of each package and find a
quick overview on whether a given plugin is valid and where it exists.

We've also created tests, and unit tests, for the new PluginRegistry class. This helps
with monitoring that registries and the plugins that they contain are performing
correctly. The tests ensure plugins have specific attributes, and that no duplicate
plugin names exist in a certain interface. They also validate registries to ensure
correct formatting, and in the event of invalid formatting, they raise an appropriate
error that explains the discrepancy.

Module_based plugins now use plugin registries instead of entry points. Previously,
module plugins were accessed via their entry-point contained in a ``pyproject.toml``
file. Thanks to the information stored in the plugin registries, this functionality has
been supplanted.  This is favourable because it enables standardized accessing of
plugins in a manner similar to that currently used to access yaml_based plugins.

For more information about plugin registries, feel free to look at the source code for
their related scripts:

* Creating the plugin registry can be found `in the create_plugin_registries.py file
  <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/create_plugin_registries.py>`_.
* The PluginRegistry Class, which makes use of the plugin registries created by the
  script above, can be found `in the plugin_registry.py file
  <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugin_registry.py>`_.
* Finally, the unit tests that ensure the correct functionality of plugin registries,
  can be found `in the test_plugin_registries.py file
  <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/tests/unit_tests/plugin_registries/test_plugin_registries.py>`_.

