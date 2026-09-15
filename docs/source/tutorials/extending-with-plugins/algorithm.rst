.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _add-an-algorithm:

Extend GeoIPS with a new Algorithm
**********************************

To extend GeoIPS with a new ``algorithm`` plugin, first follow the :ref:`instructions for
setting up a plugin package<plugin-development-setup>`.

In GeoIPS 2.0, algorithms are **class-based** plugins: a Python class that subclasses the
algorithm base class and sets three class attributes:

* ``interface``
* ``family``
* ``name``

See :ref:`writing-class-based-plugins` for the full class-based plugin contract, and
:ref:`the algorithm interface <algorithm_functionality>` for the argument model. If you are
migrating a 1.x module-based algorithm, see :ref:`converting-module-to-class`.

Creating an Algorithm
---------------------

The following steps teach you how to create a custom algorithm plugin. Change directories
to your package's ``classes`` algorithm directory:

::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/classes/algorithms

Create a file called ``my_cloud_depth.py``. A class-based algorithm subclasses
``BaseAlgorithmPlugin``, sets ``interface``/``family``/``name``, and implements a
``call`` method. The ``call`` method is where the data manipulation happens; GeoIPS invokes
it for you (directly, or as a step in an :ref:`OBP workflow <order-based-processing>`).

The complete plugin looks like this:

.. literalinclude:: examples/my_cloud_depth.py
   :language: python
   :lines: 4-

A few things to note:

* The class name follows the ``<Name><Interface>Plugin`` convention
  (``MyCloudDepthAlgorithmPlugin``).
* ``family`` (here ``xarray_to_xarray``) determines the call signature and how GeoIPS
  converts data into and out of your plugin. To see the arguments each family expects, see
  the `algorithm base class
  <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/interfaces/class_based/algorithms.py>`_.
* ``variables`` is ordered — it matches the order you define variables in your product
  plugin, so ``variables[0]`` and ``variables[1]`` are cloud top height and cloud base
  height respectively.
* You can add as many keyword arguments as you need, provided your product supplies them.
* The module ends with ``PLUGIN_CLASS = MyCloudDepthAlgorithmPlugin``. This tells the
  plugin registry (``pluginify``) which class in the file is the plugin to register.

After adding the plugin, rebuild the plugin registries so GeoIPS can find it:

.. code-block:: bash

    geoips config create-registries
    geoips list algorithms          # confirm my_cloud_depth appears
    geoips describe alg my_cloud_depth

.. note::

   The plugin above is a real, tested example. It lives at
   ``docs/source/tutorials/extending-with-plugins/examples/my_cloud_depth.py`` and is
   imported and executed by ``tests/unit_tests/docs/test_tutorial_examples.py``, so this
   tutorial's code stays runnable.

Using your algorithm
--------------------

Algorithms are not used on their own — they are one step of a larger product. If you have
already created a Product in the :ref:`Products<create-a-product>` section, revisit your
:ref:`My-Cloud-Depth product definition<cloud-depth-product>` to reference the algorithm you
just created. The product (or the workflow that includes it) supplies the ``variables``,
``output_data_range``, and ``scale_factor`` arguments your ``call`` method expects.

Your algorithm then runs as part of an :ref:`Order-Based Processing workflow
<order-based-processing>`, either directly (``geoips run order_based <workflow> <files>``)
or via a product step. The same class can also be called from a Python script — see
:ref:`scripting-guide`.
