.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _running-the-order-based-procflow:

Running the Order-Based Procflow
================================

.. contents::

Overview
--------

.. note::

  If you have not already read the :ref:`documentation<order-based-procflow>`about the
  Order-Based Procflow (OBP), please do so before continuing with the content in this
  document.

To run the OBP, we make use of the :ref:`GeoIPS CLI<command_line>`. You can execute the
contents of a registered or unregistered workflow plugin via the
``geoips run order_based <args>`` command.

For any instance of this command, there are two, ordered, REQUIRED arguments. Those
include:

1. workflow
2. filepaths

This tells the CLI what workflow to execute and what data to feed it. There are numerous
optional arguments that modify how the OBP will execute your workflow. New optional
arguments added specifically for this command include override flags. Overrides can be
implemented in two methods, string overrides, and dictionary-based overrides.

Below we'll demonstrate how to apply overrides of both formats.

String-based Overrides
----------------------

Specifying a dictionary at the commandline can be arduous and time consuming. Therefore
we've created string-based overrides which encapsulate the exact same override
functionality as dictionary-based overrides do. These are specified via lowercase
``-s``, ``-k``, and ``-g`` flags which represent ``[s]tep``, ``[k]ind``, and ``[g]lobal``
overrides.

A step override tells the CLI to override the value of an argument at a given workflow
step. A kind override tells the CLI to override the value of an argument for any
instance a step is of a certain interface ``kind``. Global overrides tell the CLI to
override or add an argument at every step. In any instance an argument passed to a
plugin is not supported, they will automatically be removed before that plugin is called.

When these overrides are added, one or more arguments for each flag can be supplied. You
do not need to respecify a flag before each individual override. Just group your
overrides by type and specify them in a row, then add another flag with overrides if
required.

Below we'll demonstrate how to use overrides via the GeoIPS CLI.

.. code-block:: bash

  geoips run order_based test_product $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/* \
    -s abi:Infrared.spec.steps.algorithm.output_units=Kelvin \
    -s reader.area_def=null \
    -k readers.satellite_zenith_angle_cutoff=80 \
    -g sector_list=global_cylindrical \
    -g logging_level=info

The format of string-based overrides goes as follows:

Step override: ``<step_id>.<optional_string1>.<optional_string2>...<argument>=<some_value>``
Kind override: ``<kind>.<argument_name>=<some_value>``
Global override: ``<global_variable_name>=<some_value>``

.. note::

  Every key of a step override should map to the ``expanded`` version of your workflow.
  For example, let's say the following were the expanded contents of your workflow:

  .. code-block:: yaml

    steps:
      reader:
        kind: reader
        name: abi_netcdf
        arguments:
          variables:
          - B14BT
      abi:Infrared:
        kind: workflow
        spec:
          steps:
            interpolator:
              kind: interpolator
              name: interp_nearest
              arguments: {}
            algorithm:
              kind: algorithm
              name: single_channel
              arguments:
                output_data_range:
                - -90.0
                - 30.0
                input_units: Kelvin
                output_units: celsius
                min_outbounds: crop
                max_outbounds: crop
                norm: false
                inverse: false
            colormapper:
              kind: colormapper
              name: Infrared
              arguments:
                data_range:
                - -90.0
                - 30.0

  Then, to override the ``output_units`` argument of the ``algorithm`` step, your
  override string would need to look like this:

  ``-s abi:Infrared.spec.steps.algorithm.output_units=Kelvin``

Dictionary-based Overrides
--------------------------

You can also override a workflow via dictionary-based overrides. This is how overrides
occur in a workflow's ``test`` section, and the same logic can be applied via the
command line. To specify dictionary-based overrides at the command line, we use
uppercase ``-S``, ``-K``, and ``-G`` flags. These are flags accept singular instances
of dictionaries that adhere to the format in which you can specify ``[S]tep``, ``[K]ind``,
and ``[G]lobal`` overrides in a workflow's test section.

Below we demonstrate how to specify dictionary-based overrides at the command line.

.. code-block:: bash

  geoips run order_based test_product $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/* \
      -S '{"reader": {"self_register": "LOW"}, "abi:Infrared": {"spec": {"steps": {"algorithm": {"output_units": "kelvin"}}}}}' \
      -K '{"readers": {"satellite_zenith_angle_cutoff": 80}}' \
      -G '{"sector_list": "global_cylindrical", "logging_level": "info"}'

As you can see, these are not nearly as easy to specify at the command line, but we
support them nonetheless, especially in the instance your scripts are being generated
for near-realtime processing, which is a very real possibility.

Other Arguments
---------------

The OBP accepts additional arguments which can be provided to any GeoIPS procflow. For
more information on those arguments and how to use them, please feel free to consult the
:ref:`CLI docs<command_line>`.