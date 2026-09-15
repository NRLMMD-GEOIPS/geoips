.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _architecture:

Architecture
============

The architecture section describes the design and structure of GeoIPS
in-depth. This section is intended for users who want to understand how GeoIPS
works, plugin developers who need a deeper understanding of how plugins
operate, and developers of the core GeoIPS package. The architecture section
details the plugin system, the various plugin kinds and how they behave,
interfaces and how they manage plugins, the plugin registry, unit and
integration test structure, documentation standards, code standards, and more.

.. toctree::
    :maxdepth: 1

    extend-with-plugins
    plugin-registry
    interfaces/module_based/output-checkers/index.rst
    structure-of-geoips/index
    data-structures
    geoips-specification
    cached-files
    test-infrastructure/index
    ci-infrastructure
    documentation/index
    command_line_interface
    custom-types/index
