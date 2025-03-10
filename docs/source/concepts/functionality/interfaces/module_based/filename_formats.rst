:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _filename_formats:

**************************
Filename Formats in GeoIPS
**************************

A filename format is a module-based GeoIPS plugin that defines how an output
file is named. Filaname formatters generally produce a unique filename based
on the metadata of the xarray dataset, but this plugin type is flexible. The
output of this plugin is a string, so it can be formatted however the user
desires.

For a simple example of a filename formatter, see the
`basic <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/modules/filename_formatters/basic_fname.py>`_
filename formatter.

A more advanced example is the
`standard GeoIPS <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/modules/filename_formatters/geoips_fname.py>`_
filename formatter.

Filename formatters can be applied in two ways:

1. **Specification at the Command Line:** Filename formatters are specified
as arguments at the command line. For example:

   .. code-block:: bash

      --filename_formatter geoips_fname

For an example of calling a filename formatter from a test script, see the
`ABI Infrared <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/tests/scripts/abi.static.Infrared.imagery_annotated.sh>`_
test script.

2. **Direct Invocation:** If you have your own output formatter, the filename
formatter can be called directly:

   .. code-block:: python

      from geoips.interfaces import filename_formatters
      fname_fmt = "geoips_fname"
      output_filename = filename_formatters.get_plugin(fname_fmt)

The output of the plugin can then be used when saving the output.
