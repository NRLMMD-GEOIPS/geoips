Plugins
=======

GeoIPS is composed almost entirely of plugins. Plugins are are modular pieces
of code that perform specific functions or yaml that modify the behavior of
those functions. These plugins can be used in Python scripts and packages or
configured in YAML files to create consistent, reliable, infrastructure-as-code
workflows. This section provides an overview of the plugin system and the
various kinds of plugins that GeoIPS supports.

Class-based & Yaml-based Plugins
--------------------------------

There are two major types of plugins, each of which has several kinds. These
are Class-based plugins and Yaml-based plugins. Class-based plugins provide
callable functionality while Yaml-based plugins configure the behavior of the
class-based plugins. For example, an ``Interpolator`` plugin is a class-based
plugin that performs interpolation while a ``Sector`` plugin is a Yaml-based
plugin that configures the behavior of the ``Interpolator`` plugin by defining
a geographical region to interpolate to.

.. warning::
   There is a third, deprecated, type of plugin called a module-based
   plugin.  These plugins are being phased out in favor of class-based plugins and
   new module-based plugins should not be created. For more information on
   module-based plugins, see :ref:`here <module-based-plugins>`.

Plugin Interfaces
-----------------

The various plugin kinds are managed by ``Interfaces``. There is one interface
per plugin kind (e.g. ``InterpolatorsInterface``, ``ReadersInterface``,
``SectorsInterface``, etc.). All interfaces provide the same basic
functionality for retrieving and validating plugins.

Generally, the only interaction users will have with interfaces is to import
them and call their ``get_plugin()`` method to retrieve a specific plugin. For
example, to retrieve the ``Reader`` plugin for GOES ABI NetCDF data, you would
do the following:

.. code-block:: python

    from geoips.plugins.interfaces import Readers

    reader = Readers.get_plugin("abi_netcdf")

Likewise, to retrieve the ``Sector`` plugin for the Continental US, you would
do the following:

.. code-block:: python

    from geoips.plugins.interfaces import Sectors

    sector = Sectors.get_plugin("conus")

Plugin Types & Kinds
--------------------

.. toctree::
    :maxdepth: 2

    class-based/index
    yaml-based/index
    module-based