Yaml-based Plugins
==================

Yaml-based plugins configure the behavior of GeoIPS and how class-based
plugins will act upon your data. They include plugins that define ``Sectors``
to be interpolated to, ``FeatureAnnotators`` and ``GridlineAnnotators`` that
control how features and gridlines are plotted on output images,
infrastructure-as-code ``Workflows`` that combine other plugins into an
ordered series of steps, and more. They are specifically formatted yaml files
that must contain certain fields depending on their kind.

Yaml-based Plugin Kinds
-----------------------

The current available kinds of yaml-based plugins include:

- ``FeatureAnnotators``: Configure how features (e.g. coastlines, country
  borders, etc.) are plotted on output images.
- ``GridlineAnnotators``: Configure how gridlines and lat/lon labels are
  plotted on output images.
- ``Sectors``: Define geographical regions to be interpolated to.
- ``Workflows``: Define infrastructure-as-code workflows that combine other
  plugins into an ordered series of steps.

Deprecated Yaml-based Kinds
---------------------------

There are two deprecated yaml-based plugin kinds. These will still work
through translation scripts, but new plugins of these kinds should not be
created and existing plugins of these kinds should be converted to the new
kinds. Conversion scripts are provided to convert these to ``Workflow``
plugins. The deprecated kinds are:

- ``Products``: These were used to define products to be generated. They have
  been replaced by ``Workflows`` which are more flexible and can be used to
  define products as well as other kinds of workflows.
- ``ProductDefaults``: These were used to define default values for product
  generation. They have been replaced by ``Workflows`` can be used inside one
  another as sub-workflows.