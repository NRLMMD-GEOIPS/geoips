:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _feature-annotators:

Feature Annotators Interface
****************************
GeoIPS Feature Annotators describe the format of the features shown in your imagery.
Features in GeoIPS imagery include coastline, borders, rivers, states, and the
background color of the map-based portion of your image. Similar to
:ref:`Gridline Annotators<gridline-annotators>`, plugins of this interface can only
be used in conjunction with an output formatter that makes use of these annotators.
A commonly used output formatter which makes use of gridline and feature annotators is
the ``imagery_annotated`` plugin.

Every annotated image that can be created using GeoIPS by default employs the
feature_annotator plugin ``default``. As the name suggests, this is the default
configuration for features in annotated imagery. For more information on this plugin,
including where to find it, simply run ``geoips describe feature-annotator default``.

Feature Annotator Specification
===============================
A feature_annotator plugin is broken into 5 elements, all of them being optional.
The following sections will describe each element, and how each come together to format
your features in any annotated image that you create using GeoIPS.

Every feature_annotator plugin is composed of:

Feature Annotator Elements
--------------------------
Any element in [``coastline``, ``borders``, ``states``, ``rivers``] follow the same
argument format for constructing features in your image. These elements directly relate
to the ``cartopy`` package, which we use in our backend to create geospatially located
maps in our imagery. For each of the elements previously mentioned, you can specify
whether or not you want that feature present in your image. If enabled, then you can
specify ``edgecolor`` and ``linewidth``, which as these names suggest, specify the
color of the feature and how thick (in pixels), the feature will appear in your image.

These arguments construct a `cartopy Feature object
<https://scitools.org.uk/cartopy/docs/v0.14/matplotlib/feature_interface.html>`_,
which is a uniform interface for creating map features in your annotated imagery.

Any element mentioned so far can be specified in this format:

.. code-block:: yaml

    <feature_name_enabled>:
        enabled: true
        edgecolor: red # matplotlib named color or hexidecimal string
        linewidth: 2 # float / integer using pixel units
    # OR
    <feature_name_disabled>:
        enabled: false

Coastline Element
^^^^^^^^^^^^^^^^^
The ``coastline`` element describes how coastlines are formatted in your image. If
enabled, the set of arguments used to create that element construct a cartopy
``Feature`` object which is present in your image.

Borders Element
^^^^^^^^^^^^^^^
The ``borders`` element describes how political borders are formatted in your image. If
enabled, the set of arguments used to create that element construct a cartopy
``Feature`` object which is present in your image.

States Element
^^^^^^^^^^^^^^
The ``states`` element describes how political states are formatted in your image. If
enabled, the set of arguments used to create that element construct a cartopy
``Feature`` object which is present in your image.

Rivers Element
^^^^^^^^^^^^^^
The ``rivers`` element describes how river geography is formatted in your image. If
enabled, the set of arguments used to create that element construct a cartopy
``Feature`` object which is present in your image.

GeoIPS-specific Feature Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``background`` (string: optional):
    * This is an optional element and specifies the background color of the map/data
      portion of your annotated image. Can either be a matplotlib named color or a
      hexidecimal string which represents your color.

.. code-block:: python

    # --------------------------
    # |  Frame                 |
    # |  _____________________ |
    # |  |                   | |
    # |  |    Map / Data     | |
    # |  |                   | |
    # |  _____________________ |
    # |------------------------|

An Example Feature Annotator
============================
Shown below, is the default_oldlace feature annotator.

.. code-block:: yaml

    interface: feature_annotators
    name: default_oldlace
    family: cartopy
    docstring: |
      The default_oldlace feature_annotators plugin. All line types enabled. All colored
      red. 2px coastlines, 1px countries, 0.5px states borders, and 0px rivers. oldlace
      background color.
    spec:
      coastline:
        enabled: true
        edgecolor: red
        linewidth: 2
      borders:
        enabled: true
        edgecolor: red
        linewidth: 1
      states:
        enabled: true
        edgecolor: red
        linewidth: 0.5
      rivers:
        enabled: false
      background: oldlace
