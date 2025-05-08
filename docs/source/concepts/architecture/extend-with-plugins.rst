.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _plugin-extend:

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

An example repository `Template Basic Plugin <https://github.com/NRLMMD-GEOIPS/template_basic_plugin/tree/main>`_
is provided that can guide you through the process of creating a new plugin package
containing one or more custom plugins.

.. _plugin-vocabulary:

GeoIPS Plugin Vocabulary
========================

Plugin
------
A GeoIPS plugin may be either a Python module or a YAML file that extends GeoIPS with
new functionality. Whether a plugin is a Python module or a YAML file is determined by
its interface.

Plugins are stored in installable Python packages that register their payload with
GeoIPS through the use of
`entrypoints <https://packaging.python.org/en/latest/specifications/entry-points/>`_.

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

.. _required-attributes:

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

Docstring
---------

A ``docstring`` is a chunk of documentation which describes what your plugin does. This
property is required for every GeoIPS plugin created, module-based or YAML-based. We
require this property for proper documentation of created plugins, and it will also be
a useful feature later on when the GeoIPS Command Line Interface (CLI) is created, as
you will be able to see what each plugin does provided the ``docstring`` for that plugin
is filled.
