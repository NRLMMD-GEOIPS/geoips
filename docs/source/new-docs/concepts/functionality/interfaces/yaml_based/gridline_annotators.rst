:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _gridline-annotators:

Gridline Annotators Interface
*****************************
GeoIPS Gridline Annotators describe the format of the grid lines shown in your imagery.
This includes the spacing of the grid lines, their units, the labels used for the grid
lines, the thickness of the lines, and optionally, the background color of the annotated
image in which your grid lines will format.

Every annotated image that can be created using GeoIPS by default employs the
gridline_annotator plugin ``default``. As the name suggests, this is the default grid
line configuration for annotated imagery. For more information on this plugin, including
where to find it, simply run ``geoips describe gridline-annotator default``.

Gridline Annotator Specification
================================
A gridline_annotator plugin is broken into 4 elements, one of them which is optional.
The following sections will describe each element, and how each come together to format
your gridlines in any annotated image that you create using GeoIPS.

Every gridline_annotator plugin is composed of:

Labels
------
The ``labels`` element describes how grid line labels are formatted in your image. The
arguments used to construct the labels element largely follow the keyword arguments used
to construct a `matplotlib.pyplot.text <https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.text.html>`_
object. There are also a  few distinct arguments which are used to support label
positioning, which are GeoIPS specific arguments.

GeoIPS-specific Label Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``top``, ``bottom``, ``left``, ``right`` (required):
    * Boolean value representing whether or not you want labels on the specified side of
      your image. I.e., if ``top: True`` was specified in the ``labels`` section of your
      gridline annotator plugin, then grid line labels would be included in the top
      portion of your image.

matplotlib.pyplot.text Keyword Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For a listing of GeoIPS supported matplotlib.pyplot.text label keyword arguments, see
``geoips.schema.gridline_annotators.cartopy:labels``. For documentation on how to use
each of those keyword arguments, see `here <https://matplotlib.org/stable/api/text_api.html#matplotlib.text.Text>`_.

Lines
-----
The ``lines`` element describes how grid lines are formatted in your image. This
includes the color of the line, the thickness of the line (in pixels), and the linestyle
of the line, which matches the ``linestyle`` attribute of a
`matplotlib.axes.Axes.grid object <https://matplotlib.org/stable/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D.set_linestyle>`_.

Line Arguments
^^^^^^^^^^^^^^
``color`` (required):
    * The color of the grid lines. Can either be a matplotlib named color or a
      hexidecimal string.
``linewidth`` (required):
    * The width of the grid lines in pixels. This is an integer value and not a float.
``linestyle`` (required):
    * The style of your grid lines. See `set_linestyle <https://matplotlib.org/stable/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D.set_linestyle>`_
      for more information.

Spacing
-------
The ``spacing`` element describes the set distance between grid lines in your image.
This is established using ``latitude`` and ``longitude`` arguments, which are both
required to construct a spacing element.

Spacing Arguments
^^^^^^^^^^^^^^^^^
``latitude``, ``longitude`` (required):
    * Either a string or number which represent the spacing in degrees between each
      gridline. If a string, then the string must be ``auto``, which means the spacing
      will automatically be determined based on the area-defition provided to GeoIPS.

Background
----------
This is an optional element and specifies the background color of the frame of your
annotated image. The frame of the image is the portion which contains the label,
colorbar, title, etc., and not the map portion of the image which contains your actual
data.

.. code-block:: python

    # --------------------------
    # |  Frame                 |
    # |  _____________________ |
    # |  |                   | |
    # |  |    Map / Data     | |
    # |  |                   | |
    # |  _____________________ |
    # |------------------------|

The ``background`` element is not like the other elements mentioned, and is simply just
a string. Specified as ``background: <color>``, where ``<color>`` is either a matplotlib
named color or a hexidecimal string.

An Example Gridline Annotator
=============================
Shown below, is the default_palegreen gridline annotator.

.. code-block:: yaml

    interface: gridline_annotators
    family: cartopy
    name: default_palegreen
    docstring: |
      The default_palegreen gridline_annotators plugin. Top and left gridline labels
      (offset 50 px), latitude and longitude lines colored black, auto spacing, 1px
      linewidth, and [4, 2] linestyle. palegreen background color.
    spec:
      labels:
        top: true
        bottom: false
        left: true
        right: false
        xpadding: 50
        ypadding: 50
        fontfamily: 'URW Bookman'
        fontstyle: oblique
        fontweight: demibold
        fontsize: 50
      lines:
        color: black
        linestyle: [4, 2]
        linewidth: 1
      spacing:
        latitude: auto
        longitude: auto
      background: palegreen
