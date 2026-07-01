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

Specifying Output Checker Overrides
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A workflow's ``test`` section supports one more type of override that cannot be
specified via a command line flag. You can add ``output_checker`` overrides in the test
section of a workflow. These are used to check the output of one or more referenced
steps in a workflow.

Take for example the following workflow.

.. code-block:: yaml

  apiVersion: geoips/v1
  interface: workflows
  family: order_based
  name: test_product
  docstring: |
    11.2 µm Infrared.

    This product utilizes channel 14 (11.2 µm) and highlights areas of deep convection within a Tropical Cyclone.
  description: 11.2 µm Infrared.
  test:
    fnames: !ENV ${GEOIPS_TESTDATA_DIR}/test_data_abi/data/goes16_20200918_1950/*
    outputs:
      abi:Infrared:
        full_test_policy: on_token_mismatch # | always | never
        compare_path: !ENV ${GEOIPS_PACKAGES_DIR}/geoips/tests/outputs/abi.static.Infrared.imagery_clean/20200918.195020.goes-16.abi.Infrared.test_goes16_eqc_3km_day_20200918T1950Z.100p00.noaa.3p0.png
    steps:
      reader:
        area_def: null
      abi:Infrared:
        spec:
          steps:
            algorithm:
              output_units: Kelvin
    kinds:
      readers:
        satellite_zenith_angle_cutoff: 80
    globals:
      sector_list: global_cylindrical
      logging_level: info
  spec:
    steps:
      reader:
        kind: reader
        name: abi_netcdf
        arguments:
          chans: ['B14BT']
      abi:Infrared:
        kind: product
        name: [abi, Infrared]
        arguments: {}

You'll see that the workflow above has an ``outputs`` field in its test section. This is
how output checker overrides are implemented. Generically, the ``outputs`` override
field must take on the following format:

.. code-block:: yaml

  test:
    outputs:
      <step_id>: &output-step-definition
        # name: <output_checker_name>                 # optional, derived from compare path if not provided
        # full_test_policy: "on_token_mismatch" | "always" | "never"         # optional
        # compare_path: /path/to/comparison/file.ext  # optional, but usually should exist
        # threshold: float [0,1] # Only works for image output checker
      <step_idX>:
        spec:
          steps:
            <step_idY>:
              <nested_keys>: *output-step-definition

You can see in the code block above that nested output_checker overrides are supported.
Under the hood, when an output checker override is detected, a new step in your workflow
is generated at runtime directly after the step whose output we want to inspect.

So, in workflow example above, a new step would be inserted directly after the
``abi:Infrared`` step. The workflow that the Order Based Procflow would encounter at
runtime would equal the following:

.. code-block:: yaml

  apiVersion: geoips/v1
  interface: workflows
  family: order_based
  name: test_product
  docstring: |
    11.2 µm Infrared.

    This product utilizes channel 14 (11.2 µm) and highlights areas of deep convection within a Tropical Cyclone.
  description: 11.2 µm Infrared.
  spec:
    steps:
      reader:
        kind: reader
        name: abi_netcdf
        depends_on: []
        keep: False
        arguments:
          chans: ['B14BT']
          sector_list: global_cylindrical
          logging_level: info
          satellite_zenith_angle_cutoff: 80
      abi:Infrared:
        kind: workflow
        spec:
          outputs: ['colormapper']
          retention: keep_referenced
          keep: False,
          depends_on: ['reader']
          arguments: None
        steps:
          interpolator:
            kind: interpolator
            name: interp_nearest
            depends_on: []
            keep: False
            arguments:
              sector_list: global_cylindrical
              logging_level: info
          algorithm:
            kind: algorithm
            name: single_channel
            depends_on: ['interpolator']
            keep: False
            arguments:
              output_data_range: [-90.0, 30.0]
              input_units: Kelvin
              output_units: Kelvin
              min_outbounds: crop
              max_outbounds: crop
              norm: False
              inverse: False
              sector_list: global_cylindrical
              logging_level: info
          colormapper:
            kind: colormapper
            name: Infrared
            depends_on: ['algorithm']
            keep: False
            arguments:
              data_range: [-90.0, 30.0]
              sector_list: global_cylindrical
              logging_level: info
      output_checker1:
        policy: on_failure
        name: image
        kind: output_checker
        depends_on: ['abi:Infrared']
        arguments:
          compare_path: /home/evan/geoips/geoips_packages/geoips/tests/outputs/abi.static.Infrared.imagery_clean/20200918.195020.goes-16.abi.Infrared.test_goes16_eqc_3km_day_20200918T1950Z.100p00.noaa.3p0.png

You can see that the product step was expanded, all of the overrides were applied, and a
new ``output_checker`` step was added in the correct location. The plugin used in the
output checker step was derived from the compare path argument, but this can be
supplied explicitly if desired.

Other Arguments
---------------

The OBP accepts additional arguments which can be provided to any GeoIPS procflow. For
more information on those arguments and how to use them, please feel free to consult the
:ref:`CLI docs<command_line>`.