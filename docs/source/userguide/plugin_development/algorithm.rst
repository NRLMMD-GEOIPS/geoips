.. _add-an-algorithm:

**********************************
Extend GeoIPS with a new Algorithm
**********************************

To extend GeoIPS with a new ``algorithm`` plugin, first follow the :ref:`instructions for
setting up a plugin package<plugin-development-setup>`.

The following steps will teach you how to create a custom algorithm plugin. Copy the
existing algorithm plugin to a new file to modify
::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/modules/algorithms
    cp pmw_89test.py my_cloud_depth.py

Edit my_cloud_depth.py (see below)

Module plugins are required to have several top-level variables:
    * name
    * interface
    * family

It is additionally required to have a docstring. To convert this algorithm to
“my_cloud_depth” you'll need to update the ``docstring`` and update the ``name`` to
``my_cloud_depth``.

.. code-block:: python

    """Sample algorithm plugin, duplicate of "89pct".

    Duplicate of Passive Microwave 89 GHz Polarization Corrected Temperature.
    Data manipulation steps for the "89test" product, duplicate of "89pct".
    This algorithm expects Brightness Temperatures in units of degrees Kelvin
    """
    import logging
    from xarray import DataArray

    LOG = logging.getLogger(__name__)

    interface = "algorithms"  # The same for all algorithm plugins
    family = "xarray_to_xarray"
    # In English: this plugin takes an Xarray dataset containing all required variables,
    # and returns an Xarray dataset with a new variable holding the output from the algorithm
    name = "pmw_89test"

Update the code block above with the changes shown below.

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
pmw_89test.py plugin.

.. code-block:: python

    def call(
        xobj,  # Xarray dataset holding xarrays
        variables,  # list of required input variables for algorithm. Note: Python lists are ordered, so you can count on your list of variables being in the order in which you define them in your product plugin variables
        product_name,
        output_data_range,
        min_outbounds="crop",
        max_outbounds="mask",
        norm=False,
        inverse=False,
    ):
        """89pct product algorithm data manipulation steps."""

Update the code block above to the code block below. These changes will help us create
a cloud-depth algorithm.

.. code-block:: python

    def call(
        xobj,
        variables,
        product_name,
        output_data_range,
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

.. code-block:: python

    h89 = xobj[variables[0]]
    v89 = xobj[variables[1]]

    out = (1.7 * v89) - (0.7 * h89)

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

Update the code above to the code below. This is how cloud-depth will be calculated.

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

Now that we've created our custom algorithm, we need to add an entry point for it in
pyproject.toml so that GeoIPS can locate it during runtime. This must be done anytime
a new module-based plugin is created.

Module-based plugins must be registered to an entry-point namespace. This allows
GeoIPS to find your plugin, even though it is in a different package!
The namespaces are named for their interface (e.g. ``geoips.algorithms``,
``geoips.interpolators``, etc.).

Add your entrypoint:
::

    cd $MY_PKG_DIR
	# Edit pyproject.toml

.. code-block:: toml

    [project.entry-points."geoips.algorithms"]
    pmw_89test = "cool_plugins.plugins.modules.algorithms.pmw_89test"
    my_cloud_depth = "cool_plugins.plugins.modules.algorithms.my_cloud_depth"

Reinstall your package
::

    pip install -e $MY_PKG_DIR
    # This is required anytime pyproject.toml is edited!

Let's revisit our My-Cloud-Depth product definition to use the algorithm we just created
Note: If you haven't yet created this product, see the *Products* section.
::

    cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/yaml/products

Edit my_clavrx_products.yaml (see below)

