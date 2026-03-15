.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Plugins
=======

.. toctree:: :hidden:
    :glob:
    :maxdepth: 2

    class_based/*
    yaml_based/*

GeoIPS provides a number of different kinds of plugins. Each plugin kind is
intended to perform a specific type of function and plugins of the same kind
are grouped together under common `interfaces <interfaces>`_. There are two
primary types of interfaces: `class-based <class_based_interfaces>`_ and
`yaml-based <yaml_based_interfaces>`_. Class-based interfaces manage plugins
that are defined as Python classes and which perform actions directly on data.
Yaml-based interfaces manage plugins that are defined as yaml documents and
which modify the behavior of class-based plugins.

.. note::

   There is a third type of interface, `module-based
   <module_based_interfaces>`_, but this interface type has been deprecated.
   Plugins implemented as module-based plugins will still function, but are
   automatically converted to be class-based plugins at runtime. Module-based
   plugins will eventually raise a deprecation warning and should be converted
   to class-based.

Class-based interfaces
----------------------

`Algorithms <class_based/algorithms>`_: perform calculations to
produce new data variables.

`ColorMappers <class_based/colormappers>`_: define how to apply
a colormap to data when producing an image-based output. These may fully
define a colormap or apply an existing colormap (e.g. from matplotlib).

`CoverageCheckers <class_based/coverage_checkers>`_: determine how much
coverage a dataset has over a specified sector and whether that coverage is
sufficient.

`Databases <class_based/databases>`_: **not sure what to put here.**

`FilenameFormatters <class_based/filename_formatters>`_:
generate file names for output files, typically based on the metadata of the
dataset being output.

`Interpolators <class_based/interpolators>`_: perform
interpolation on data in any dimension. This is most commonly used to
interpolate in space, but may also be used to interpolate over other
dimensions like time or wavelength.

`OutputCheckers <class_based/output_checkers>`_: compare the output product
against a preexisting product to determine whether they match. This is
typically used for integration testing and not needed during normal processing.

`OutputFormatters <class_based/output_formatters>`_: write data to disk in a
particular format (e.g. PNG, GeoTIFF, NetCDF, HDF, etc.).

`Procflows <class_based/procflows>`_: define the a method of processing data
by calling other plugins in a specified order, whether specified by a config
file (e.g. a Workflow plugin) or by hardcoding processing steps in a script.

`Readers <class_based/readers>`_: read data from an input data file.

`SectorAdjusters <class_based/sector_adjusters>`_: adjust the ...

`SectorSpecGenerators <class_based/sector_spec_generators>`_: generate the
`spec` section of a dynamic `Sector`.

`SectorMetadataGenerators <class_based/sector_metadata_generators>`_: generate
the metadata section of a dynamic `Sector`.

`TitleFormatters <class_based/title_formatters>`_: produce a standard title
format for use in imagery output.


Yaml-based interfaces
---------------------
`FeatureAnnotators <yaml_based/feature_annotators>`_: define how geographic
features should be added to imagery, such as coastlines, borders, rivers,
states, and the background color of the map-based portion of the image.

`GridlineAnnotators <yaml_based/gridline_annotators>`_: define how grid lines
are added to imagery including their spacing, linestyle, color, etc.

`ProductDefaults <yaml_based/product_defaults>`_ (deprecated): define a default set of
options to be reused in multiple products.

`Products <yaml_based/products>`_ (deprecated): define how a specific product should be
produced by the single-source procflow.

`Sectors <yaml_based/sectors>`_: define a geographic area to which data may be
interpolated. These may be statically defined sectors or dynamic sectors that
use `SectorSpecGenerators` and `SectorMetadataGenerators`.

`Workflows <yaml_based/workflows>`_: define an ordered set of processing steps
to be performed on a dataset where each step is a plugin and arguments to be
passed to that plugin. This is used by the order-based procflow.
