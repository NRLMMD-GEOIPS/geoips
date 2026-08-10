.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _title_formats_functionality:

Title Formatters in GeoIPS
**************************

A title formatter is a class-based GeoIPS plugin that generates a title that is
applied to image-based outputs. Title formatters generally contain useful
information (e.g. valid time) concerning the plotted data, but this plugin type
can be customized however the user desires.

For an example of a title formatter, see the
`static standard
<https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/classes/title_formatters/static_standard.py>`_
title formatter.

Title formatters can be applied in two ways:

1. **Direct Invocation:** Unlike most class-based GeoIPS plugins, title
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
`HY-2 windspeed
<https://github.com/NRLMMD-GEOIPS/geoips/blob/main/tests/scripts/hy2.tc.windspeed.imagery_annotated.sh>`_
test script.


Plugin arguments
================

The arguments accepted by a title formatter step (validated in
:ref:`Order-Based Processing workflows <order-based-processing>`) are defined by
the model below. These fields are generated directly from the code, so they always
reflect the current validation rules.

.. autopydantic_model:: geoips.pydantic_models.v1.title_formatters.TitleFormatterArgumentsModel
   :noindex:
