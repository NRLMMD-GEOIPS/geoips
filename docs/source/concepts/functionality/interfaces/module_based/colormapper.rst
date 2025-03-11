.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _colormapper_functionality:

*******************
Colormaps in GeoIPS
*******************

A colormap is a module-based GeoIPS plugin that works in conjunction with an
image-based output formatter to dictate which colors are used to represent your
data. GeoIPS colormaps are structured as Python dictionaries that contain the
information needed for the output formatter to apply a colormap to the final
image. This information can include things like the matplotlib-compatible
colormap (existing or user-created), the data range covered by the colormap,
and information about the colorbar (if one is desired).

Most colormappers include a standard set of information that is useful for plotting:
  * cmap: The matplotlib colormap object that will be applied to the image.
  * norm: An object that scales your values so the colorbar covers the
    specified range.
  * colorbar: A boolean indicating whether to include a colorbar in the image.
  * cbar_ticks: Data points at which to place tick marks.
  * cbar_tick_labels: labels for the tick marks (a list of strings; should be
    the same length as cbar_ticks).
  * cbar_label: The label of the colorbar.
  * boundaries: A matplotlib parameter that is used to specify the boundaries
    within the colormap.
  * cbar_spacing: A matplotlib parameter that determines if each color has the
    same size in the colorbar, or if it is based on the proportion of data it covers.
  * cbar_full_width: A boolean indicating whether the colorbar should cover the
    full width of the image.

Other keyword arguments can be passed to the matplotlib colorbar in some output formatters
using the `colorbar_kwargs`, `set_ticks_kwargs`, and `set_label_kwargs` keys.

For an example of how a custom colormapper is formatted, see the
`Infrared colormapper <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/modules/colormappers/visir/Infrared.py>`_.

Using a Colormapper
===================

Colormappers can be applied in two ways:

1. **Inclusion in Product Specifications:** If using one of the existing output
formatters in GeoIPS, the colormapper can be included in the product default
specification, which can be executed via the command line or a test
script using a GeoIPS procflow.

For examples of including a colormapper in a product implementation, see the
`Extend GeoIPS with a Colormapper <https://github.com/NRLMMD-GEOIPS/geoips/blob/main/docs/source/tutorials/extending-with-plugins/colormapper/index.rst>`_
and
:ref:`product defaults <create-product-defaults>`
tutorials.

2. **Direct Invocation:** If you have your own output formatter, the colormapper
can be called directly:

   .. code-block:: python

      from geoips.interfaces import colormappers
      cmap_name = "Infrared"
      mpl_colors_info = colormappers.get_plugin(cmap_name)

The output of the plugin can then be applied to the plot of the image. For example:

   .. code-block:: python

      from geoips.image_utils.mpl_utils import create_colorbar

      main_ax.imshow(
          data,
          transform=mapobj,
          extent=mapobj.bounds,
          cmap=mpl_colors_info["cmap"],  # Use the colormap defined in the colormapper
          norm=mpl_colors_info["norm"],  # with the defined norm.
          **extra_args,
      )

      if mpl_colors_info["colorbar"] is True:
          # Create the colorbar defined in the colormapper.
          create_colorbar(fig, mpl_colors_info)

