.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

====================
Order-Based Procflow
====================

.. contents::

Summary
=======

The Order-Based Procflow (OBP) follows an ETCVO (Extract, Transform, Compute,
Visualize, Output) computational workflow.

It enables a a user-defined sequence of plugin operations, known as "steps,"
for processing workflows. The sequence of plugin operations (steps) is defined
in a YAML product definition file and validated using `Pydantic <https://docs.pydantic.dev/latest/>`_.

The most common steps (not limited to) in OBP within GeoIPS are:

* Reader
* Algorithm
* Interpolator
* Output_formatter

The Output Formatter step accepts two additional plugins, colormapper,
and filename_formatter, as arguments for enhanced customization.

Syntax of a Step Definition in OBP:
-----------------------------------
Each step is defined in the following YAML format:

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

Example of a Step Definition:
-----------------------------
An example YAML configuration for reader step:

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


