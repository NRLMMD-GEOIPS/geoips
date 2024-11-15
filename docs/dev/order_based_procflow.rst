.. .. dropdown:: Distribution Statement

..  | # # # This source code is protected under the license referenced at
..  | # # # https://github.com/NRLMMD-GEOIPS.

====================
Order-Based Procflow
====================

.. contents::

Overview:
=========

The GeoIPS Order-Based Procflow (OBP) implements a computational workflow based
on the ETCVO sequence: Extract, Transform, Compute, Visualize, and Output.
OBP offers the following key advantages over other procflows:

* **user-defined order of steps:** allows users to specify the exact sequence
  of processing steps.
* **flexible number of step repetitions:** supports repeating specific steps
  such as multiple algorithm plugins as needed for a specific product.
* **pydantic validation for better error control:** uses Pydantic validation
  for comprehensive error checking and input validation.
* **scalable architecture :** accomodates additional steps enabling more
  complex product processing workflows.

The OBP workflow consists of sequence of user-defined plugin operations. The
top-level plugins are those that can be used as steps in the OBP and at minimum
include readers, algorithms, Interpolators, and output fomatters. Each step can
also take other valid plugins as arguments. For instance, the Output Formatter
step accepts two additional plugins viz, colormapper, and filename_formatter,
as arguments for enhanced customization.

These plugin operations or steps are defined in a YAML format within a product
definition file and are validated using `Pydantic <https://docs.pydantic.dev/latest/>`_.

Syntax of a Step Definition in OBP:
-----------------------------------

.. code-block:: python

     step:                                         # synonym for plugin type
      [type]:  <type_name>                         # optional, auto-filled if omitted
      name: <plugin_name>
      arguments: {}


* step: Equivalent to the plugin type, representing each stage (plugin) in the
  computational sequence.
* type: Specifies the plugin type, which is optional as it can be inferred from
  the step.
* name: specifies the specific plugin name for the step.
* arguments: accepts a list of arguments for validation against the plugin's
  call signature. This field can also include other plugins (steps) if needed.

These plugins must:

* conform to call signature for its plugin type.
* accept data that matches the standard GeoIPS data format except reader step.
* return data that matches the standard GeoIPS data format except
  output_formatters step.

Example of a Step Definition: An example YAML configuration for reader step:

.. code-block:: python

    steps:
    - reader:
        name: abi_netcdf
        arguments:
          area_def: None
          chans: None
          metadata_only: False
          self_register: False
          variables: ['B14BT']


