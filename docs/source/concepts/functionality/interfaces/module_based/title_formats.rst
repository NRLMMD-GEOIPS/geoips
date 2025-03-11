.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _title_formats_functionality:

***********************
Title Formats in GeoIPS
***********************

A title format is a module-based GeoIPS plugin that generates a title that is
applied to image-based outputs. Title formatters generally contain useful
information (e.g. valid time) concerning the plotted data, but this plugin type
can be customized however the user desires.

For an example of a title formatter, see the
`static standard <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/modules/title_formatters/static_standard.py>`_
title formatter.

Title formatters can be applied in two ways:

1. **Direct Invocation:** Unlike most module-based GeoIPS plugins, title
formatters are generally accessed directly from within an output formatter:

   .. code-block:: python

      from geoips.interfaces import title_formatters
      title_fmt_name = "static_standard"
      title_string = title_formatters.get_plugin(title_fmt_name)
      ax.set_title(title_string, position=[xpos, ypos], fontsize=fontsize)

2. **Specification at the Command Line:** Title formatters can also be specified
as arguments at the command line. Since they are called from within an output
formatter, they are passed as an output formatter keyword argument formatted as
a JSON dictionary:

   .. code-block:: bash

      --output_formatter_kwargs '{"title_formatter": "static_standard"}'

For an example of calling a title formatter from a test script, see the
`HY-2 windspeed <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/tests/scripts/hy2.tc.windspeed.imagery_annotated.sh>`_
test script.
