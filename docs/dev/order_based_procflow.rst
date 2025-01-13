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

* **User-Defined Step Order:** allows users to specify the exact sequence
  of processing steps.
* **Flexible Step Repetition:** supports repeating specific steps, such as
  multiple algorithm plugins, as needed for a particular product.
* **Comprehensive Error Control:** uses Pydantic validation for thorough error
  checking and input validation.
* **Scalable Architecture:** accomodates additional steps and enables more
  complex product processing workflows.

The OBP is a sequence of user-defined plugin operations. The
top-level plugins required as steps in the OBP are readers, algorithms,
interpolators, and output formatters. These plugin operations, or steps, are
defined in a YAML format within a product definition file and validated using `Pydantic <https://docs.pydantic.dev/latest/>`.

The code block below shows the syntax of a sample step definition:

.. code-block:: yaml

    spec:
      steps:
        - step:     # Beginning of first step
            _type:  <type_name>        #auto-filled, takes the value of step / plugin type
            name:   <plugin_name>
            arguments: {}
        - step:     # Beginning of second step

Description of properties
*************************

Few of the important fields definition from the product definition file.

* ``step`` (required) : represents each stage (top-level plugin) in the
  computational sequence. It is equivalent to the plugin type.
* ``type`` (optional): private variable and for internal use only.
* ``name`` (required) : Specifies the specific plugin name for the step.
* ``arguments`` (required) : Accepts a list of arguments validated against the
  plugin's call signature. This field can also include other plugins (steps) if
  needed.

Example of a Step Definition
****************************
Below is an example YAML configuration for reader step:

.. code-block:: yaml

    steps:
    - reader:
        name: abi_netcdf
        arguments:
          area_def: None
          chans: None
          metadata_only: False
          self_register: False
          variables: ['B14BT']


Plugin Definition Requirements
******************************

These plugin definitions must:

* Conform to call signature for their plugin type.
* Accept data matching the standard GeoIPS data format (except for the reader
  step).
* Return data matching the standard GeoIPS data format (except for the output
  formatter step).

Each step can also take other valid plugins as arguments. For instance, the
Output Formatter step in the code-block below includes two additional plugins,
colormapper and filename_formatter, for enhanced customization.

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
            chans: None
            metadata_only: False
            self_register: False
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

The code block above demonstrates a valid product definition for an Order-Based
procflow.

