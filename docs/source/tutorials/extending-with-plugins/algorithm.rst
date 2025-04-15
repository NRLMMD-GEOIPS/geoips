.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _add-an-algorithm:

Extend GeoIPS with a new Algorithm
**********************************

To extend GeoIPS with a new ``algorithm`` plugin, first follow the :ref:`instructions for
setting up a plugin package<plugin-development-setup>`.

Module plugins are required to have several top-level variables:
    * name
    * interface
    * family
    * docstring

Please see documentation for
:ref:`additional info on GeoIPS required attributes<required-attributes>`

Creating an Algorithm
---------------------

The following steps will teach you how to create a custom algorithm plugin. First off,
change directories to your algorithms directory.
::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/modules/algorithms

Create a file called ``my_cloud_depth.py`` (see below). To convert this algorithm to
my_cloud_depth you'll need to update the ``docstring`` (multiline string at the top
of the file) and update the ``name`` to ``my_cloud_depth``.

Copy and paste the code block below into ``my_cloud_depth.py``

.. code-block:: python

    """Cloud depth product.

    Difference of cloud top height and cloud base height.
    """
    import logging
    from xarray import DataArray

    LOG = logging.getLogger(__name__)

    interface = "algorithms"
    family = "xarray_to_xarray"
    name = "my_cloud_depth"
    # Conventionally matches the name of the plugin definition file, but can be anything
    # that does not contain hyphens.

Each module-based plugin is required to have a ``call`` function. This is how geoips
will interact with the module-based plugins. See below for the call signature of the
my_cloud_depth.py plugin. To see a list of required arguments for each algorithm family,
see this `link <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/interfaces/module_based/algorithms.py>`_.

As for keyword arguments (kwargs), you can create as many as you want provided you include
them in your product and are needed for your algorithm.

Copy and paste this code into your algorithm file (feel free to remove the comments).

.. code-block:: python

    def call(
        xobj, # Xarray dataset holding xarrays
        variables, # list of required input variables for algorithm.
                   # Note: Python lists are ordered, so you can count on
                   # your list of variables being in the order in which you
                   # define them in your product plugin variables
        product_name,
        output_data_range,  # Range of values that your algorithm will output
        scale_factor,  # Adding a scale factor here for use in converting input meters to output kilometers
        min_outbounds="crop",
        max_outbounds="crop",
        norm=False,
        inverse=False,
    ):
        """My cloud depth product algorithm manipulation steps."""

This is where the actual data manipulation occurs. Make sure to index the variable
list to the order of the variables you defined in your product, then make the
following changes.

Add the code block below to your ``call`` function. This is how cloud-depth will be
calculated.

.. code-block:: python

    cth = xobj[variables[0]]
    cbh = xobj[variables[1]]

    out = (cth - cbh) * scale_factor

    from geoips.data_manipulations.corrections import apply_data_range

    data = apply_data_range(
        out,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )
    xobj[product_name] = DataArray(data)

    return xobj

If you have already created a Product defined in the :ref:`Products<create-a-product>`
section, we should revisit our :ref:`My-Cloud-Depth product definition<cloud-depth-product>`
to use the algorithm we just created. Note: If you haven't yet created this product, see the
:ref:`Products<create-a-product>` section.

If you are using this page as more of a guideline for how to create an algorithm plugin,
it should be noted that *algorithms are useless on their own*. This goes for other plugins
too, like colormappers, interpolators, etc. These are just sub-components of a larger
plugin, that being a Product, which fully defines the process of how to create a Product
via GeoIPS.

In other words, you should implement your product in a fashion similar to what is done
in the :ref:`My-Cloud-Depth product definition<cloud-depth-product>`.
