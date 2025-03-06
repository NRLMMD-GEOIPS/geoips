.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _plugin-extend:

Extend GeoIPS with Plugins
**************************

GeoIPS is almost entirely composed of plugins and can be extended by developing new plugins in external python
packages. The ability to extend GeoIPS using plugins means that there is no need to edit the main GeoIPS code to add
new functionality.  Most types of functionality in GeoIPS can be extended. If you encounter something that you would
like to be able to extend but are unable to, please contact the GeoIPS team or create an issue on GitHub.

Developing a new plugin for GeoIPS requires developing a new Python package, known as a "plugin package" within
GeoIPS. The plugin package can contain one or more plugins. It is configured in a special way such that, when it is
installed, it registers itself and its plugins with GeoIPS.

An example repository `Template Basic Plugin <https://github.com/NRLMMD-GEOIPS/template_basic_plugin/tree/main>`_ is
provided that can guide you through the process of creating a new plugin package containing one or more custom plugins.

.. _plugin-vocabulary:

GeoIPS Plugin Vocabulary
========================

Plugin
------
A GeoIPS plugin may be either a Python module or a YAML file that extends GeoIPS with new functionality. The type
(Python module / YMAL) of the product plugin is determined by its interface.

Plugins are stored in installable Python packages that register their payload with GeoIPS through the use of
`entrypoints <https://packaging.python.org/en/latest/specifications/entry-points/>`_.

Module-based Plugin
-------------------
A module-based plugin extends GeoIPS by adding new functionality capable of performing specific actions, such as
applying an algorithm, read data, or formatting outputs. These plugins are defined as a single python modules
containing a few required top-level variables and a function that executes the plugin's action. Examples of
module-based plugins include ``algorithms``, ``readers``, and various types of formatters.

YAML-based Plugin
-----------------
A YAML-based plugin extends GeoIPS by adding a new set of static configuration options for GeoIPS. Examples of
YAML-based plugins include ``sectors``, ``products``, and ``feature-annotators``.

.. _required-attributes:


Plugin Attributes:
------------------

The following are the top-level plugin attributes. Any required attribute will be explicitly stated.

#. Interface

   **Required.** An ``interface`` defines a class of GeoIPS plugins that extend    the same type of functionality
   within GeoIPS. For example, some commonly used interfaces include the ``algorithms``, ``colormappers``, and
   ``sectors`` interfaces.

#. Family (Required)

   **Required.** A ``family`` is a subset of an interface's plugins which accept specific sets of
   arguments/properties. Module-based plugins of the same ``family`` have similar call signatures. YAML-based plugins
   of the same ``family`` are validated against the same schema (i.e. they contain the same properties).

#. Docstring (Required)

   **Required.** A ``docstring`` is a block of documentation that describes a plugin's functionality. It is required
   for all GeoIPS plugins, whether module-based or YAML-based, to ensure proper documentation.
