.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Interfaces
==========

GeoIPS plugins come in two forms: **class-based** plugins written in Python (readers,
algorithms, interpolators, colormappers, output formatters, and more) and **YAML-based**
plugins defined declaratively (products, sectors, annotators). The pages below describe
each interface. To learn how to author a class-based plugin, see
:ref:`writing-class-based-plugins`.

.. toctree::
    :maxdepth: 1
    :caption: Writing plugins

    writing-class-based-plugins

.. toctree::
    :maxdepth: 1
    :caption: Class-based (Python) interfaces

    class_based/readers
    class_based/algorithm
    class_based/interpolators
    class_based/colormapper
    class_based/coverage_checkers
    class_based/output_formats
    class_based/filename_formats
    class_based/title_formats
    class_based/output_checkers
    class_based/sector_adjusters
    class_based/sector_metadata_generators
    class_based/sector_spec_generators
    class_based/databases
    class_based/procflows
    class_based/validators

.. toctree::
    :maxdepth: 1
    :caption: YAML-based interfaces

    yaml_based/products
    yaml_based/product_defaults
    yaml_based/static_sectors
    yaml_based/dynamic_sectors
    yaml_based/feature_annotators
    yaml_based/gridline_annotators
