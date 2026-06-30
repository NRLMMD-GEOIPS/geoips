Interfaces
==========

GeoIPS plugins are managed, validated, and accessed via plugin interfaces.
Each plugin interface is responsible for managing a specific kind of plugin.
Each interface provides the same main methods and are the primary way through
which users can access plugins.

.. autoclass:: geoips.interfaces.base.BaseInterface
    :members:
    :noindex: