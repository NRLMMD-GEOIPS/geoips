.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.


Order-Based Procflow
====================


.. contents::

Overview
--------

The Order-Based Procflow (OBP) implements an Extract, Transform,
Compute, Visualize, and Output (ETCVO) workflow.

OBP offers the following key advantages over other procflows:

* **User-Defined Step Order:** Allows users to specify the exact sequence
  of processing steps.
* **Flexible Step Repetition:** Supports repeating specific steps, such as
  running multiple algorithm plugins, as needed for a particular product.
* **Comprehensive Error Control:** Uses Pydantic validation for robust error
  and input checking.
* **Scalable Architecture:** Accommodates additional steps and enables more
  complex product processing workflows.

The OBP is a sequence of user-defined plugin operations. The top-level plugins
required as steps in the OBP are readers, algorithms, interpolators, and
output_formatters. We use the singular form of plugin type as the step name.
These plugin operations, or steps, are defined in YAML format
within a product definition file and validated using `Pydantic <https://docs.pydantic.dev/latest/>`_.

Important Fields
-----------------

A few of the important field definitions from the product definition file are:

* ``step`` (required): A top-level plugin in the computational sequence.
* ``type`` (private): A private variable intended for internal use.
* ``name`` (required): The name of the plugin for the ``step`` type.
* ``arguments`` (required): Accepts a list of arguments validated against the
  plugin's call signature. This field can also include other nested-level
  plugins (steps) when required.

Syntax
------

The code block below demonstrates the syntax of a sample step definition:

.. code-block:: yaml

    spec:
      steps:
        - step:     # beginning of first step
            # private, for internal use only
            type:  <type_name>        #takes the value of step / plugin type
            name:  <plugin_name>
            arguments: {}
        - step:     # beginning of second step


Example
-------

The following code block demonstrates a valid YAML configuration for a reader
step:

.. code-block:: yaml

    spec:
      steps:
      - reader:
          name: abi_netcdf
          arguments:
            area_def: None
            metadata_only: False
            self_register: [None]
            variables: ['B14BT']


Plugin Definition Requirements
------------------------------

These plugin definitions must:

* Conform to the call signature for their plugin type.
* **Accept data**: The input for each step must conform to the standard GeoIPS
  data :ref:`xarray_standards`, except for the ``reader`` step.
* **Return data**: The output data for each step must conform to the standard
  GeoIPS data :ref:`xarray_standards` except for the ``output_formatter`` step.

Each step can also accept other valid plugins as arguments. For instance, the
Output Formatter step in the code block below includes two additional plugins,
``colormapper`` and ``filename_formatter``, for enhanced customization.

.. code-block:: yaml

    interface: products
    family: order_based
    name: read_test
    docstring: Read test.
    package: geoips
    spec:
      steps:
        - reader:
            name: abi_netcdf
            arguments:
            area_def: None
            metadata_only: False
            self_register: [None]
            variables: ['B14BT']
        - algorithm:
            name: single_channel
            arguments:
            output_data_range: [-90.0, 30.0]
        - interpolator:
            name: interp_nearest
        - output_formatter:
            name: imagery_annotated
            arguments:
            colormapper:
                name: Infrared
                arguments:
                data_range: [-90.0, 30.0]
            filename_formatter:
                name: geoips_fname
                arguments:
                suffix: ".png"

The code block above demonstrates a valid example of a product definition for
an Order-Based Procflow.

