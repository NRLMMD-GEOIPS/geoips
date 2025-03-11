.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _output_formats_functionality:

************************
Output Formats in GeoIPS
************************

An output format is a module-based GeoIPS plugin designed to output a dataset
to a file. This encompasses many varied types of output, including geotiff,
netCDF, and imagery. Output formatters vary in complexity depending on the
output type.

Examples of output formatter plugins can be found in the list of GeoIPS built-in
`output formatters <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/modules/output_formatters>`_.

A tutorial for implementing a new output formatter can be found
`here <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/docs/source/tutorials/extending-with-plugins/output_formatter.rst>`_.

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
