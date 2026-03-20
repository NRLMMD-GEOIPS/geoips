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

- Data Structures
- Metadata Standards
- File Caching
- Plugin System
- Plugin Types & Kinds
- Plugin Interfaces
- Plugin Packages
- Plugin Registry
- Testing Infrastructure
- Documentation Standards
- Code Standards
- CI/CD

.. toctree::
    :maxdepth: 1

    data-structures
    test-infrastructure
    documentation
    cached-files