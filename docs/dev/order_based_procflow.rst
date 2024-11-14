.. .. dropdown:: Distribution Statement

..  | # # # This source code is protected under the license referenced at
..  | # # # https://github.com/NRLMMD-GEOIPS.

====================
Order-Based Procflow
====================

.. contents::

Overview:
=========

The GeoIPS' Order-Based Procflow (OBP) follows an ETCVO (Extract, Transform,
Compute, Visualize, Output) computational workflow. Current procflows
computational sequence is not well defined and exhibits black box nature.
The advantages of OBP over existing procflows are as follows:

* user-defined order of steps
* flexible number of step repetitions
* pydantic validation for better error control
* scalable architecture allowing more steps as needed

The OBP workflow consists of sequence of user-defined plugin operations which
are also referred as steps. These plugin operations or steps are defined in a
YAML format within a product definition file and are validated using `Pydantic <https://docs.pydantic.dev/latest/>`_.

The most common steps (not limited to) in OBP within GeoIPS are:

* Reader
* Algorithm
* Interpolator
* Output_formatter

The top-level plugins such as Reader, Algorithm, Interpolators, and Output
formatter are those that can act as steps in OBP. Each step can also take other
valid plugins as arguments. For instance, the Output Formatter step accepts two
additional plugins viz, colormapper, and filename_formatter, as arguments for
enhanced customization. Moving these nested plugins to the top-level plugin operations is near


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


