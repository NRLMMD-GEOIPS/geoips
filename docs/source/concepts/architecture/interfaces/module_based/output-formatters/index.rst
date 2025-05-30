What Are Output Checkers?
=========================

Output checkers are testing tools that compare newly generated GeoIPS outputs against pre-generated reference outputs
known to be correct. They help ensure that any changes to GeoIPS code or configurations don't inadvertently alter the
expected outputs.

GeoIPS currently supports output checkers for four types of outputs:

1. Imagery
2. NetCDF Files
3. GeoTIFFs
4. Text-based outputs

Why Output Checkers Are Important
---------------------------------

GeoIPS processes and outputs various forms of geospatial satellite data. For each output type, we need to verify:

* **Imagery**: Pixel values, annotations, colormaps
* **NetCDF Files**: Data variables, metadata, date ranges, geographic coverage
* **GeoTIFFs**: Geospatial information, pixel values
* **Text-based outputs**: Correct formatting and values (e.g., for tropical cyclone data)

Output checkers provide an automated way to ensure these outputs remain consistent and accurate.

How Output Checkers Work
========================

Step 1: Understanding the Comparison Process
--------------------------------------------

Each output checker uses a different method appropriate for its file type:

* **Image Checker**: Compares images pixel-by-pixel using the PIL library and pixelmatch
* **NetCDF Checker**: Compares data variables and metadata, either exactly or within a specified tolerance
* **GeoTIFF Checker**: Uses a diff-based approach to compare files
* **Text Checker**: Performs line-by-line comparison of text files

Step 2: Setting Up Reference Outputs
------------------------------------

Before using output checkers, you need reference outputs:

1. Run your GeoIPS workflow with known-good configurations
2. Verify the outputs manually to ensure they're correct
3. Save these outputs in a designated location for future comparisons

Step 3: Using Output Checkers in a Workflow
-------------------------------------------

To use an output checker in your GeoIPS workflow:

1. Run your GeoIPS process workflow with the ``--compare_path`` parameter
2. Specify the path to your reference output files
3. GeoIPS will automatically select the appropriate output checker based on the file type

Example command:

.. code-block:: bash

    run_procflow $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/* \
                 --procflow single_source \
                 --reader_name abi_netcdf \
                 --product_name Infrared \
                 --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_annotated" \
                 --output_formatter imagery_annotated \
                 --filename_formatter geoips_fname \
                 --resampled_read \
                 --logging_level info \
                 --sector_list goes_east

Step 4: Interpreting Output Checker Results
-------------------------------------------

After running the workflow with a comparison path:

1. GeoIPS will generate new outputs
2. The appropriate output checker will compare these with reference outputs
3. Results will be reported in the console log
4. For image comparisons, a difference image may be generated highlighting mismatches in red

Practical Examples
==================

For practical examples, please refer to the documentation on `functionality of output checkers
<./../../../../functionality/interfaces/module_based/output-checkers/index.rst>`.

Creating Custom Output Checkers
-------------------------------

If you need to check specialized output types you can implement your own output checker.

For more information on implementing custom output checkers, please refer to this tutorial on
`Implementing Custom Output Checkers <./../../../../../tutorials/extending-with-plugins/output-formatter.rst>`_
