.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _output_formats_functionality:

***************************
Output Formatters in GeoIPS
***************************

An output formatter is a class-based GeoIPS plugin designed to output a dataset
to a file. This encompasses many varied types of output, including geotiff,
netCDF, and imagery. Output formatters vary in complexity depending on the
output type.

Examples of output formatter plugins can be found in the list of GeoIPS built-in
`output formatters <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/classes/output_formatters>`_.

A tutorial for implementing a new output formatter can be found in the
:ref:`GeoIPS Documentation <create-output-formatter>`

Output formatters can be executed in two ways:

1. **Specification at the Command Line:** Output formatters are specified
as arguments at the command line. For example:

   .. code-block:: bash

      --output_formatter imagery_annotated

2. **Direct Invocation:** Call the output formatter from within a program:

   .. code-block:: python

      from geoips.interfaces import output_formatters
      output_fmt_name = "imagery_annotated"
      output_formatter = output_formatters.get_plugin(output_fmt_name)


Plugin arguments
================

The arguments accepted by a output formatter step (validated in
:ref:`Order-Based Processing workflows <order-based-processing>`) are defined by
the model below. These fields are generated directly from the code, so they always
reflect the current validation rules.

.. autopydantic_model:: geoips.pydantic_models.v1.output_formatters.OutputFormatterArgumentsModel
   :noindex:
