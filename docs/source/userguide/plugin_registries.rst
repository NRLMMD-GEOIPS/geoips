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

In summary, the plugin registry is a cached ledger of all available plugins within every
geoips package, that can be used for all GeoIPS functionality. When new plugins are
added, users need to run ``create_plugin_registries``, to update the cached registry
to include your new plugins. Moving from the legacy dynamic system to the current
pre-built plugin registry cache reduced the start up time of GeoIPS twenty-fold.

Defining a Plugin Registry
--------------------------

Plugin Registries are crucial for processing with GeoIPS. Essentially,
they are large dictionaries that store information about plugins across
all GeoIPS packages. They also provide the backend of GeoIPS with functionality
to locate and validate each plugin at runtime.

There are two methods to create Plugin Registries: one prioritizes readability
(YAML-based), and the other efficiency (JSON-based). The motivation for
Plugin Registries stemmed from the inefficiencies observed in the
`geoips/geoips/geoips_utils.py:load_all_yaml_plugins` function. This function was
responsible for locating all YAML-based plugins in the GeoIPS packages and merging
them into a single, nested dictionary for access by the YAML-based interfaces. Despite
its good intentions, it was called multiple times (5 times, one for each interface),
significantly impacting GeoIPS performance.

To address this, the new `PluginRegistry` class was introduced, utilizing the
`create_plugin_registries.py` script for its creation. It significantly improves
efficiency, requiring only a single load operation for any GeoIPS import statement.
This efficiency is achieved by integrating it as a top-level property, inherited across
all interface types.



Creating a Plugin Registry
--------------------------

To create a plugin registry, we first must define what needs to be in each registry.
At its top level, a plugin registry defines three keys:
*{module_based, yaml_based, text_based}*. These keys encapsulate the three plugin types
used in GeoIPS. For example, a module_based plugin can be an algorithm, reader, etc.
A text_based plugin (while not many exist), defines a custom ASCII palette used by
some plugins. A yaml_based plugin, as its name implies, is a yaml file which defines
properties for a certain plugin. This can be a product, product_default, sector, etc.

The organization within the plugin registry is further refined by categorizing plugins
under their corresponding interfaces, facilitating one-call access to plugins based
on their operational context. This structure allows for efficient plugin locating,
loading, and processing, serving as a comprehensive catalog of all plugins across
the GeoIPS packages.

For instance, to access a YAML plugin named ``denver``, one
would navigate through the registry using a structured path that reflects the plugin's
characteristics and location, as illustrated in the following example:

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

Using this information, we would create an entry in the registry that looks like this.
In the case shown below, this is a yaml-based plugin registry for the GeoIPS package.

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

Benefits of a Plugin Registry
-----------------------------

The efficiency of the new plugin registries is a twenty-fold reduction in GeoIPS startup
time. In practice, this resulted in a reduction from >10 seconds to 0.5 seconds when
importing GeoIPS. Largely, this is attributable to efficient json loading and only
instantiating the plugin registry when a user requests a plugin. Before, we dynamically
created the yaml-registry for each yaml interface (5 in total), which was often
unnecessary and took much longer for a single call than it does for creating a plugin
registry with our new methods.

..
    what was the instantiation like before reducing instantiation? also: work on that
    sentance

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
been surpplanted.  This is favourable because it enables standardized accessing of
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

