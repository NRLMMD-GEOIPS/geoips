# cspell:ignore ETCVO
.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _order-based-procflow:

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

* ``steps`` (required): A dictionary mapping from step ID (a unique
  identifier) to each plugin step definition.
* ``step_id`` (required within steps): The unique name for each step. It must
  be a valid Python identifier. The step_id serves as the dictionary key under
  steps and distinguishes each step within the workflow.
* ``kind`` (required): Specifies the type of plugin.
* ``name`` (required): The plugin's name corresponding to the specified
  ``kind``.
* ``arguments`` (required): Accepts a list of arguments validated against the
  plugin's call signature. This field can also include other nested-level
  plugins (steps) when required.

Syntax
------

The code block below demonstrates the syntax of a sample step definition:

.. code-block:: yaml

    spec:
      steps:
        step_id:     # unique step identifier for this step
          kind:  <kind_name>        # plugin kind such as reader
          name:  <plugin_name>      # specific plugin name
          arguments: {}
        step_idX:     # unique step identifier for second step


Example
-------

The following code block demonstrates a valid YAML configuration for a reader
step:

.. code-block:: yaml

    spec:
      global-arguments:
        presector: False
        product_db: False
        product_db_writer: None
        product_db_writer_kwargs: None
        product_name: None
        reader_defined_area_def: False
        sector_list: []
        window_start_time: None
        window_end_time: None
      steps:
        reader_1:
          kind: reader
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

    apiVersion: geoips/v1
    interface: workflows
    family: order_based
    name: abi_static_infrared_annotated_enhanced
    docstring: |
      This product utilizes channel 14 (11.2 µm) and highlights areas of deep convection within a Tropical Cyclone.
    description: 11.2 µm Infrared.
    test:
      fnames: !ENV ${GEOIPS_TESTDATA_DIR}/test_data_abi/data/goes16_20200918_1950/*
      outputs:
        output_formatter:
          full_test_policy: on_token_mismatch # always | never
          compare_path: !ENV ${GEOIPS_PACKAGES_DIR}/geoips/tests/outputs/abi.static.Infrared.imagery_clean
          output_checker_name: image
      globals:
        # sector_list: test_goes16_eqc_3km_night_20200918T1950Z
        logging_level: info
    spec:
      steps:
        reader:
          kind: reader
          name: abi_netcdf
          arguments:
            chans: ['B14BT']
        sector:
          kind: sector
          name: test_goes16_eqc_3km_day_20200918T1950Z
        abi_Infrared:
          kind: product
          name: [abi, Infrared]
          depends_on: [reader, sector]
        gridlines:
          kind: gridline_annotator
          name: default
        features:
          kind: feature_annotator
          name: default
        check_coverage:
          kind: coverage_checker
          name: masked_arrays
          depends_on: [abi_Infrared.algorithm, sector]
          arguments:
            variable_name: data
        create_filenames:
          kind: filename_formatter
          name: geoips_fname
          depends_on: [abi_Infrared.algorithm, sector, check_coverage]
          arguments:
            product_name: Infrared
        output_formatter:
          kind: output_formatter
          name: imagery_clean
          depends_on:
            - abi_Infrared.algorithm
            - abi_Infrared.colormapper
            - create_filenames
            - gridlines
            - features
            - sector
          arguments:
            product_name: Infrared
            product_name_title: G16 Infrared @ 11.2 um

The code block above demonstrates a valid example of a product definition for
an Order-Based Procflow.
