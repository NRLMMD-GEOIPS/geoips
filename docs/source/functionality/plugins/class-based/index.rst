Class-based Plugins
===================

Class-based plugins provide most of GeoIPS' functionality. They include
``Readers`` for reading input data, ``Interpolators`` for interpolating data
(e.g. in space, time, and other dimeisions), ``Algorithms`` for applying
scientific algorithms to data, ``OutputFromatters`` for writing output data
products and imagery, and more.  They are defined as Python classes that must
inherit from an appropriate base class depending on their kind. For example, an
``Interpolator`` plugin must inherit from the ``InterpolatorPlugin`` base
class.

.. _class-based-kinds:

Class-based Plugin Kinds
------------------------

The current available kinds of class-based plugins include:

- ``Algorithms``: Apply scientific algorithms to data.
- ``ColorMappers``: Define color maps for use when plotting data.
- ``CoverageCheckers``: Check whether a dataset has sufficient coverage over a
  ``Sector`` to proceed with processing.
- ``FilenameFormatters``: Define how output file names should be formatted
  based on available metadata.
- ``Interpolators``: Interpolate data (e.g. in space, time, and other
  dimensions).
- ``OutputFormatters``: Write output data products and imagery.
- ``Readers``: Read input data.
- ``SectorMetadataGenerators``: Generate metadata for a dynamic sector based
  on input information (e.g. for following tropical cyclones).
- ``SectorSpecGenerators``: Generate a sector specification for a dynamic
  sector based on input information (e.g. for following tropical cyclones).
- ``TitleFormatters``: Define how output image titles should be formatted
  based on available metadata.

Deprecated Class-based Kinds
----------------------------

.. deprecated:: v2.0.0

    ``Procflow`` plugins are deprecated and will eventually be removed in
    favor of the Order-Based Procflow (OBP).

- ``Procflows``: These define the flow of data through GeoIPS. Older
  procflows, such as the Single-Source procflow and the Data-Fusion procflow
  are being phased out in favor of the Order-Based procflow (OBP). While the
  older procflows were black-boxes that programmatically defined the flow of
  data through GeoIPS using a series of conditionals, the OBP is transparent
  and relies upon ``Workflow`` plugins to define the flow of data. Eventually,
  the ``ProcflowInterface`` will be removed entirely and the OBP will become
  the core of GeoIPS.