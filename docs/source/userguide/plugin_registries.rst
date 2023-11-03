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
GeoIPS Plugin Registries Explained
**********************************

Defining a Plugin Registry
--------------------------

Plugin Registries are fundamental to the processing of any GeoIPS code. At their core,
they are essentially large dictionaries containing information about each plugin in
every GeoIPS package. However, they are not just limited to providing information, as
they are extended in the backend of GeoIPS to be able to locate and validate eaech
plugin at runtime.

Plugin Registries can be created in two methods; one for readability's sake (YAML-based)
and another for effeciency's sake (JSON-based). The concept of Plugin Registries was
inspired by the lack of efficiency brought about by
geoips/geoips/geoips_utils.py:load_all_yaml_plugins. This function was responsible for
locating all yaml-based plugins in every GeoIPS package, then merging them into one
nested dictionary that could be accessed by all GeoIPS yaml-based interfaces. While this
was a good idea in nature, it ended up being called 5 times (one for each interface),
and was very slow for each call.

The new PluginRegistry class, created after we made a script called
'create_plugin_registries.py', is very efficient, and is now only loaded once for any
GeoIPS import statement. We've done this by adding it as a top-level property,
inherited by every type of interface.

Creating a Plugin Registry
--------------------------

To create a plugin registry, we first must define what needs to be in each registry.
At it's top level, a plugin registry defines three keys:
*{module_based, yaml_based, text_based}*. These keys encapsulate every type of plugin
used in GeoIPS. For example, a module_based plugin can be an algorithm, reader, etc.
A text_based plugin (while not many exist), define a custom ascii palette used by
certain plugins. A yaml_based plugin, as its name implies, is a yaml file which defines
properties for a certain plugin. This can be a product, product_default, sector, etc.

Now that we know the types of plugins expected to be in the registry, we can go about
separating these plugins by their corresponding interfaces. At the second level of the
registry (under their corresponding plugin type), we include interfaces. This way, we
can separate plugins according to the interface they operate under. By designing the
registries in this fashion, we streamline methods to access appropriate plugins by the
information the include in their own files. For example, if we wanted to locate the
yaml_plugin *denver* we would use the information as keys shown below to access the
registry appropriately. This would give us the information we need to load in such
plugin.

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

With this information, we have enough intel to locate, load, and process the plugins
accordingly. Having this registry cached for all of GeoIPS is extremely useful, as we
no longer need to dynamically locate these plugins to use their functionality.
Essentially, we have a ledger of all available plugins within every geoips package, that
can be used for all GeoIPS functionality as a static source. When new plugins are added,
all we need to do is run *create_plugin_registries*, which will create new registries
that include your new plugins where appropriate.

Benefits of a Plugin Registry
-----------------------------

While coding the correct functionaly for creating plugin registries took quite some
time, the benefits of it definitely outweigh the time it took to get this working. First
off, the efficiency of the new plugin registries is nearly twenty-fold. What once took
ten plus seconds to import geoips, now takes around half of a second. We can attribute
this to efficient json loading, as well as only insantiating the plugin registry when a
user actually requests a plugin. Beforehand, we dynamically created the yaml-registry
for each yaml interface (5 in total), which was not only a waste of time, but took much
longer for a single call than it does for creating a plugin registry with our new
methods.

Another benefit is the information that we gain from the plugin registry. We can now
easily search through the registry for every plugin of each package, which gives us a
quick overview if plugins are valid, where they exist, and how many exist for each
interface.

We've also created tests, and unit tests, for the new PluginRegistry class. This not
only ensures that our registries are performing correctly, but also the plugins that
they contain. We ensure that plugins have specific attributes, and that no duplicate
plugin names exist in a certain interface. We also can validate registries that they are
correctly formatted, and if they are not, we can raise an appropriate error that
explains what is wrong with them.

A final boost that plugin registries provided was that module_based plugins now use
plugin registries, rather than entry points which they did before. Previously, module
plugins were accessed via their entry-point contained in their corresponding
pyproject.toml, however now that we have enough information about each module_based
plugin in the registry, we can access them without the need for entry points. This is
good, because we can now control the process of accessing these plugins, in a
standardized manner similar to yaml_based plugins.

For more information about plugin registries, feel free to look at the source code for
their related scripts. Creating the plugin registry can be found
`at this link <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/create_plugin_registries.py>`_.
The PluginRegistry Class, which makes use of the plugin registries created by the script
above, can be found `here <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugin_registry.py>`_.
Finally, the unit tests that ensure the correct functionality of plugin registries, can
be found `in geoips here <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/tests/unit_tests/plugin_registries/test_plugin_registries.py>`_.

