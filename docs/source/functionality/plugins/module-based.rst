.. _module-based-plugins:

Module-based Plugins (Deprecated)
=================================

Module-based plugins are a **deprecated** type of plugin. They are being
phased out in favor of class-based plugins. New module-based plugins should
not be created, but existing module-based plugins will continue to be
supported for the forseeable future.

Module-based plugins are Python modules that must contain a docstring, three
top-level variables (``interface``, ``family``, and ``name``), and a ``call()``
function. They may contain anything else as well, but these are the require
components. The ``interface``, ``family``, and ``name`` variables are used to
register the plugin in the plugin registry and the ``call()`` function is what
is called when the plugin is used.

The basic structure of a module-based plugin looks like this:

.. code-block:: python

    """
    Docstring describing the plugin.
    """

    interface = "interface_name"
    family = "family_name"
    name = "plugin_name"

    def call(*args, **kwargs):
        # Plugin functionality goes here
        pass

Module-based plugins behave exactly the same as class-based plugins and are,
in fact, converted into class-based plugins under-the-hood. However, they are
less flexiable and not easily able to take advantage of the object-oriented
features of class-based plugins.

The available module-based plugin kinds are also identical to the class-based
plugin kinds. For more information on the available plugin kinds, see
:ref:`here <class-based-kinds>`.